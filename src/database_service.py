"""
Database Service for BookingAssistant
Handles all CRUD operations and database interactions with proper query management
"""

import os
import json
import uuid
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from src.metrics_service import metrics
from dotenv import load_dotenv

load_dotenv()

@dataclass
class SlackInteraction:
    """Data class for Slack interactions"""
    session_id: str
    interaction_type: str  # 'button_click', 'modal_submit', 'message_edit'
    action_value: str      # 'approve', 'reject', 'rate_5', etc.
    user_id: str
    user_name: str
    channel_id: str
    message_ts: str
    trigger_id: Optional[str] = None
    response_time_ms: Optional[int] = None
    payload: Optional[Dict] = None

@dataclass
class QualityFeedback:
    """Data class for quality feedback"""
    session_id: str
    human_action: str  # 'approved', 'edited', 'rejected'
    human_rating: Optional[int] = None  # 1-5
    slack_message_id: Optional[str] = None
    slack_channel_id: Optional[str] = None
    slack_user_id: Optional[str] = None
    slack_user_name: Optional[str] = None
    feedback_notes: Optional[str] = None
    interaction_metadata: Optional[Dict] = None

class DatabaseService:
    """Service for handling all database operations"""
    
    def __init__(self):
        self.db_pool = metrics.db_pool
        if not self.db_pool:
            print("⚠️  Warning: No database connection available")
    
    # =====================================================
    # SLACK INTERACTION METHODS
    # =====================================================
    
    def record_slack_interaction(self, interaction: SlackInteraction) -> bool:
        """Record a Slack interaction in the database"""
        if not self.db_pool:
            return False
        
        conn = None
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO slack_interactions (
                        session_id, interaction_type, action_value, user_id, user_name,
                        channel_id, message_ts, trigger_id, response_time_ms, payload
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    interaction.session_id,
                    interaction.interaction_type,
                    interaction.action_value,
                    interaction.user_id,
                    interaction.user_name,
                    interaction.channel_id,
                    interaction.message_ts,
                    interaction.trigger_id,
                    interaction.response_time_ms,
                    json.dumps(interaction.payload) if interaction.payload else None
                ))
                conn.commit()
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ Error recording Slack interaction: {e}")
            return False
        finally:
            if conn:
                self.db_pool.putconn(conn)
    
    def record_quality_feedback(self, feedback: QualityFeedback) -> bool:
        """Record quality feedback from Slack interaction"""
        if not self.db_pool:
            return False
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO quality_feedback (
                        session_id, human_action, human_rating, slack_message_id,
                        slack_channel_id, slack_user_id, slack_user_name,
                        approval_timestamp, feedback_notes, interaction_metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s)
                """, (
                    feedback.session_id,
                    feedback.human_action,
                    feedback.human_rating,
                    feedback.slack_message_id,
                    feedback.slack_channel_id,
                    feedback.slack_user_id,
                    feedback.slack_user_name,
                    feedback.feedback_notes,
                    json.dumps(feedback.interaction_metadata) if feedback.interaction_metadata else None
                ))
                conn.commit()
            self.db_pool.putconn(conn)
            return True
            
        except Exception as e:
            print(f"❌ Error recording quality feedback: {e}")
            return False
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data for Slack interaction"""
        if not self.db_pool:
            return None
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        es.id, es.sender_email, es.sender_name, es.subject, es.classification,
                        dg.draft_content, dg.final_draft_content,
                        ew.workflow_state, ew.current_step
                    FROM email_sessions es
                    LEFT JOIN draft_generations dg ON es.id = dg.session_id
                    LEFT JOIN email_workflows ew ON es.id = ew.session_id
                    WHERE es.id = %s
                """, (session_id,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'id': str(result['id']),
                        'sender_email': result['sender_email'],
                        'sender_name': result['sender_name'],
                        'subject': result['subject'],
                        'classification': result['classification'],
                        'draft_content': result['draft_content'],
                        'final_draft_content': result['final_draft_content'],
                        'workflow_state': result['workflow_state'],
                        'current_step': result['current_step']
                    }
            self.db_pool.putconn(conn)
            return None
            
        except Exception as e:
            print(f"❌ Error getting session data: {e}")
            return None
    
    def update_workflow_state(self, session_id: str, new_state: str, 
                            current_step: str, next_actions: Dict = None) -> bool:
        """Update workflow state after Slack interaction"""
        if not self.db_pool:
            return False
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE email_workflows 
                    SET 
                        workflow_state = %s,
                        current_step = %s,
                        next_actions = %s,
                        updated_at = NOW()
                    WHERE session_id = %s
                """, (
                    new_state,
                    current_step,
                    json.dumps(next_actions) if next_actions else None,
                    session_id
                ))
                
                # Also update email session status
                cursor.execute("""
                    UPDATE email_sessions 
                    SET 
                        status = CASE 
                            WHEN %s = 'approved' THEN 'approved'
                            WHEN %s = 'rejected' THEN 'rejected'
                            WHEN %s = 'edited' THEN 'edited'
                            ELSE status
                        END,
                        updated_at = NOW()
                    WHERE id = %s
                """, (new_state, new_state, new_state, session_id))
                
                conn.commit()
            self.db_pool.putconn(conn)
            return True
            
        except Exception as e:
            print(f"❌ Error updating workflow state: {e}")
            return False
    
    def update_draft_content(self, session_id: str, new_content: str) -> bool:
        """Update draft content when edited via Slack"""
        if not self.db_pool:
            return False
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE draft_generations 
                    SET 
                        final_draft_content = %s,
                        final_draft_length = LENGTH(%s),
                        updated_at = NOW()
                    WHERE session_id = %s
                """, (new_content, new_content, session_id))
                conn.commit()
            self.db_pool.putconn(conn)
            return True
            
        except Exception as e:
            print(f"❌ Error updating draft content: {e}")
            return False
    
    def mark_gmail_draft_created(self, session_id: str) -> bool:
        """Mark Gmail draft as created"""
        if not self.db_pool:
            return False
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE quality_feedback 
                    SET 
                        gmail_draft_created = TRUE,
                        updated_at = NOW()
                    WHERE session_id = %s
                """, (session_id,))
                conn.commit()
            self.db_pool.putconn(conn)
            return True
            
        except Exception as e:
            print(f"❌ Error marking Gmail draft as created: {e}")
            return False
    
    def mark_gmail_draft_sent(self, session_id: str) -> bool:
        """Mark Gmail draft as sent"""
        if not self.db_pool:
            return False
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE quality_feedback 
                    SET 
                        gmail_draft_sent = TRUE,
                        updated_at = NOW()
                    WHERE session_id = %s
                """, (session_id,))
                conn.commit()
            self.db_pool.putconn(conn)
            return True
            
        except Exception as e:
            print(f"❌ Error marking Gmail draft as sent: {e}")
            return False
    
    # =====================================================
    # ANALYTICS AND REPORTING METHODS
    # =====================================================
    
    def get_slack_interaction_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get Slack interaction statistics"""
        if not self.db_pool:
            return []
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        interaction_type,
                        action_value,
                        COUNT(*) as interaction_count,
                        COUNT(DISTINCT user_id) as unique_users,
                        AVG(response_time_ms) as avg_response_time
                    FROM slack_interactions 
                    WHERE created_at >= NOW() - INTERVAL '%s days'
                    GROUP BY interaction_type, action_value
                    ORDER BY interaction_count DESC
                """, (days,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'interaction_type': row['interaction_type'],
                        'action_value': row['action_value'],
                        'interaction_count': row['interaction_count'],
                        'unique_users': row['unique_users'],
                        'avg_response_time': float(row['avg_response_time']) if row['avg_response_time'] else 0
                    })
                
            self.db_pool.putconn(conn)
            return results
            
        except Exception as e:
            print(f"❌ Error getting Slack interaction stats: {e}")
            return []
    
    def get_approval_rates_by_classification(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get approval rates by email classification"""
        if not self.db_pool:
            return []
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        es.classification,
                        COUNT(*) as total_sessions,
                        COUNT(CASE WHEN qf.human_action = 'approved' THEN 1 END) as approved,
                        COUNT(CASE WHEN qf.human_action = 'rejected' THEN 1 END) as rejected,
                        COUNT(CASE WHEN qf.human_action = 'edited' THEN 1 END) as edited,
                        ROUND(
                            COUNT(CASE WHEN qf.human_action = 'approved' THEN 1 END) * 100.0 / COUNT(*), 
                            2
                        ) as approval_rate
                    FROM email_sessions es
                    LEFT JOIN quality_feedback qf ON es.id = qf.session_id
                    WHERE es.processing_completed_at >= NOW() - INTERVAL '%s days'
                    GROUP BY es.classification
                    ORDER BY approval_rate DESC
                """, (days,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'classification': row['classification'],
                        'total_sessions': row['total_sessions'],
                        'approved': row['approved'],
                        'rejected': row['rejected'],
                        'edited': row['edited'],
                        'approval_rate': float(row['approval_rate']) if row['approval_rate'] else 0
                    })
                
            self.db_pool.putconn(conn)
            return results
            
        except Exception as e:
            print(f"❌ Error getting approval rates: {e}")
            return []
    
    def get_pending_sessions(self) -> List[Dict[str, Any]]:
        """Get sessions pending Slack feedback"""
        if not self.db_pool:
            return []
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        es.id,
                        es.sender_email,
                        es.subject,
                        es.processing_completed_at,
                        ew.workflow_state,
                        ew.current_step
                    FROM email_sessions es
                    JOIN email_workflows ew ON es.id = ew.session_id
                    LEFT JOIN quality_feedback qf ON es.id = qf.session_id
                    WHERE ew.workflow_state = 'pending_review'
                    AND qf.id IS NULL
                    ORDER BY es.processing_completed_at ASC
                """)
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'id': str(row['id']),
                        'sender_email': row['sender_email'],
                        'subject': row['subject'],
                        'processing_completed_at': row['processing_completed_at'].isoformat() if row['processing_completed_at'] else None,
                        'workflow_state': row['workflow_state'],
                        'current_step': row['current_step']
                    })
                
            self.db_pool.putconn(conn)
            return results
            
        except Exception as e:
            print(f"❌ Error getting pending sessions: {e}")
            return []
    
    def get_quality_ratings_distribution(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get quality ratings distribution"""
        if not self.db_pool:
            return []
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        human_rating,
                        COUNT(*) as rating_count,
                        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
                    FROM quality_feedback 
                    WHERE human_rating IS NOT NULL
                    AND created_at >= NOW() - INTERVAL '%s days'
                    GROUP BY human_rating
                    ORDER BY human_rating
                """, (days,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'rating': row['human_rating'],
                        'count': row['rating_count'],
                        'percentage': float(row['percentage'])
                    })
                
            self.db_pool.putconn(conn)
            return results
            
        except Exception as e:
            print(f"❌ Error getting quality ratings distribution: {e}")
            return []
    
    # =====================================================
    # WORKFLOW MANAGEMENT METHODS
    # =====================================================
    
    def get_workflow_states_summary(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get summary of workflow states"""
        if not self.db_pool:
            return []
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        ew.workflow_state,
                        COUNT(*) as session_count,
                        AVG(EXTRACT(EPOCH FROM (NOW() - es.processing_completed_at)) / 3600) as avg_hours_in_state
                    FROM email_workflows ew
                    JOIN email_sessions es ON ew.session_id = es.id
                    WHERE es.processing_completed_at >= NOW() - INTERVAL '%s days'
                    GROUP BY ew.workflow_state
                    ORDER BY session_count DESC
                """, (days,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'workflow_state': row['workflow_state'],
                        'session_count': row['session_count'],
                        'avg_hours_in_state': float(row['avg_hours_in_state']) if row['avg_hours_in_state'] else 0
                    })
                
            self.db_pool.putconn(conn)
            return results
            
        except Exception as e:
            print(f"❌ Error getting workflow states summary: {e}")
            return []
    
    def get_overdue_sessions(self, hours_threshold: int = 24) -> List[Dict[str, Any]]:
        """Get sessions that are overdue for review"""
        if not self.db_pool:
            return []
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        es.id,
                        es.sender_email,
                        es.subject,
                        es.processing_completed_at,
                        EXTRACT(EPOCH FROM (NOW() - es.processing_completed_at)) / 3600 as hours_pending
                    FROM email_sessions es
                    JOIN email_workflows ew ON es.id = ew.session_id
                    WHERE ew.workflow_state = 'pending_review'
                    AND es.processing_completed_at < NOW() - INTERVAL '%s hours'
                    ORDER BY es.processing_completed_at ASC
                """, (hours_threshold,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'id': str(row['id']),
                        'sender_email': row['sender_email'],
                        'subject': row['subject'],
                        'processing_completed_at': row['processing_completed_at'].isoformat() if row['processing_completed_at'] else None,
                        'hours_pending': float(row['hours_pending']) if row['hours_pending'] else 0
                    })
                
            self.db_pool.putconn(conn)
            return results
            
        except Exception as e:
            print(f"❌ Error getting overdue sessions: {e}")
            return []

# Global database service instance
database_service = DatabaseService()