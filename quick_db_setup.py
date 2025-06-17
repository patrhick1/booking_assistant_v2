#!/usr/bin/env python3
"""
Quick Database Setup for Replit
Fixes the missing tables issue
"""

import sys
import os
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')
load_dotenv()

def main():
    print("🔧 QUICK DATABASE SETUP FOR REPLIT")
    print("="*50)
    
    try:
        # Import metrics service to get database connection
        from src.metrics_service import metrics
        
        if not metrics.db_pool:
            print("❌ No database connection available")
            print("   Check your Replit Secrets for database credentials")
            return False
        
        print("✅ Database connection available")
        
        # Get connection
        conn = metrics.db_pool.getconn()
        cursor = conn.cursor()
        
        # Check existing tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Found {len(existing_tables)} existing tables")
        
        # Required tables
        required_tables = [
            'email_sessions', 'node_executions', 'classification_results',
            'document_extractions', 'draft_generations', 'quality_feedback',
            'slack_interactions', 'prompt_templates', 'prompt_versions'
        ]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if not missing_tables:
            print("✅ All required tables already exist!")
            metrics.db_pool.putconn(conn)
            return True
        
        print(f"📋 Missing tables: {missing_tables}")
        print("🏗️  Creating tables from schema file...")
        
        # Read and execute schema
        schema_file = "database/schema/complete_schema.sql"
        if not os.path.exists(schema_file):
            print(f"❌ Schema file not found: {schema_file}")
            metrics.db_pool.putconn(conn)
            return False
        
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema
        cursor.execute(schema_sql)
        conn.commit()
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        new_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"✅ Database now has {len(new_tables)} tables")
        
        # Create default prompts
        print("📝 Loading default prompts...")
        try:
            from src import prompts
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
                }
            }
            
            created_count = 0
            for prompt_name, prompt_data in default_prompts.items():
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
                    
                    conn.commit()
                    created_count += 1
                    
                except Exception as e:
                    print(f"⚠️  Error creating prompt {prompt_name}: {e}")
                    conn.rollback()
            
            print(f"✅ Created {created_count} default prompts")
            
        except Exception as e:
            print(f"⚠️  Error loading prompts: {e}")
        
        metrics.db_pool.putconn(conn)
        
        print("\n🎉 DATABASE SETUP COMPLETE!")
        print("   Restart your Replit to see the changes")
        print("   Visit /health to verify all services are working")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()