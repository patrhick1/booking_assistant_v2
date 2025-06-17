#!/usr/bin/env python3
"""
Replit Database Setup using psycopg2
Creates all required tables and schema programmatically
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Get direct psycopg2 connection to PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('PGHOST'),
            database=os.getenv('PGDATABASE'),
            user=os.getenv('PGUSER'),
            password=os.getenv('PGPASSWORD'),
            port=os.getenv('PGPORT', 5432),
            sslmode='require'
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def create_email_sessions_table(cursor):
    """Create email_sessions table"""
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
    print("✅ Created email_sessions table")

def create_node_executions_table(cursor):
    """Create node_executions table"""
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
    print("✅ Created node_executions table")

def create_classification_results_table(cursor):
    """Create classification_results table"""
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
    print("✅ Created classification_results table")

def create_document_extractions_table(cursor):
    """Create document_extractions table"""
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
    print("✅ Created document_extractions table")

def create_draft_generations_table(cursor):
    """Create draft_generations table"""
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
    print("✅ Created draft_generations table")

def create_quality_feedback_table(cursor):
    """Create quality_feedback table"""
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
    print("✅ Created quality_feedback table")

def create_slack_interactions_table(cursor):
    """Create slack_interactions table"""
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
    print("✅ Created slack_interactions table")

def create_prompt_templates_table(cursor):
    """Create prompt_templates table"""
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
    print("✅ Created prompt_templates table")

def create_prompt_versions_table(cursor):
    """Create prompt_versions table"""
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
    print("✅ Created prompt_versions table")

def create_prompt_usage_table(cursor):
    """Create prompt_usage table"""
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
    print("✅ Created prompt_usage table")

def create_system_metrics_table(cursor):
    """Create system_metrics table"""
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
    print("✅ Created system_metrics table")

def create_email_workflows_table(cursor):
    """Create email_workflows table"""
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
    print("✅ Created email_workflows table")

def create_indexes(cursor):
    """Create performance indexes"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_email_sessions_processing_started ON email_sessions(processing_started_at)",
        "CREATE INDEX IF NOT EXISTS idx_email_sessions_status ON email_sessions(status)",
        "CREATE INDEX IF NOT EXISTS idx_email_sessions_classification ON email_sessions(classification)",
        "CREATE INDEX IF NOT EXISTS idx_email_sessions_sender ON email_sessions(sender_email)",
        "CREATE INDEX IF NOT EXISTS idx_node_executions_session_node ON node_executions(session_id, node_name)",
        "CREATE INDEX IF NOT EXISTS idx_classification_results_session ON classification_results(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_document_extractions_session ON document_extractions(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_draft_generations_session ON draft_generations(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_quality_feedback_session ON quality_feedback(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_slack_interactions_session ON slack_interactions(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_prompt_versions_name ON prompt_versions(prompt_name)",
        "CREATE INDEX IF NOT EXISTS idx_prompt_versions_active ON prompt_versions(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_email_workflows_session ON email_workflows(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_system_metrics_name_timestamp ON system_metrics(metric_name, timestamp)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    print("✅ Created performance indexes")

