"""
Prompt Management Service for BookingAssistant
Provides dynamic prompt management, versioning, and A/B testing
"""

import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from src.metrics_service import metrics

@dataclass
class PromptVersion:
    """Represents a version of a prompt"""
    id: str
    prompt_name: str
    version: int
    content: str
    description: str
    created_at: str
    created_by: str
    is_active: bool = False
    performance_score: float = 0.0
    usage_count: int = 0

class PromptManager:
    """Service for managing prompts with versioning and A/B testing"""
    
    def __init__(self):
        try:
            self.db_pool = metrics.db_pool
            self._ensure_tables_exist()
            self._load_default_prompts()
        except Exception as e:
            print(f"⚠️  Prompt manager initialization failed: {e}")
            print("   Falling back to static prompts from prompts.py")
            self.db_pool = None
    
    def _ensure_tables_exist(self):
        """Create prompt management tables if they don't exist"""
        if not self.db_pool:
            return
        
        create_tables_sql = """
        -- Prompt Templates Table
        CREATE TABLE IF NOT EXISTS prompt_templates (
            id VARCHAR(36) PRIMARY KEY,
            prompt_name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            category VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Prompt Versions Table
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id VARCHAR(36) PRIMARY KEY,
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
        );
        
        -- Prompt Usage Tracking Table
        CREATE TABLE IF NOT EXISTS prompt_usage (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(36) REFERENCES email_sessions(id) ON DELETE CASCADE,
            prompt_name VARCHAR(100) NOT NULL,
            prompt_version_id VARCHAR(36) REFERENCES prompt_versions(id) ON DELETE CASCADE,
            node_name VARCHAR(100) NOT NULL,
            execution_time_ms INTEGER,
            success BOOLEAN DEFAULT TRUE,
            output_quality_score DECIMAL(5,4),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        -- A/B Test Configurations Table
        CREATE TABLE IF NOT EXISTS ab_test_configs (
            id VARCHAR(36) PRIMARY KEY,
            test_name VARCHAR(100) NOT NULL UNIQUE,
            prompt_name VARCHAR(100) NOT NULL,
            variant_a_version_id VARCHAR(36) REFERENCES prompt_versions(id),
            variant_b_version_id VARCHAR(36) REFERENCES prompt_versions(id),
            traffic_split DECIMAL(3,2) DEFAULT 0.5, -- 0.5 = 50/50 split
            is_active BOOLEAN DEFAULT TRUE,
            start_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            end_date TIMESTAMP WITH TIME ZONE,
            created_by VARCHAR(100),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_prompt_versions_name ON prompt_versions(prompt_name);
        CREATE INDEX IF NOT EXISTS idx_prompt_versions_active ON prompt_versions(is_active);
        CREATE INDEX IF NOT EXISTS idx_prompt_usage_session ON prompt_usage(session_id);
        CREATE INDEX IF NOT EXISTS idx_prompt_usage_name ON prompt_usage(prompt_name);
        CREATE INDEX IF NOT EXISTS idx_ab_test_active ON ab_test_configs(is_active);
        """
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute(create_tables_sql)
                conn.commit()
            self.db_pool.putconn(conn)
            print("✅ Prompt management tables created/verified")
        except Exception as e:
            print(f"❌ Error creating prompt tables: {e}")
    
    def _load_default_prompts(self):
        """Load default prompts from prompts.py into database"""
        try:
            from src.prompts import (
                classification_fewshot, draft_generation_prompt, slack_notification_prompt,
                query_for_relevant_email_prompt, rejection_strategy_prompt,
                soft_rejection_drafting_prompt, draft_editing_prompt, 
                continuation_decision_prompt, client_gdrive_extract_prompt
            )
            
            default_prompts = {
                "classification_fewshot": {
                    "content": classification_fewshot,
                    "description": "Few-shot examples for email classification",
                    "category": "classification"
                },
                "draft_generation_prompt": {
                    "content": draft_generation_prompt,
                    "description": "Main prompt for generating email drafts",
                    "category": "generation"
                },
                "slack_notification_prompt": {
                    "content": slack_notification_prompt,
                    "description": "Prompt for Slack notification messages",
                    "category": "notification"
                },
                "query_for_relevant_email_prompt": {
                    "content": query_for_relevant_email_prompt,
                    "description": "Prompt for generating vector search queries",
                    "category": "retrieval"
                },
                "rejection_strategy_prompt": {
                    "content": rejection_strategy_prompt,
                    "description": "Prompt for analyzing rejection strategies",
                    "category": "rejection"
                },
                "soft_rejection_drafting_prompt": {
                    "content": soft_rejection_drafting_prompt,
                    "description": "Prompt for drafting soft rejection responses",
                    "category": "rejection"
                },
                "draft_editing_prompt": {
                    "content": draft_editing_prompt,
                    "description": "Prompt for editing and refining drafts",
                    "category": "editing"
                },
                "continuation_decision_prompt": {
                    "content": continuation_decision_prompt,
                    "description": "Prompt for deciding whether to continue processing",
                    "category": "decision"
                },
                "client_gdrive_extract_prompt": {
                    "content": client_gdrive_extract_prompt,
                    "description": "Prompt for client document extraction",
                    "category": "extraction"
                }
            }
            
            created_count = 0
            existing_count = 0
            error_count = 0
            
            for prompt_name, prompt_data in default_prompts.items():
                result = self._create_prompt_if_not_exists(
                    prompt_name=prompt_name,
                    content=prompt_data["content"],
                    description=prompt_data["description"],
                    category=prompt_data["category"]
                )
                
                if result == "created":
                    created_count += 1
                elif result == "exists":
                    existing_count += 1
                elif result == "error":
                    error_count += 1
            
            # Summary message
            if created_count > 0:
                print(f"✅ Initialized {created_count} new prompts")
            if existing_count > 0:
                print(f"✅ Found {existing_count} existing prompts")
            if error_count > 0:
                print(f"⚠️  {error_count} prompts had errors (using fallback)")
            print(f"✅ Total prompts available: {len(default_prompts)}")
                
        except Exception as e:
            print(f"⚠️  Could not load default prompts: {e}")
    
    def _create_prompt_if_not_exists(self, prompt_name: str, content: str, 
                                   description: str, category: str) -> str:
        """Create a prompt template and version if it doesn't exist"""
        if not self.db_pool:
            return "no_db"
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                # Check if prompt template exists (handle RealDictRow format)
                cursor.execute(
                    "SELECT COUNT(*) as count FROM prompt_templates WHERE prompt_name = %s",
                    (prompt_name,)
                )
                result = cursor.fetchone()
                template_exists = result['count'] > 0 if result else False
                
                # Check if active version exists
                cursor.execute(
                    "SELECT COUNT(*) as count FROM prompt_versions WHERE prompt_name = %s AND is_active = TRUE",
                    (prompt_name,)
                )
                version_result = cursor.fetchone()
                active_version_exists = version_result['count'] > 0 if version_result else False
                
                if template_exists and active_version_exists:
                    return "exists"  # Already complete
                
                # Create prompt template if missing
                if not template_exists:
                    template_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO prompt_templates (id, prompt_name, description, category)
                        VALUES (%s, %s, %s, %s)
                    """, (template_id, prompt_name, description, category))
                
                # Create active version if missing
                if not active_version_exists:
                    # Deactivate any existing versions first
                    cursor.execute(
                        "UPDATE prompt_versions SET is_active = FALSE WHERE prompt_name = %s",
                        (prompt_name,)
                    )
                    
                    # Create new active version
                    version_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO prompt_versions 
                        (id, prompt_name, version, content, description, created_by, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (version_id, prompt_name, 1, content, "Initial version", "system", True))
                
                conn.commit()
            self.db_pool.putconn(conn)
            return "created"
            
        except Exception as e:
            if "already exists" in str(e) or "duplicate key" in str(e):
                return "exists"
            else:
                # Log the actual error for debugging in production
                print(f"⚠️  Error creating prompt '{prompt_name}': {e}")
                return "error"
    
    def get_active_prompt(self, prompt_name: str) -> Optional[str]:
        """Get the active version of a prompt"""
        if not self.db_pool:
            # Fallback to prompts.py if database unavailable
            return self._get_fallback_prompt(prompt_name)
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT content, id FROM prompt_versions 
                    WHERE prompt_name = %s AND is_active = TRUE
                    ORDER BY version DESC LIMIT 1
                """, (prompt_name,))
                
                result = cursor.fetchone()
                if result:
                    # Handle RealDictRow format
                    if hasattr(result, 'items'):  # RealDictRow
                        content = result['content']
                        version_id = result['id']
                    else:  # Regular tuple
                        content = result[0]
                        version_id = result[1]
                    
                    # Track usage if we have a valid version ID
                    if version_id and content:
                        self._track_prompt_usage(prompt_name, version_id)
                        print(f"✅ Retrieved prompt {prompt_name} from database (length: {len(content)})")
                        return content
                
            self.db_pool.putconn(conn)
            
        except Exception as e:
            print(f"Error getting prompt {prompt_name}: {e}")
        
        # Fallback to original prompts.py
        return self._get_fallback_prompt(prompt_name)
    
    def _get_fallback_prompt(self, prompt_name: str) -> Optional[str]:
        """Fallback to original prompts.py if database unavailable"""
        try:
            from src import prompts
            prompt_content = getattr(prompts, prompt_name, None)
            if prompt_content:
                print(f"✅ Using fallback prompt for {prompt_name}")
                return prompt_content
            else:
                print(f"⚠️  Prompt {prompt_name} not found in prompts.py")
                return None
        except Exception as e:
            print(f"❌ Error importing prompts.py: {e}")
            return None
    
    def _track_prompt_usage(self, prompt_name: str, version_id: str, 
                          node_name: str = "unknown", execution_time_ms: int = None,
                          success: bool = True, quality_score: float = None):
        """Track prompt usage for analytics"""
        if not self.db_pool or not hasattr(metrics, 'current_session'):
            return
        
        try:
            session_id = metrics.current_session.session_id if metrics.current_session else None
            if not session_id:
                return
            
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO prompt_usage 
                    (session_id, prompt_name, prompt_version_id, node_name, 
                     execution_time_ms, success, output_quality_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (session_id, prompt_name, version_id, node_name, 
                      execution_time_ms, success, quality_score))
                
                # Update usage count
                cursor.execute("""
                    UPDATE prompt_versions 
                    SET usage_count = usage_count + 1 
                    WHERE id = %s
                """, (version_id,))
                
                conn.commit()
            self.db_pool.putconn(conn)
            
        except Exception as e:
            print(f"Error tracking prompt usage: {e}")
    
    def create_prompt_version(self, prompt_name: str, content: str, 
                            description: str, created_by: str) -> str:
        """Create a new version of a prompt"""
        if not self.db_pool:
            raise Exception("Database not available")
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                # Get next version number
                cursor.execute("""
                    SELECT COALESCE(MAX(version), 0) + 1 
                    FROM prompt_versions WHERE prompt_name = %s
                """, (prompt_name,))
                next_version = cursor.fetchone()[0]
                
                # Create new version
                version_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO prompt_versions 
                    (id, prompt_name, version, content, description, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (version_id, prompt_name, next_version, content, description, created_by))
                
                conn.commit()
            self.db_pool.putconn(conn)
            
            return version_id
            
        except Exception as e:
            raise Exception(f"Error creating prompt version: {e}")
    
    def activate_prompt_version(self, prompt_name: str, version_id: str) -> bool:
        """Activate a specific version of a prompt"""
        if not self.db_pool:
            return False
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                # Deactivate all versions of this prompt
                cursor.execute("""
                    UPDATE prompt_versions 
                    SET is_active = FALSE 
                    WHERE prompt_name = %s
                """, (prompt_name,))
                
                # Activate the specified version
                cursor.execute("""
                    UPDATE prompt_versions 
                    SET is_active = TRUE 
                    WHERE id = %s AND prompt_name = %s
                """, (version_id, prompt_name))
                
                conn.commit()
            self.db_pool.putconn(conn)
            
            return True
            
        except Exception as e:
            print(f"Error activating prompt version: {e}")
            return False
    
    def get_prompt_versions(self, prompt_name: str) -> List[Dict[str, Any]]:
        """Get all versions of a prompt"""
        if not self.db_pool:
            return []
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, version, description, created_at, created_by, 
                           is_active, performance_score, usage_count
                    FROM prompt_versions 
                    WHERE prompt_name = %s 
                    ORDER BY version DESC
                """, (prompt_name,))
                
                versions = []
                for row in cursor.fetchall():
                    versions.append({
                        "id": row["id"],
                        "version": row["version"],
                        "description": row["description"],
                        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                        "created_by": row["created_by"],
                        "is_active": row["is_active"],
                        "performance_score": float(row["performance_score"]) if row["performance_score"] else 0.0,
                        "usage_count": row["usage_count"]
                    })
                
            self.db_pool.putconn(conn)
            return versions
            
        except Exception as e:
            print(f"Error getting prompt versions: {e}")
            return []
    
    def get_all_prompts(self) -> List[Dict[str, Any]]:
        """Get all prompt templates with their active versions"""
        if not self.db_pool:
            return []
        
        try:
            conn = self.db_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT pt.prompt_name, pt.description, pt.category,
                           pv.id as active_version_id, pv.version as active_version,
                           pv.performance_score, pv.usage_count
                    FROM prompt_templates pt
                    LEFT JOIN prompt_versions pv ON pt.prompt_name = pv.prompt_name 
                        AND pv.is_active = TRUE
                    ORDER BY pt.prompt_name
                """)
                
                prompts = []
                for row in cursor.fetchall():
                    prompts.append({
                        "prompt_name": row["prompt_name"],
                        "description": row["description"],
                        "category": row["category"],
                        "active_version_id": row["active_version_id"],
                        "active_version": row["active_version"],
                        "performance_score": float(row["performance_score"]) if row["performance_score"] else 0.0,
                        "usage_count": row["usage_count"] or 0
                    })
                
            self.db_pool.putconn(conn)
            return prompts
            
        except Exception as e:
            print(f"Error getting all prompts: {e}")
            return []

# Global prompt manager instance
prompt_manager = PromptManager()