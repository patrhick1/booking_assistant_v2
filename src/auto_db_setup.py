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
    results = cursor.fetchall()
    
    # Handle RealDictRow format
    existing_tables = [row['table_name'] for row in results]
    
    required_tables = [
        'email_sessions', 'node_executions', 'classification_results',
        'document_extractions', 'draft_generations', 'quality_feedback',
        'slack_interactions', 'prompt_templates', 'prompt_versions'
    ]
    
    missing_tables = [table for table in required_tables if table not in existing_tables]
    return missing_tables, existing_tables

def check_session_id_type(cursor) -> str:
    """Check the data type of email_sessions.id column"""
    try:
        cursor.execute("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'email_sessions' 
            AND column_name = 'id' 
            AND table_schema = 'public'
        """)
        result = cursor.fetchone()
        if result:
            return result['data_type']
        return 'uuid'  # default assumption
    except:
        return 'uuid'  # default assumption

def create_core_tables(cursor, fk_type="UUID"):
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
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS node_executions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id {fk_type} REFERENCES email_sessions(id) ON DELETE CASCADE,
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
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS classification_results (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id {fk_type} REFERENCES email_sessions(id) ON DELETE CASCADE,
            predicted_label VARCHAR(100) NOT NULL,
            confidence_score FLOAT,
            human_verified_label VARCHAR(100),
            is_correct BOOLEAN,
            feedback_timestamp TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    
    # Document extractions table
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS document_extractions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id {fk_type} REFERENCES email_sessions(id) ON DELETE CASCADE,
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
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS draft_generations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id {fk_type} REFERENCES email_sessions(id) ON DELETE CASCADE,
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
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS quality_feedback (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id {fk_type} REFERENCES email_sessions(id) ON DELETE CASCADE,
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
    
    # Slack interactions table (use compatible foreign key type)
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS slack_interactions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id {fk_type} REFERENCES email_sessions(id) ON DELETE CASCADE,
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

def create_prompt_tables(cursor, fk_type="UUID"):
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
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS prompt_usage (
            id SERIAL PRIMARY KEY,
            session_id {fk_type} REFERENCES email_sessions(id) ON DELETE CASCADE,
            prompt_name VARCHAR(100) NOT NULL,
            prompt_version_id UUID REFERENCES prompt_versions(id) ON DELETE CASCADE,
            node_name VARCHAR(100) NOT NULL,
            execution_time_ms INTEGER,
            success BOOLEAN DEFAULT TRUE,
            output_quality_score DECIMAL(5,4),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)

def create_workflow_tables(cursor, fk_type="UUID"):
    """Create workflow and system tables"""
    
    # Email workflows table
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS email_workflows (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id {fk_type} REFERENCES email_sessions(id) ON DELETE CASCADE,
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
        if 'src' not in sys.path:
            sys.path.append('src')
        try:
            from src import prompts
        except ImportError:
            # Try without src prefix
            import prompts
        
        essential_prompts = {
            "classification_fewshot": {
                "content": getattr(prompts, 'classification_fewshot', 'DEFAULT_CLASSIFICATION_PROMPT'),
                "description": "Few-shot examples for email classification",
                "category": "classification"
            },
            "draft_generation_prompt": {
                "content": getattr(prompts, 'draft_generation_prompt', 'DEFAULT_DRAFT_PROMPT'),
                "description": "Main prompt for generating email drafts",
                "category": "generation"
            },
            "continuation_decision_prompt": {
                "content": getattr(prompts, 'continuation_decision_prompt', 'DEFAULT_CONTINUATION_PROMPT'),
                "description": "Prompt for deciding whether to continue processing",
                "category": "decision"
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
                print(f"WARNING: Error creating prompt {prompt_name}: {str(e)}")
                print(f"         Exception type: {type(e).__name__}")
                import traceback
                print(f"         Traceback: {traceback.format_exc()[:200]}...")
        
        return created_count
        
    except ImportError:
        print("WARNING: Could not import prompts module")
        return 0

def auto_setup_database(db_pool) -> bool:
    """
    Automatically set up database if tables are missing
    This is called from the unified app startup
    """
    print("🔍 Starting auto database setup...")
    
    if not db_pool:
        print("❌ ERROR: No database connection available for auto-setup")
        return False
    
    try:
        print("📡 Getting database connection...")
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        print("🔍 Checking existing tables...")
        # Check what tables exist
        missing_tables, existing_tables = check_tables_exist(cursor)
        
        print(f"📊 Found {len(existing_tables)} existing tables")
        print(f"📋 Missing tables: {missing_tables}")
        
        if not missing_tables:
            print("✅ All database tables exist - no setup needed")
            db_pool.putconn(conn)
            return True
        
        print(f"🔧 Auto-creating {len(missing_tables)} missing database tables...")
        
        # Check existing session_id type for compatibility
        session_id_type = check_session_id_type(cursor)
        print(f"🔍 Detected email_sessions.id type: {session_id_type}")
        
        # Determine the correct foreign key type
        if session_id_type in ['character varying', 'varchar', 'text']:
            fk_type = "VARCHAR(255)"
        else:
            fk_type = "UUID"
        
        # Create tables
        print("📝 Creating core tables...")
        create_core_tables(cursor, fk_type)
        
        print("📝 Creating prompt tables...")
        create_prompt_tables(cursor, fk_type)
        
        print("📝 Creating workflow tables...")
        create_workflow_tables(cursor, fk_type)
        
        print("📝 Creating indexes...")
        create_basic_indexes(cursor)
        
        print("📝 Loading essential prompts...")
        # Load essential prompts
        prompt_count = load_essential_prompts(cursor)
        
        print("💾 Committing changes...")
        # Commit all changes
        conn.commit()
        
        print("✅ Verifying setup...")
        # Verify setup
        missing_after, existing_after = check_tables_exist(cursor)
        
        print(f"🎉 Database auto-setup complete!")
        print(f"   📊 Created tables: {len(existing_after) - len(existing_tables)}")
        print(f"   📝 Loaded prompts: {prompt_count}")
        
        db_pool.putconn(conn)
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Auto database setup failed: {e}")
        print(f"   Exception type: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        try:
            if 'conn' in locals():
                print("🔄 Rolling back transaction...")
                conn.rollback()
                db_pool.putconn(conn)
        except Exception as rollback_error:
            print(f"⚠️  Rollback error: {rollback_error}")
        return False

def ensure_database_ready(db_pool) -> bool:
    """
    Ensure database is ready for operations
    Call this from service initialization
    """
    return auto_setup_database(db_pool)