"""
Auto Database Setup Module
Automatically creates database schema if tables don't exist
"""

import os
import sys
import uuid
from typing import List, Dict, Any

def check_tables_exist(cursor) -> List[str]:
    """Check which required tables exist"""
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    required_tables = [
        'email_sessions', 'node_executions', 'classification_results',
        'document_extractions', 'draft_generations', 'quality_feedback',
        'slack_interactions', 'prompt_templates', 'prompt_versions'
    ]
    
    missing_tables = [table for table in required_tables if table not in existing_tables]
    return missing_tables, existing_tables

def create_core_tables(cursor):
    """Create core database tables"""
    
    # Email sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email_hash VARCHAR(64) UNIQUE NOT NULL,
            sender_email VARCHAR(255) NOT NULL,
            sender_name VARCHAR(255),
            subject TEXT,
            email_content TEXT,
            classification VARCHAR(100),
            processing_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            processing_completed_at TIMESTAMP WITH TIME ZONE,
            total_duration_ms INTEGER,
            status VARCHAR(50) DEFAULT 'processing',
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    
    # Node executions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS node_executions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id UUID REFERENCES email_sessions(id) ON DELETE CASCADE,
            node_name VARCHAR(100) NOT NULL,
            started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            completed_at TIMESTAMP WITH TIME ZONE,
            duration_ms INTEGER,
            success BOOLEAN DEFAULT TRUE,
            error_message TEXT,
            input_data JSONB,
            output_data JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    
    # Classification results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classification_results (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id UUID REFERENCES email_sessions(id) ON DELETE CASCADE,
            predicted_label VARCHAR(100) NOT NULL,
            confidence_score FLOAT,
            human_verified_label VARCHAR(100),
            is_correct BOOLEAN,
            feedback_timestamp TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    
    # Document extractions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_extractions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id UUID REFERENCES email_sessions(id) ON DELETE CASCADE,
            client_folders_found INTEGER DEFAULT 0,
            client_matched BOOLEAN DEFAULT FALSE,
            client_folder_id VARCHAR(255),
            client_name VARCHAR(255),
            documents_found INTEGER DEFAULT 0,
            document_selected BOOLEAN DEFAULT FALSE,
            selected_document_id VARCHAR(255),
            selected_document_name VARCHAR(255),
            extraction_success BOOLEAN DEFAULT FALSE,
            extraction_duration_ms INTEGER,
            error_reason TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    
    # Draft generations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS draft_generations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id UUID REFERENCES email_sessions(id) ON DELETE CASCADE,
            draft_content TEXT,
            final_draft_content TEXT,
            draft_length INTEGER,
            final_draft_length INTEGER,
            context_used BOOLEAN DEFAULT FALSE,
            context_length INTEGER DEFAULT 0,
            vector_threads_used INTEGER DEFAULT 0,
            placeholders_count INTEGER DEFAULT 0,
            template_adherence_score FLOAT,
            auto_quality_score FLOAT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    
    # Quality feedback table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_feedback (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id UUID REFERENCES email_sessions(id) ON DELETE CASCADE,
            human_action VARCHAR(50),
            human_rating INTEGER CHECK (human_rating >= 1 AND human_rating <= 5),
            edit_distance INTEGER DEFAULT 0,
            edit_type VARCHAR(50),
            approval_timestamp TIMESTAMP WITH TIME ZONE,
            feedback_notes TEXT,
            slack_message_id VARCHAR(100),
            slack_channel_id VARCHAR(100),
            slack_user_id VARCHAR(100),
            slack_user_name VARCHAR(100),
            gmail_draft_created BOOLEAN DEFAULT FALSE,
            gmail_draft_sent BOOLEAN DEFAULT FALSE,
            final_quality_score FLOAT,
            interaction_metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    
    # Slack interactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS slack_interactions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id UUID REFERENCES email_sessions(id) ON DELETE CASCADE,
            interaction_type VARCHAR(50) NOT NULL,
            action_value VARCHAR(100),
            user_id VARCHAR(100),
            user_name VARCHAR(100),
            channel_id VARCHAR(100),
            message_ts VARCHAR(100),
            trigger_id VARCHAR(100),
            response_time_ms INTEGER,
            payload JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

