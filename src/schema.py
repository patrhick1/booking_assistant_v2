"""
Database Schema Management for BookingAssistant
Secure database operations with SQL injection protection using psycopg2
"""

import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    """Secure database manager with SQL injection protection"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('PGHOST'),
            'port': os.getenv('PGPORT', 5432),
            'database': os.getenv('PGDATABASE'),
            'user': os.getenv('PGUSER'),
            'password': os.getenv('PGPASSWORD')
        }
        
        # Validate required environment variables
        required_vars = ['PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        self.pool = None
        self._init_connection_pool()
    
    def _init_connection_pool(self):
        """Initialize secure connection pool"""
        try:
            self.pool = SimpleConnectionPool(
                minconn=2,
                maxconn=50,  # Increased from 20 to handle concurrent email processing
                cursor_factory=RealDictCursor,
                **self.db_config
            )
            print("✅ Database connection pool initialized")
        except Exception as e:
            print(f"❌ Failed to initialize database connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager for secure database connections"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.pool.putconn(conn)
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = False) -> Optional[List[Dict]]:
        """
        Execute SQL query with parameterized statements to prevent SQL injection
        
        Args:
            query: SQL query with %s placeholders
            params: Parameters to safely substitute into query
            fetch: Whether to fetch and return results
        
        Returns:
            Query results if fetch=True, None otherwise
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if fetch:
                    return cursor.fetchall()
                conn.commit()
                return None
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """
        Execute query multiple times with different parameters
        Uses executemany for better performance and security
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(query, params_list)
                conn.commit()
    
    def create_all_tables(self) -> bool:
        """Create all database tables with proper constraints and indexes"""
        try:
            self._create_email_sessions_table()
            self._create_node_executions_table()
            self._create_classification_results_table()
            self._create_document_extractions_table()
            self._create_draft_generations_table()
            self._create_quality_feedback_table()
            self._create_prompt_management_tables()
            self._create_audit_logs_table()
            self._create_indexes()
            print("✅ All database tables created successfully")
            return True
        except Exception as e:
            print(f"❌ Error creating database tables: {e}")
            return False
    
    def _create_email_sessions_table(self):
        """Create email_sessions table with proper constraints"""
        query = """
        CREATE TABLE IF NOT EXISTS email_sessions (
            id VARCHAR(36) PRIMARY KEY,
            email_hash VARCHAR(64) UNIQUE NOT NULL,
            sender_email VARCHAR(255) NOT NULL,
            sender_name VARCHAR(255),
            subject TEXT,
            processing_started_at TIMESTAMP WITH TIME ZONE NOT NULL,
            processing_completed_at TIMESTAMP WITH TIME ZONE,
            total_duration_ms INTEGER CHECK (total_duration_ms >= 0),
            status VARCHAR(20) NOT NULL DEFAULT 'processing' 
                CHECK (status IN ('processing', 'completed', 'failed')),
            classification VARCHAR(100),
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.execute_query(query)
    
    def _create_node_executions_table(self):
        """Create node_executions table with foreign key constraints"""
        query = """
        CREATE TABLE IF NOT EXISTS node_executions (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL REFERENCES email_sessions(id) ON DELETE CASCADE,
            node_name VARCHAR(100) NOT NULL,
            started_at TIMESTAMP WITH TIME ZONE NOT NULL,
            completed_at TIMESTAMP WITH TIME ZONE,
            duration_ms INTEGER CHECK (duration_ms >= 0),
            success BOOLEAN NOT NULL DEFAULT FALSE,
            error_message TEXT,
            input_data JSONB,
            output_data JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.execute_query(query)
    
    def _create_classification_results_table(self):
        """Create classification_results table"""
        query = """
        CREATE TABLE IF NOT EXISTS classification_results (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL REFERENCES email_sessions(id) ON DELETE CASCADE,
            predicted_label VARCHAR(100) NOT NULL,
            confidence_score DECIMAL(5,4) CHECK (confidence_score >= 0 AND confidence_score <= 1),
            processing_time_ms INTEGER CHECK (processing_time_ms >= 0),
            model_version VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.execute_query(query)
    
    def _create_document_extractions_table(self):
        """Create document_extractions table"""
        query = """
        CREATE TABLE IF NOT EXISTS document_extractions (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL REFERENCES email_sessions(id) ON DELETE CASCADE,
            client_matched BOOLEAN NOT NULL DEFAULT FALSE,
            client_name VARCHAR(255),
            documents_found INTEGER NOT NULL DEFAULT 0 CHECK (documents_found >= 0),
            extraction_success BOOLEAN NOT NULL DEFAULT FALSE,
            extraction_duration_ms INTEGER CHECK (extraction_duration_ms >= 0),
            error_reason TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.execute_query(query)
    
    def _create_draft_generations_table(self):
        """Create draft_generations table"""
        query = """
        CREATE TABLE IF NOT EXISTS draft_generations (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL REFERENCES email_sessions(id) ON DELETE CASCADE,
            draft_length INTEGER NOT NULL CHECK (draft_length >= 0),
            final_draft_length INTEGER CHECK (final_draft_length >= 0),
            context_used BOOLEAN NOT NULL DEFAULT FALSE,
            context_length INTEGER NOT NULL DEFAULT 0 CHECK (context_length >= 0),
            vector_threads_used INTEGER NOT NULL DEFAULT 0 CHECK (vector_threads_used >= 0),
            placeholders_count INTEGER NOT NULL DEFAULT 0 CHECK (placeholders_count >= 0),
            template_adherence_score DECIMAL(5,4) CHECK (template_adherence_score >= 0 AND template_adherence_score <= 1),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.execute_query(query)
    
    def _create_quality_feedback_table(self):
        """Create quality_feedback table"""
        query = """
        CREATE TABLE IF NOT EXISTS quality_feedback (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL REFERENCES email_sessions(id) ON DELETE CASCADE,
            human_action VARCHAR(50) NOT NULL 
                CHECK (human_action IN ('rated', 'approved', 'rejected', 'edited', 'feedback_added')),
            human_rating INTEGER CHECK (human_rating >= 1 AND human_rating <= 5),
            feedback_text TEXT,
            slack_message_id VARCHAR(100),
            feedback_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            user_id VARCHAR(100),
            edit_distance INTEGER CHECK (edit_distance >= 0),
            final_quality_score DECIMAL(5,4) CHECK (final_quality_score >= 0 AND final_quality_score <= 1),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.execute_query(query)
    
    def _create_prompt_management_tables(self):
        """Create prompt management tables"""
        
        # Prompt templates table
        query1 = """
        CREATE TABLE IF NOT EXISTS prompt_templates (
            id VARCHAR(36) PRIMARY KEY,
            prompt_name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            category VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.execute_query(query1)
        
        # Prompt versions table
        query2 = """
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id VARCHAR(36) PRIMARY KEY,
            prompt_name VARCHAR(100) NOT NULL REFERENCES prompt_templates(prompt_name) ON DELETE CASCADE,
            version INTEGER NOT NULL CHECK (version > 0),
            content TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(100) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT FALSE,
            performance_score DECIMAL(5,4) DEFAULT 0.0 CHECK (performance_score >= 0 AND performance_score <= 1),
            usage_count INTEGER NOT NULL DEFAULT 0 CHECK (usage_count >= 0),
            UNIQUE(prompt_name, version)
        )
        """
        self.execute_query(query2)
        
        # Prompt usage tracking table
        query3 = """
        CREATE TABLE IF NOT EXISTS prompt_usage (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL REFERENCES email_sessions(id) ON DELETE CASCADE,
            prompt_name VARCHAR(100) NOT NULL,
            prompt_version_id VARCHAR(36) NOT NULL REFERENCES prompt_versions(id) ON DELETE CASCADE,
            node_name VARCHAR(100) NOT NULL,
            execution_time_ms INTEGER CHECK (execution_time_ms >= 0),
            success BOOLEAN NOT NULL DEFAULT TRUE,
            output_quality_score DECIMAL(5,4) CHECK (output_quality_score >= 0 AND output_quality_score <= 1),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.execute_query(query3)
        
        # A/B test configurations table
        query4 = """
        CREATE TABLE IF NOT EXISTS ab_test_configs (
            id VARCHAR(36) PRIMARY KEY,
            test_name VARCHAR(100) NOT NULL UNIQUE,
            prompt_name VARCHAR(100) NOT NULL,
            variant_a_version_id VARCHAR(36) NOT NULL REFERENCES prompt_versions(id),
            variant_b_version_id VARCHAR(36) NOT NULL REFERENCES prompt_versions(id),
            traffic_split DECIMAL(3,2) NOT NULL DEFAULT 0.5 
                CHECK (traffic_split >= 0 AND traffic_split <= 1),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            start_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            end_date TIMESTAMP WITH TIME ZONE,
            created_by VARCHAR(100) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.execute_query(query4)
    
    def _create_audit_logs_table(self):
        """Create audit logs table for security tracking"""
        query = """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(100) NOT NULL,
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(50) NOT NULL,
            resource_id VARCHAR(100),
            old_values JSONB,
            new_values JSONB,
            ip_address INET,
            user_agent TEXT,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            success BOOLEAN NOT NULL DEFAULT TRUE,
            error_message TEXT
        )
        """
        self.execute_query(query)
    
    def _create_indexes(self):
        """Create database indexes for optimal performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_email_sessions_sender ON email_sessions(sender_email)",
            "CREATE INDEX IF NOT EXISTS idx_email_sessions_status ON email_sessions(status)",
            "CREATE INDEX IF NOT EXISTS idx_email_sessions_started_at ON email_sessions(processing_started_at)",
            "CREATE INDEX IF NOT EXISTS idx_email_sessions_hash ON email_sessions(email_hash)",
            
            "CREATE INDEX IF NOT EXISTS idx_node_executions_session ON node_executions(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_node_executions_node_name ON node_executions(node_name)",
            "CREATE INDEX IF NOT EXISTS idx_node_executions_started_at ON node_executions(started_at)",
            
            "CREATE INDEX IF NOT EXISTS idx_classification_results_session ON classification_results(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_classification_results_label ON classification_results(predicted_label)",
            
            "CREATE INDEX IF NOT EXISTS idx_document_extractions_session ON document_extractions(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_document_extractions_client ON document_extractions(client_matched)",
            
            "CREATE INDEX IF NOT EXISTS idx_draft_generations_session ON draft_generations(session_id)",
            
            "CREATE INDEX IF NOT EXISTS idx_quality_feedback_session ON quality_feedback(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_quality_feedback_action ON quality_feedback(human_action)",
            "CREATE INDEX IF NOT EXISTS idx_quality_feedback_timestamp ON quality_feedback(feedback_timestamp)",
            
            "CREATE INDEX IF NOT EXISTS idx_prompt_versions_name ON prompt_versions(prompt_name)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_versions_active ON prompt_versions(is_active)",
            
            "CREATE INDEX IF NOT EXISTS idx_prompt_usage_session ON prompt_usage(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_prompt_usage_name ON prompt_usage(prompt_name)",
            
            "CREATE INDEX IF NOT EXISTS idx_ab_test_active ON ab_test_configs(is_active)",
            
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)"
        ]
        
        for index_query in indexes:
            try:
                self.execute_query(index_query)
            except Exception as e:
                print(f"Warning: Could not create index: {e}")
    
    def insert_email_session(self, session_data: Dict[str, Any]) -> bool:
        """Securely insert email session with parameterized query"""
        query = """
        INSERT INTO email_sessions 
        (id, email_hash, sender_email, sender_name, subject, processing_started_at, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            session_data['id'],
            session_data['email_hash'],
            session_data['sender_email'],
            session_data.get('sender_name'),
            session_data.get('subject'),
            session_data['processing_started_at'],
            session_data.get('status', 'processing')
        )
        
        try:
            self.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error inserting email session: {e}")
            return False
    
    def log_audit_event(self, user_id: str, action: str, resource_type: str, 
                       resource_id: str = None, old_values: Dict = None, 
                       new_values: Dict = None, ip_address: str = None,
                       user_agent: str = None, success: bool = True, 
                       error_message: str = None) -> bool:
        """Log audit event for security tracking"""
        query = """
        INSERT INTO audit_logs 
        (user_id, action, resource_type, resource_id, old_values, new_values, 
         ip_address, user_agent, success, error_message)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            user_id, action, resource_type, resource_id,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None,
            ip_address, user_agent, success, error_message
        )
        
        try:
            self.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Error logging audit event: {e}")
            return False
    
    def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = %s
        )
        """
        result = self.execute_query(query, (table_name,), fetch=True)
        return result[0]['exists'] if result else False
    
    def get_table_info(self) -> List[Dict[str, Any]]:
        """Get information about all tables in the database"""
        query = """
        SELECT 
            schemaname,
            tablename,
            tableowner,
            tablespace,
            hasindexes,
            hasrules,
            hastriggers,
            rowsecurity
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY tablename
        """
        return self.execute_query(query, fetch=True) or []

# Global database manager instance
db_manager = DatabaseManager()