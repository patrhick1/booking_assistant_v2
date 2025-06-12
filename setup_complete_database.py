#!/usr/bin/env python3
"""
Complete Database Setup Script
Sets up all tables, triggers, and initial data for the BookingAssistant system
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')
load_dotenv()

def run_sql_file(db_pool, file_path: str) -> bool:
    """Run SQL commands from a file"""
    try:
        with open(file_path, 'r') as file:
            sql_content = file.read()
        
        conn = db_pool.getconn()
        with conn.cursor() as cursor:
            cursor.execute(sql_content)
            conn.commit()
        db_pool.putconn(conn)
        
        print(f"✅ Successfully executed: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error executing {file_path}: {e}")
        return False

def test_database_connection():
    """Test database connectivity"""
    try:
        from src.metrics_service import metrics
        
        if not metrics.db_pool:
            print("❌ No database connection available")
            return False
            
        conn = metrics.db_pool.getconn()
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ Database connected: {version}")
        metrics.db_pool.putconn(conn)
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def create_directories():
    """Create required directories"""
    directories = [
        'database',
        'database/schema', 
        'database/queries',
        'database/migrations'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Database directories created")

def setup_complete_schema():
    """Set up the complete database schema"""
    try:
        from src.metrics_service import metrics
        
        schema_file = "database/schema/complete_schema.sql"
        if not os.path.exists(schema_file):
            print(f"❌ Schema file not found: {schema_file}")
            return False
        
        return run_sql_file(metrics.db_pool, schema_file)
        
    except Exception as e:
        print(f"❌ Error setting up schema: {e}")
        return False

def load_default_prompts():
    """Load default prompts into the database"""
    try:
        from src import prompts
        from src.metrics_service import metrics
        import uuid
        
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
        
        conn = metrics.db_pool.getconn()
        created_count = 0
        existing_count = 0
        
        for prompt_name, prompt_data in default_prompts.items():
            try:
                with conn.cursor() as cursor:
                    # Check if prompt template exists
                    cursor.execute(
                        "SELECT COUNT(*) FROM prompt_templates WHERE prompt_name = %s",
                        (prompt_name,)
                    )
                    if cursor.fetchone()[0] > 0:
                        existing_count += 1
                        continue
                    
                    # Create prompt template
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
                    
                    conn.commit()
                    created_count += 1
                    print(f"✅ Created prompt: {prompt_name}")
                    
            except Exception as e:
                print(f"❌ Error creating prompt '{prompt_name}': {e}")
                conn.rollback()
        
        metrics.db_pool.putconn(conn)
        
        print(f"\n📊 Prompt Loading Summary:")
        print(f"   Created: {created_count}")
        print(f"   Existing: {existing_count}")
        
        return created_count > 0 or existing_count > 0
        
    except Exception as e:
        print(f"❌ Error loading prompts: {e}")
        return False

def verify_database_setup():
    """Verify that all tables and data are properly set up"""
    try:
        from src.metrics_service import metrics
        
        conn = metrics.db_pool.getconn()
        with conn.cursor() as cursor:
            # Check main tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'email_sessions', 'node_executions', 'classification_results',
                'document_extractions', 'draft_generations', 'quality_feedback',
                'slack_interactions', 'prompt_templates', 'prompt_versions',
                'prompt_usage', 'ab_test_configs', 'system_metrics',
                'user_sessions', 'email_workflows'
            ]
            
            missing_tables = [table for table in expected_tables if table not in tables]
            
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
                return False
            
            # Check prompts
            cursor.execute("SELECT COUNT(*) FROM prompt_templates")
            prompt_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM prompt_versions WHERE is_active = TRUE")
            active_prompts = cursor.fetchone()[0]
            
            # Check triggers
            cursor.execute("""
                SELECT trigger_name 
                FROM information_schema.triggers 
                WHERE trigger_schema = 'public'
            """)
            triggers = [row[0] for row in cursor.fetchall()]
            
        metrics.db_pool.putconn(conn)
        
        print(f"\n📊 Database Verification Results:")
        print(f"   Total tables: {len(tables)}")
        print(f"   Expected tables: {len(expected_tables)}")
        print(f"   Missing tables: {len(missing_tables)}")
        print(f"   Prompt templates: {prompt_count}")
        print(f"   Active prompts: {active_prompts}")
        print(f"   Database triggers: {len(triggers)}")
        
        success = (len(missing_tables) == 0 and 
                  prompt_count == 9 and 
                  active_prompts == 9 and
                  len(triggers) >= 3)
        
        if success:
            print(f"\n✅ Database setup verification: PASSED")
        else:
            print(f"\n❌ Database setup verification: FAILED")
        
        return success
        
    except Exception as e:
        print(f"❌ Error verifying database setup: {e}")
        return False

def test_database_operations():
    """Test basic database operations"""
    try:
        from src.database_service import database_service, SlackInteraction, QualityFeedback
        import uuid
        
        # Test session creation (would normally be done by main processing)
        print("\n🧪 Testing database operations...")
        
        # Test Slack interaction recording
        test_interaction = SlackInteraction(
            session_id=str(uuid.uuid4()),
            interaction_type="button_click",
            action_value="test_action",
            user_id="test_user",
            user_name="Test User",
            channel_id="test_channel",
            message_ts="123456789.123"
        )
        
        # This will fail gracefully if email_sessions doesn't have the test session
        # but will test the SQL query structure
        success = database_service.record_slack_interaction(test_interaction)
        print(f"   Slack interaction test: {'✅ PASSED' if success else '⚠️  Expected failure (no session)'}")
        
        # Test analytics queries
        stats = database_service.get_slack_interaction_stats(days=30)
        print(f"   Analytics query test: {'✅ PASSED' if isinstance(stats, list) else '❌ FAILED'}")
        
        workflow_states = database_service.get_workflow_states_summary(days=7)
        print(f"   Workflow query test: {'✅ PASSED' if isinstance(workflow_states, list) else '❌ FAILED'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing database operations: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 COMPLETE DATABASE SETUP")
    print("="*50)
    
    # Test database connection
    if not test_database_connection():
        print("❌ Cannot proceed without database connection")
        return False
    
    # Create directories
    create_directories()
    
    # Setup complete schema
    print(f"\n🏗️  Setting up complete database schema...")
    if not setup_complete_schema():
        print("❌ Failed to set up database schema")
        return False
    
    # Load default prompts
    print(f"\n📝 Loading default prompts...")
    if not load_default_prompts():
        print("❌ Failed to load default prompts")
        return False
    
    # Verify setup
    print(f"\n🔍 Verifying database setup...")
    if not verify_database_setup():
        print("❌ Database verification failed")
        return False
    
    # Test operations
    print(f"\n🧪 Testing database operations...")
    if not test_database_operations():
        print("❌ Database operations test failed")
        return False
    
    print(f"\n🎉 SUCCESS! Complete database setup finished!")
    print(f"\nNext steps:")
    print(f"   1. Restart secure_dashboard_app.py")
    print(f"   2. Test Slack interactions")
    print(f"   3. Process test emails")
    print(f"   4. Monitor database activity")
    
    return True

if __name__ == "__main__":
    main()