def create_prompt_tables(cursor):
    """Create prompt management tables"""
    
    # Prompt templates table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompt_templates (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            prompt_name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            category VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Prompt versions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            prompt_name VARCHAR(100) REFERENCES prompt_templates(prompt_name) ON DELETE CASCADE,
            version INTEGER NOT NULL,
            content TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(100),
            is_active BOOLEAN DEFAULT FALSE,
            performance_score DECIMAL(5,4) DEFAULT 0.0,
            usage_count INTEGER DEFAULT 0,
            UNIQUE(prompt_name, version)
        )
    """)
    
    # Prompt usage table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompt_usage (
            id SERIAL PRIMARY KEY,
            session_id UUID REFERENCES email_sessions(id) ON DELETE CASCADE,
            prompt_name VARCHAR(100) NOT NULL,
            prompt_version_id UUID REFERENCES prompt_versions(id) ON DELETE CASCADE,
            node_name VARCHAR(100) NOT NULL,
            execution_time_ms INTEGER,
            success BOOLEAN DEFAULT TRUE,
            output_quality_score DECIMAL(5,4),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)

def create_workflow_tables(cursor):
    """Create workflow and system tables"""
    
    # Email workflows table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_workflows (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id UUID REFERENCES email_sessions(id) ON DELETE CASCADE,
            workflow_state VARCHAR(50) DEFAULT 'draft_created',
            current_step VARCHAR(100),
            next_actions JSONB,
            assigned_to VARCHAR(100),
            deadline TIMESTAMP WITH TIME ZONE,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    
    # System metrics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_metrics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            metric_name VARCHAR(100) NOT NULL,
            metric_value FLOAT NOT NULL,
            metric_unit VARCHAR(50),
            tags JSONB,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

def create_basic_indexes(cursor):
    """Create essential indexes"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_email_sessions_processing_started ON email_sessions(processing_started_at)",
        "CREATE INDEX IF NOT EXISTS idx_email_sessions_status ON email_sessions(status)",
        "CREATE INDEX IF NOT EXISTS idx_node_executions_session_node ON node_executions(session_id, node_name)",
        "CREATE INDEX IF NOT EXISTS idx_classification_results_session ON classification_results(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_slack_interactions_session ON slack_interactions(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_prompt_versions_name ON prompt_versions(prompt_name)",
        "CREATE INDEX IF NOT EXISTS idx_prompt_versions_active ON prompt_versions(is_active)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)

def load_essential_prompts(cursor):
    """Load essential prompts for system operation"""
    try:
        # Add src to path for imports
        sys.path.append('src')
        from src import prompts
        
        essential_prompts = {
            "classification_fewshot": {
                "content": prompts.classification_fewshot,
                "description": "Few-shot examples for email classification",
                "category": "classification"
            },
            "draft_generation_prompt": {
                "content": prompts.draft_generation_prompt,
                "description": "Main prompt for generating email drafts",
                "category": "generation"
            },
            "slack_notification_prompt": {
                "content": prompts.slack_notification_prompt,
                "description": "Prompt for Slack notification messages",
                "category": "notification"
            }
        }
        
        created_count = 0
        for prompt_name, prompt_data in essential_prompts.items():
            try:
                # Check if exists
                cursor.execute(
                    "SELECT COUNT(*) FROM prompt_templates WHERE prompt_name = %s",
                    (prompt_name,)
                )
                if cursor.fetchone()[0] > 0:
                    continue
                
                # Create template
                template_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO prompt_templates (id, prompt_name, description, category)
                    VALUES (%s, %s, %s, %s)
                """, (template_id, prompt_name, prompt_data["description"], prompt_data["category"]))
                
                # Create version
                version_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO prompt_versions 
                    (id, prompt_name, version, content, description, created_by, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (version_id, prompt_name, 1, prompt_data["content"], "Initial version", "system", True))
                
                created_count += 1
                
            except Exception as e:
                print(f"⚠️  Error creating prompt {prompt_name}: {e}")
        
        return created_count
        
    except ImportError:
        print("⚠️  Could not import prompts module")
        return 0

def auto_setup_database(db_pool) -> bool:
    """
    Automatically set up database if tables are missing
    This is called from the unified app startup
    """
    if not db_pool:
        print("❌ No database connection available for auto-setup")
        return False
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Check what tables exist
        missing_tables, existing_tables = check_tables_exist(cursor)
        
        if not missing_tables:
            print("✅ All database tables exist - no setup needed")
            db_pool.putconn(conn)
            return True
        
        print(f"🔧 Auto-creating {len(missing_tables)} missing database tables...")
        
        # Create tables
        create_core_tables(cursor)
        create_prompt_tables(cursor)
        create_workflow_tables(cursor)
        create_basic_indexes(cursor)
        
        # Load essential prompts
        prompt_count = load_essential_prompts(cursor)
        
        # Commit all changes
        conn.commit()
        
        # Verify setup
        missing_after, existing_after = check_tables_exist(cursor)
        
        print(f"✅ Database auto-setup complete!")
        print(f"   Created tables: {len(existing_after) - len(existing_tables)}")
        print(f"   Loaded prompts: {prompt_count}")
        
        db_pool.putconn(conn)
        return True
        
    except Exception as e:
        print(f"❌ Auto database setup failed: {e}")
        conn.rollback()
        db_pool.putconn(conn)
        return False

def ensure_database_ready(db_pool) -> bool:
    """
    Ensure database is ready for operations
    Call this from service initialization
    """
    return auto_setup_database(db_pool)