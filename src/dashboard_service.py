"""
Dashboard service for BookingAssistant performance monitoring.
Provides APIs for real-time metrics, analytics, and quality insights.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import json
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv

load_dotenv()

class DashboardService:
    """Service for generating dashboard data and analytics"""
    
    def __init__(self):
        self.db_pool = None
        self._init_database_connection()
    
    def _init_database_connection(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.db_pool = SimpleConnectionPool(
                1, 20,  # min, max connections
                host=os.getenv('PGHOST', 'localhost'),
                port=os.getenv('PGPORT', 5432),
                database=os.getenv('PGDATABASE', 'booking_assistant'),
                user=os.getenv('PGUSER', 'postgres'),
                password=os.getenv('PGPASSWORD'),
                cursor_factory=RealDictCursor
            )
            print("Dashboard database connection established")
        except Exception as e:
            print(f"Failed to connect to dashboard database: {e}")
            self.db_pool = None
    
    def _execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute database query and return results"""
        if not self.db_pool:
            return []
            
        conn = None
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            print(f"Dashboard query error: {e}")
            return []
        finally:
            if conn:
                self.db_pool.putconn(conn)
    
    def get_overview_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get high-level overview statistics"""
        since_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Total sessions
        total_sessions = self._execute_query("""
            SELECT COUNT(*) as count FROM email_sessions 
            WHERE processing_started_at > %s
        """, (since_date,))
        
        # Success rate
        success_rate = self._execute_query("""
            SELECT 
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) as total
            FROM email_sessions 
            WHERE processing_started_at > %s
        """, (since_date,))
        
        # Average processing time
        avg_time = self._execute_query("""
            SELECT AVG(total_duration_ms) as avg_ms
            FROM email_sessions 
            WHERE status = 'completed' AND processing_started_at > %s
        """, (since_date,))
        
        # Classification distribution
        classifications = self._execute_query("""
            SELECT classification, COUNT(*) as count
            FROM email_sessions 
            WHERE processing_started_at > %s AND classification IS NOT NULL
            GROUP BY classification
        """, (since_date,))
        
        return {
            "total_sessions": total_sessions[0]['count'] if total_sessions else 0,
            "success_rate": round((success_rate[0]['completed'] / max(success_rate[0]['total'], 1)) * 100, 1) if success_rate else 0,
            "avg_processing_time": round((avg_time[0]['avg_ms'] or 0) / 1000, 2) if avg_time else 0,
            "classifications": {row['classification']: row['count'] for row in classifications},
            "time_period": f"Last {days} days"
        }
    
    def get_processing_timeline(self, hours: int = 24) -> Dict[str, Any]:
        """Get processing timeline for recent sessions"""
        since_date = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        sessions = self._execute_query("""
            SELECT 
                processing_started_at,
                total_duration_ms,
                status,
                classification,
                sender_email
            FROM email_sessions 
            WHERE processing_started_at > %s
            ORDER BY processing_started_at DESC
        """, (since_date,))
        
        if not sessions:
            return {"timeline": [], "summary": {}}
        
        df = pd.DataFrame(sessions)
        df['processing_started_at'] = pd.to_datetime(df['processing_started_at'])
        
        # Create timeline chart
        fig = px.scatter(
            df, 
            x='processing_started_at', 
            y='total_duration_ms',
            color='status',
            hover_data=['classification', 'sender_email'],
            title=f"Email Processing Timeline (Last {hours} hours)",
            labels={'total_duration_ms': 'Processing Time (ms)', 'processing_started_at': 'Time'}
        )
        
        return {
            "timeline": json.dumps(fig, cls=PlotlyJSONEncoder),
            "summary": {
                "total_processed": len(df),
                "avg_time": round(df['total_duration_ms'].mean() / 1000, 2) if len(df) > 0 else 0,
                "success_count": len(df[df['status'] == 'completed'])
            }
        }
    
    def get_classification_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get classification accuracy and distribution analytics"""
        since_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Classification distribution
        distribution = self._execute_query("""
            SELECT 
                cr.predicted_label,
                COUNT(*) as count,
                AVG(cr.confidence_score) as avg_confidence
            FROM classification_results cr
            JOIN email_sessions es ON cr.session_id = es.id
            WHERE es.processing_started_at > %s
            GROUP BY cr.predicted_label
            ORDER BY count DESC
        """, (since_date,))
        
        # Classification trends over time
        trends = self._execute_query("""
            SELECT 
                DATE(es.processing_started_at) as date,
                cr.predicted_label,
                COUNT(*) as count
            FROM classification_results cr
            JOIN email_sessions es ON cr.session_id = es.id
            WHERE es.processing_started_at > %s
            GROUP BY DATE(es.processing_started_at), cr.predicted_label
            ORDER BY date DESC
        """, (since_date,))
        
        if distribution:
            # Create pie chart for distribution
            labels = [row['predicted_label'] for row in distribution]
            values = [row['count'] for row in distribution]
            
            fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.3)])
            fig_pie.update_layout(title="Classification Distribution")
            
            pie_chart = json.dumps(fig_pie, cls=PlotlyJSONEncoder)
        else:
            pie_chart = None
        
        if trends:
            # Create trends chart
            df_trends = pd.DataFrame(trends)
            fig_trends = px.line(
                df_trends, 
                x='date', 
                y='count', 
                color='predicted_label',
                title="Classification Trends Over Time"
            )
            trends_chart = json.dumps(fig_trends, cls=PlotlyJSONEncoder)
        else:
            trends_chart = None
        
        return {
            "distribution": distribution,
            "pie_chart": pie_chart,
            "trends_chart": trends_chart,
            "total_classifications": sum(row['count'] for row in distribution) if distribution else 0
        }
    
    def get_document_extraction_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get document extraction performance statistics"""
        since_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Overall extraction stats
        stats = self._execute_query("""
            SELECT 
                COUNT(*) as total_attempts,
                COUNT(*) FILTER (WHERE client_matched = true) as client_matches,
                COUNT(*) FILTER (WHERE extraction_success = true) as successful_extractions,
                AVG(documents_found) as avg_docs_found
            FROM document_extractions de
            JOIN email_sessions es ON de.session_id = es.id
            WHERE es.processing_started_at > %s
        """, (since_date,))
        
        # Client matching trends
        client_trends = self._execute_query("""
            SELECT 
                DATE(es.processing_started_at) as date,
                COUNT(*) as total_attempts,
                COUNT(*) FILTER (WHERE de.client_matched = true) as matches
            FROM document_extractions de
            JOIN email_sessions es ON de.session_id = es.id
            WHERE es.processing_started_at > %s
            GROUP BY DATE(es.processing_started_at)
            ORDER BY date DESC
        """, (since_date,))
        
        # Top clients matched
        top_clients = self._execute_query("""
            SELECT 
                client_name,
                COUNT(*) as match_count
            FROM document_extractions
            WHERE client_matched = true AND client_name IS NOT NULL
            GROUP BY client_name
            ORDER BY match_count DESC
            LIMIT 10
        """)
        
        return {
            "stats": stats[0] if stats else {},
            "client_trends": client_trends,
            "top_clients": top_clients,
            "success_rate": round(
                (stats[0]['successful_extractions'] / max(stats[0]['total_attempts'], 1)) * 100, 1
            ) if stats else 0
        }
    
    def get_draft_quality_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get draft generation quality metrics"""
        since_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Quality stats
        quality_stats = self._execute_query("""
            SELECT 
                COUNT(*) as total_drafts,
                AVG(draft_length) as avg_length,
                AVG(template_adherence_score) as avg_template_score,
                COUNT(*) FILTER (WHERE context_used = true) as context_usage_count,
                AVG(context_length) FILTER (WHERE context_used = true) as avg_context_length
            FROM draft_generations dg
            JOIN email_sessions es ON dg.session_id = es.id
            WHERE es.processing_started_at > %s
        """, (since_date,))
        
        # Quality over time
        quality_trends = self._execute_query("""
            SELECT 
                DATE(es.processing_started_at) as date,
                AVG(dg.template_adherence_score) as avg_quality,
                COUNT(*) as draft_count
            FROM draft_generations dg
            JOIN email_sessions es ON dg.session_id = es.id
            WHERE es.processing_started_at > %s
            GROUP BY DATE(es.processing_started_at)
            ORDER BY date DESC
        """, (since_date,))
        
        # Draft length distribution
        length_distribution = self._execute_query("""
            SELECT 
                CASE 
                    WHEN draft_length < 100 THEN 'Very Short'
                    WHEN draft_length < 250 THEN 'Short'
                    WHEN draft_length < 500 THEN 'Medium'
                    WHEN draft_length < 1000 THEN 'Long'
                    ELSE 'Very Long'
                END as length_category,
                COUNT(*) as count
            FROM draft_generations dg
            JOIN email_sessions es ON dg.session_id = es.id
            WHERE es.processing_started_at > %s
            GROUP BY length_category
        """, (since_date,))
        
        return {
            "stats": quality_stats[0] if quality_stats else {},
            "quality_trends": quality_trends,
            "length_distribution": length_distribution,
            "context_usage_rate": round(
                (quality_stats[0]['context_usage_count'] / max(quality_stats[0]['total_drafts'], 1)) * 100, 1
            ) if quality_stats else 0
        }
    
    def get_node_performance(self, days: int = 7) -> Dict[str, Any]:
        """Get individual node performance metrics"""
        since_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        node_stats = self._execute_query("""
            SELECT 
                ne.node_name,
                COUNT(*) as executions,
                AVG(ne.duration_ms) as avg_duration,
                COUNT(*) FILTER (WHERE ne.success = true) as successful,
                COUNT(*) FILTER (WHERE ne.success = false) as failed
            FROM node_executions ne
            JOIN email_sessions es ON ne.session_id = es.id
            WHERE es.processing_started_at > %s
            GROUP BY ne.node_name
            ORDER BY avg_duration DESC
        """, (since_date,))
        
        # Node performance over time
        node_trends = self._execute_query("""
            SELECT 
                DATE(es.processing_started_at) as date,
                ne.node_name,
                AVG(ne.duration_ms) as avg_duration
            FROM node_executions ne
            JOIN email_sessions es ON ne.session_id = es.id
            WHERE es.processing_started_at > %s
            GROUP BY DATE(es.processing_started_at), ne.node_name
            ORDER BY date DESC
        """, (since_date,))
        
        return {
            "node_stats": node_stats,
            "node_trends": node_trends
        }
    
    def get_recent_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent email processing sessions with details"""
        sessions = self._execute_query("""
            SELECT 
                es.id,
                es.sender_email,
                es.sender_name,
                es.subject,
                es.classification,
                es.processing_started_at,
                es.total_duration_ms,
                es.status,
                cr.confidence_score,
                de.client_matched,
                de.client_name,
                dg.template_adherence_score,
                dg.context_used
            FROM email_sessions es
            LEFT JOIN classification_results cr ON es.id = cr.session_id
            LEFT JOIN document_extractions de ON es.id = de.session_id
            LEFT JOIN draft_generations dg ON es.id = dg.session_id
            ORDER BY es.processing_started_at DESC
            LIMIT %s
        """, (limit,))
        
        return sessions
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health indicators"""
        # Recent error rate
        recent_errors = self._execute_query("""
            SELECT 
                COUNT(*) FILTER (WHERE status = 'failed') as errors,
                COUNT(*) as total
            FROM email_sessions 
            WHERE processing_started_at > NOW() - INTERVAL '1 hour'
        """)
        
        # Database stats
        db_stats = self._execute_query("""
            SELECT 
                COUNT(*) as total_sessions,
                COUNT(*) FILTER (WHERE processing_started_at > NOW() - INTERVAL '24 hours') as last_24h
            FROM email_sessions
        """)
        
        return {
            "error_rate": round(
                (recent_errors[0]['errors'] / max(recent_errors[0]['total'], 1)) * 100, 1
            ) if recent_errors else 0,
            "total_sessions": db_stats[0]['total_sessions'] if db_stats else 0,
            "sessions_24h": db_stats[0]['last_24h'] if db_stats else 0,
            "database_connected": bool(self.db_pool)
        }
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive summary of a processing session"""
        if not self.db_pool:
            return None
            
        conn = None
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                query = """
                    SELECT 
                        es.*,
                        cr.predicted_label,
                        cr.confidence_score,
                        de.client_matched,
                        de.documents_found,
                        dg.draft_length,
                        dg.context_used,
                        dg.draft_content,
                        dg.final_draft_content,
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
                cursor.execute(query, (session_id,))
                result = cursor.fetchall()
                return result[0] if result else None
        except Exception as e:
            print(f"Error fetching session summary: {e}")
            return None
        finally:
            if conn:
                self.db_pool.putconn(conn)

# Global dashboard service instance
dashboard = DashboardService()