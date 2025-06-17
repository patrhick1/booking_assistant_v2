"""
Performance tracking and metrics collection service for BookingAssistant.
Tracks email processing performance, quality metrics, and human feedback.
"""

import os
import hashlib
import time
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class SessionMetrics:
    """Container for session-level metrics"""
    session_id: str
    email_hash: str
    sender_email: str
    sender_name: str
    subject: str
    started_at: datetime
    
class MetricsCollector:
    """
    Lightweight metrics collection service that tracks BookingAssistant performance
    without interfering with the core LangGraph pipeline.
    """
    
    def __init__(self):
        self.db_pool = None
        self.current_session = None
        self.node_timers = {}
        self._init_database_connection()
    
    def _init_database_connection(self):
        """Initialize secure database connection using schema manager"""
        try:
            from src.schema import db_manager
            self.db_pool = db_manager.pool
            self.db_manager = db_manager
            print("✅ Metrics database connection established via secure schema manager")
        except Exception as e:
            print(f"❌ Failed to connect to metrics database: {e}")
            self.db_pool = None
            self.db_manager = None
    
    def _get_connection(self):
        """Get database connection from pool"""
        if not self.db_pool:
            return None
        try:
            return self.db_pool.getconn()
        except Exception as e:
            print(f"Error getting database connection: {e}")
            return None
    
    def _return_connection(self, conn):
        """Return connection to pool"""
        if self.db_pool and conn:
            self.db_pool.putconn(conn)
    
    def _execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Execute database query with connection pooling"""
        if not self.db_pool:
            return None
            
        conn = self._get_connection()
        if not conn:
            return None
            
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if fetch:
                    result = cursor.fetchall()
                else:
                    result = cursor.rowcount
                conn.commit()
                return result
        except Exception as e:
            print(f"Database query error: {e}")
            conn.rollback()
            return None
        finally:
            self._return_connection(conn)
    
    def _generate_email_hash(self, email_text: str, sender_email: str) -> str:
        """Generate unique hash for email deduplication"""
        content = f"{email_text}|{sender_email}".encode('utf-8')
        return hashlib.sha256(content).hexdigest()
    
    def start_session(self, email_details: Dict[str, Any]) -> Optional[str]:
        """Start a new email processing session and return session ID"""
        session_id = str(uuid.uuid4())
        email_hash = self._generate_email_hash(
            email_details.get('body', ''), 
            email_details.get('sender_email', '')
        )
        
        self.current_session = SessionMetrics(
            session_id=session_id,
            email_hash=email_hash,
            sender_email=email_details.get('sender_email', ''),
            sender_name=email_details.get('sender_name', ''),
            subject=email_details.get('subject', ''),
            started_at=datetime.now(timezone.utc)
        )
        
        # Insert session record
        query = """
            INSERT INTO email_sessions 
            (id, email_hash, sender_email, sender_name, subject, processing_started_at, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            session_id, email_hash, 
            self.current_session.sender_email,
            self.current_session.sender_name,
            self.current_session.subject,
            self.current_session.started_at,
            'processing'
        )
        
        self._execute_query(query, params)
        return session_id
    
    def get_current_session_id(self) -> str:
        """Get the current session ID for tracking"""
        if self.current_session:
            return self.current_session.session_id
        return "unknown-session"
    
    def start_node_timer(self, node_name: str):
        """Start timing a node execution"""
        if not self.current_session:
            return
        self.node_timers[node_name] = time.time()
    
    def end_node_timer(self, node_name: str, success: bool = True, error: str = None, 
                      input_data: Dict = None, output_data: Dict = None):
        """End timing a node execution and record metrics"""
        if not self.current_session or node_name not in self.node_timers:
            return
        
        duration_ms = int((time.time() - self.node_timers[node_name]) * 1000)
        del self.node_timers[node_name]
        
        # Calculate timestamps
        completed_at = datetime.now(timezone.utc)
        started_at = completed_at - timedelta(milliseconds=duration_ms)
        
        query = """
            INSERT INTO node_executions 
            (session_id, node_name, started_at, completed_at, duration_ms, success, error_message, input_data, output_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            self.current_session.session_id, node_name, started_at, completed_at, duration_ms, 
            success, error, 
            json.dumps(input_data) if input_data else None,
            json.dumps(output_data) if output_data else None
        )
        
        self._execute_query(query, params)
    
    def log_classification(self, predicted_label: str, confidence_score: float = None):
        """Log classification results"""
        if not self.current_session:
            return
        
        query = """
            INSERT INTO classification_results 
            (session_id, predicted_label, confidence_score)
            VALUES (%s, %s, %s)
        """
        params = (self.current_session.session_id, predicted_label, confidence_score)
        self._execute_query(query, params)
    
    def log_document_extraction(self, client_matched: bool, client_name: str = None,
                              documents_found: int = 0, extraction_success: bool = False,
                              extraction_duration_ms: int = None, error_reason: str = None):
        """Log document extraction performance"""
        if not self.current_session:
            return
        
        query = """
            INSERT INTO document_extractions 
            (session_id, client_matched, client_name, documents_found, 
             extraction_success, extraction_duration_ms, error_reason)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            self.current_session.session_id, client_matched, client_name,
            documents_found, extraction_success, extraction_duration_ms, error_reason
        )
        self._execute_query(query, params)
    
    def log_draft_generation(self, draft_length: int, final_draft_length: int = None,
                           context_used: bool = False, context_length: int = 0,
                           vector_threads_used: int = 0, placeholders_count: int = 0):
        """Log draft generation metrics"""
        if not self.current_session:
            return
        
        # Calculate template adherence score (simple heuristic)
        template_score = self._calculate_template_adherence_score(
            final_draft_length or draft_length, placeholders_count
        )
        
        query = """
            INSERT INTO draft_generations 
            (session_id, draft_length, final_draft_length, context_used, context_length,
             vector_threads_used, placeholders_count, template_adherence_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            self.current_session.session_id, draft_length, final_draft_length,
            context_used, context_length, vector_threads_used, 
            placeholders_count, template_score
        )
        self._execute_query(query, params)
    
    def _calculate_template_adherence_score(self, draft_length: int, placeholders_count: int) -> float:
        """Calculate a simple template adherence score"""
        # Heuristic: good drafts have reasonable length and appropriate placeholders
        length_score = min(1.0, max(0.0, (draft_length - 50) / 250))  # Optimal ~300 chars
        placeholder_score = min(1.0, placeholders_count / 3)  # Optimal ~3 placeholders
        return (length_score + placeholder_score) / 2
    
    def log_human_feedback(self, action: str, rating: int = None, edit_distance: int = 0,
                          feedback_notes: str = None, slack_message_id: str = None):
        """Log human feedback on draft quality"""
        if not self.current_session:
            return
        
        # Calculate edit type based on edit distance
        edit_type = None
        if edit_distance > 0:
            if edit_distance < 50:
                edit_type = 'minor'
            elif edit_distance < 200:
                edit_type = 'major'
            else:
                edit_type = 'complete_rewrite'
        
        # Calculate final quality score
        quality_score = self._calculate_quality_score(action, rating, edit_distance)
        
        query = """
            INSERT INTO quality_feedback 
            (session_id, human_action, human_rating, edit_distance, edit_type,
             approval_timestamp, feedback_notes, slack_message_id, final_quality_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            self.current_session.session_id, action, rating, edit_distance,
            edit_type, datetime.now(timezone.utc), feedback_notes, 
            slack_message_id, quality_score
        )
        self._execute_query(query, params)
    
    def _calculate_quality_score(self, action: str, rating: int = None, edit_distance: int = 0) -> float:
        """Calculate composite quality score"""
        score = 0
        
        # Human feedback (60% weight)
        if action == 'approved' and edit_distance == 0:
            score += 60
        elif action == 'approved' and edit_distance < 50:
            score += 45
        elif action == 'approved' and edit_distance < 200:
            score += 30
        elif action == 'rejected':
            score += 0
        
        # Human rating (40% weight)
        if rating:
            score += (rating / 5) * 40
        
        return min(score, 100)
    
    def complete_session(self, final_result: Dict[str, Any] = None, error: str = None):
        """Mark session as completed and record final metrics"""
        if not self.current_session:
            return
        
        total_duration = int((datetime.now(timezone.utc) - self.current_session.started_at).total_seconds() * 1000)
        status = 'completed' if not error else 'failed'
        
        # Update session record
        query = """
            UPDATE email_sessions 
            SET processing_completed_at = %s, total_duration_ms = %s, 
                status = %s, error_message = %s, classification = %s
            WHERE id = %s
        """
        params = (
            datetime.now(timezone.utc), total_duration, status, error,
            final_result.get('label') if final_result else None,
            self.current_session.session_id
        )
        self._execute_query(query, params)
        
        self.current_session = None
    
    def log_system_metric(self, metric_name: str, value: float, unit: str = None, tags: Dict = None):
        """Log system-level performance metrics"""
        query = """
            INSERT INTO system_metrics (metric_name, metric_value, metric_unit, tags)
            VALUES (%s, %s, %s, %s)
        """
        params = (metric_name, value, unit, json.dumps(tags) if tags else None)
        self._execute_query(query, params)
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive summary of a processing session"""
        query = """
            SELECT 
                es.*,
                cr.predicted_label,
                cr.confidence_score,
                de.client_matched,
                de.documents_found,
                dg.draft_length,
                dg.context_used,
                qf.human_action,
                qf.human_rating,
                qf.final_quality_score
            FROM email_sessions es
            LEFT JOIN classification_results cr ON es.id = cr.session_id
            LEFT JOIN document_extractions de ON es.id = de.session_id
            LEFT JOIN draft_generations dg ON es.id = dg.session_id
            LEFT JOIN quality_feedback qf ON es.id = qf.session_id
            WHERE es.id = %s
        """
        result = self._execute_query(query, (session_id,), fetch=True)
        return result[0] if result else None
    
    def start_email_session(self, email_details: Dict[str, Any]) -> Optional[str]:
        """Simplified session starter for backward compatibility"""
        return self.start_session(email_details)
    
    def end_email_session(self, status: str, error: str = None):
        """Simplified session completion for backward compatibility"""
        if self.current_session:
            result = {"status": status}
            self.complete_session(result, error)

# Global metrics collector instance
metrics = MetricsCollector()