def create_triggers_and_functions(cursor):
    """Create triggers and functions"""
    # Update timestamp function
    cursor.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    """)
    
    # Triggers for updated_at columns
    cursor.execute("""
        DROP TRIGGER IF EXISTS update_email_sessions_updated_at ON email_sessions;
        CREATE TRIGGER update_email_sessions_updated_at 
            BEFORE UPDATE ON email_sessions 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    
    cursor.execute("""
        DROP TRIGGER IF EXISTS update_quality_feedback_updated_at ON quality_feedback;
        CREATE TRIGGER update_quality_feedback_updated_at 
            BEFORE UPDATE ON quality_feedback 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    
    cursor.execute("""
        DROP TRIGGER IF EXISTS update_email_workflows_updated_at ON email_workflows;
        CREATE TRIGGER update_email_workflows_updated_at 
            BEFORE UPDATE ON email_workflows 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    
    print("✅ Created triggers and functions")

def load_default_prompts(cursor):
    """Load default prompt templates"""
    # Add src to path for imports
    sys.path.append('src')
    
    try:
        from src import prompts
        
        default_prompts = {
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
            },
            "query_for_relevant_email_prompt": {
                "content": prompts.query_for_relevant_email_prompt,
                "description": "Prompt for generating vector search queries",
                "category": "retrieval"
            },
            "rejection_strategy_prompt": {
                "content": prompts.rejection_strategy_prompt,
                "description": "Prompt for analyzing rejection strategies",
                "category": "rejection"
            },
            "soft_rejection_drafting_prompt": {
                "content": prompts.soft_rejection_drafting_prompt,
                "description": "Prompt for drafting soft rejection responses",
                "category": "rejection"
            },
            "draft_editing_prompt": {
                "content": prompts.draft_editing_prompt,
                "description": "Prompt for editing and refining drafts",
                "category": "editing"
            },
            "continuation_decision_prompt": {
                "content": prompts.continuation_decision_prompt,
                "description": "Prompt for deciding whether to continue processing",
                "category": "decision"
            },
            "client_gdrive_extract_prompt": {
                "content": prompts.client_gdrive_extract_prompt,
                "description": "Prompt for client document extraction",
                "category": "extraction"
            }
        }
        
        created_count = 0
        for prompt_name, prompt_data in default_prompts.items():
            try:
                # Check if template exists
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
                
                # Create initial version
                version_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO prompt_versions 
                    (id, prompt_name, version, content, description, created_by, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (version_id, prompt_name, 1, prompt_data["content"], "Initial version", "system", True))
                
                created_count += 1
                
            except Exception as e:
                print(f"⚠️  Error creating prompt {prompt_name}: {e}")
        
        print(f"✅ Loaded {created_count} default prompts")
        return created_count
        
    except ImportError as e:
        print(f"⚠️  Could not import prompts module: {e}")
        return 0

def main():
    """Main setup function"""
    print("🚀 REPLIT DATABASE SETUP (psycopg2)")
    print("="*50)
    
    # Check environment variables
    required_vars = ['PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("   Please check your Replit Secrets configuration")
        return False
    
    # Get database connection
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check existing tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Found {len(existing_tables)} existing tables")
        
        # Create all tables
        print("\n🏗️  Creating database schema...")
        create_email_sessions_table(cursor)
        create_node_executions_table(cursor)
        create_classification_results_table(cursor)
        create_document_extractions_table(cursor)
        create_draft_generations_table(cursor)
        create_quality_feedback_table(cursor)
        create_slack_interactions_table(cursor)
        create_prompt_templates_table(cursor)
        create_prompt_versions_table(cursor)
        create_prompt_usage_table(cursor)
        create_system_metrics_table(cursor)
        create_email_workflows_table(cursor)
        
        # Create indexes and triggers
        print("\n📈 Creating indexes and triggers...")
        create_indexes(cursor)
        create_triggers_and_functions(cursor)
        
        # Commit schema changes
        conn.commit()
        
        # Load default prompts
        print("\n📝 Loading default prompts...")
        prompt_count = load_default_prompts(cursor)
        conn.commit()
        
        # Final verification
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        final_tables = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT COUNT(*) FROM prompt_templates")
        template_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM prompt_versions WHERE is_active = TRUE")
        active_prompts = cursor.fetchone()[0]
        
        print(f"\n📊 SETUP COMPLETE!")
        print(f"   Database tables: {len(final_tables)}")
        print(f"   Prompt templates: {template_count}")
        print(f"   Active prompts: {active_prompts}")
        
        print(f"\n🎉 SUCCESS!")
        print(f"   Restart your Replit now")
        print(f"   Visit /health to verify all services")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()