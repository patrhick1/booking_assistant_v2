-- =====================================================
-- BookingAssistant Complete Database Schema
-- Includes all tables for analytics, prompts, and interactions
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- CORE EMAIL PROCESSING TABLES
-- =====================================================

-- Email processing sessions
CREATE TABLE IF NOT EXISTS email_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_hash VARCHAR(64) UNIQUE NOT NULL, -- SHA256 of email content for deduplication
    sender_email VARCHAR(255) NOT NULL,
    sender_name VARCHAR(255),
    subject TEXT,
    email_content TEXT,
    classification VARCHAR(100),
    processing_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    total_duration_ms INTEGER,
    status VARCHAR(50) DEFAULT 'processing', -- 'processing', 'completed', 'failed'
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Node execution performance tracking
CREATE TABLE IF NOT EXISTS node_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
);

-- =====================================================
-- CLASSIFICATION AND ANALYSIS TABLES
-- =====================================================

-- Classification results and accuracy tracking
CREATE TABLE IF NOT EXISTS classification_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES email_sessions(id) ON DELETE CASCADE,
    predicted_label VARCHAR(100) NOT NULL,
    confidence_score FLOAT,
    human_verified_label VARCHAR(100), -- For accuracy measurement
    is_correct BOOLEAN, -- Human feedback on classification accuracy
    feedback_timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Document extraction performance
CREATE TABLE IF NOT EXISTS document_extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
);

-- =====================================================
-- DRAFT GENERATION AND QUALITY TABLES
-- =====================================================

-- Draft generation quality metrics
CREATE TABLE IF NOT EXISTS draft_generations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES email_sessions(id) ON DELETE CASCADE,
    draft_content TEXT,
    final_draft_content TEXT,
    draft_length INTEGER,
    final_draft_length INTEGER,
    context_used BOOLEAN DEFAULT FALSE, -- Did it use client document content?
    context_length INTEGER DEFAULT 0,
    vector_threads_used INTEGER DEFAULT 0,
    placeholders_count INTEGER DEFAULT 0,
    template_adherence_score FLOAT, -- 0-1 score for following template guidelines
    auto_quality_score FLOAT, -- Automated quality assessment
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- HUMAN FEEDBACK AND INTERACTIONS TABLES
-- =====================================================

-- Human feedback and quality ratings
CREATE TABLE IF NOT EXISTS quality_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES email_sessions(id) ON DELETE CASCADE,
    human_action VARCHAR(50), -- 'approved', 'edited', 'rejected', 'discarded'
    human_rating INTEGER CHECK (human_rating >= 1 AND human_rating <= 5),
    edit_distance INTEGER DEFAULT 0, -- Character changes made to draft
    edit_type VARCHAR(50), -- 'minor', 'major', 'complete_rewrite'
    approval_timestamp TIMESTAMP WITH TIME ZONE,
    feedback_notes TEXT,
    slack_message_id VARCHAR(100), -- For tracking Slack interactions
    slack_channel_id VARCHAR(100),
    slack_user_id VARCHAR(100), -- Who provided the feedback
    slack_user_name VARCHAR(100),
    gmail_draft_created BOOLEAN DEFAULT FALSE,
    gmail_draft_sent BOOLEAN DEFAULT FALSE,
    final_quality_score FLOAT, -- Composite quality score
    interaction_metadata JSONB, -- Store additional interaction data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Slack interaction logs (for detailed tracking)
CREATE TABLE IF NOT EXISTS slack_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES email_sessions(id) ON DELETE CASCADE,
    interaction_type VARCHAR(50) NOT NULL, -- 'button_click', 'modal_submit', 'message_edit'
    action_value VARCHAR(100), -- e.g., 'approve', 'reject', 'rate_5'
    user_id VARCHAR(100),
    user_name VARCHAR(100),
    channel_id VARCHAR(100),
    message_ts VARCHAR(100), -- Slack message timestamp
    trigger_id VARCHAR(100), -- Slack trigger ID for modals
    response_time_ms INTEGER,
    payload JSONB, -- Full Slack payload for debugging
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- PROMPT MANAGEMENT TABLES
-- =====================================================

-- Prompt Templates Table
CREATE TABLE IF NOT EXISTS prompt_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prompt_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Prompt Versions Table
CREATE TABLE IF NOT EXISTS prompt_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
    session_id UUID REFERENCES email_sessions(id) ON DELETE CASCADE,
    prompt_name VARCHAR(100) NOT NULL,
    prompt_version_id UUID REFERENCES prompt_versions(id) ON DELETE CASCADE,
    node_name VARCHAR(100) NOT NULL,
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    output_quality_score DECIMAL(5,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- A/B Test Configurations Table
CREATE TABLE IF NOT EXISTS ab_test_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_name VARCHAR(100) NOT NULL UNIQUE,
    prompt_name VARCHAR(100) NOT NULL,
    variant_a_version_id UUID REFERENCES prompt_versions(id),
    variant_b_version_id UUID REFERENCES prompt_versions(id),
    traffic_split DECIMAL(3,2) DEFAULT 0.5, -- 0.5 = 50/50 split
    is_active BOOLEAN DEFAULT TRUE,
    start_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- SYSTEM METRICS AND MONITORING TABLES
-- =====================================================

-- System performance metrics
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(50),
    tags JSONB, -- For filtering and grouping
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User authentication and sessions (for dashboard)
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- WORKFLOW STATE TABLES (for complex interactions)
-- =====================================================

-- Email workflow states (for multi-step interactions)
CREATE TABLE IF NOT EXISTS email_workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES email_sessions(id) ON DELETE CASCADE,
    workflow_state VARCHAR(50) DEFAULT 'draft_created', -- 'draft_created', 'pending_review', 'approved', 'edited', 'rejected', 'sent'
    current_step VARCHAR(100),
    next_actions JSONB, -- Available actions for this state
    assigned_to VARCHAR(100), -- User responsible for next action
    deadline TIMESTAMP WITH TIME ZONE,
    metadata JSONB, -- Workflow-specific data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Email sessions indexes
CREATE INDEX IF NOT EXISTS idx_email_sessions_processing_started ON email_sessions(processing_started_at);
CREATE INDEX IF NOT EXISTS idx_email_sessions_status ON email_sessions(status);
CREATE INDEX IF NOT EXISTS idx_email_sessions_classification ON email_sessions(classification);
CREATE INDEX IF NOT EXISTS idx_email_sessions_sender ON email_sessions(sender_email);

-- Node executions indexes
CREATE INDEX IF NOT EXISTS idx_node_executions_session_node ON node_executions(session_id, node_name);
CREATE INDEX IF NOT EXISTS idx_node_executions_duration ON node_executions(duration_ms);
CREATE INDEX IF NOT EXISTS idx_node_executions_success ON node_executions(success);

-- Classification and feedback indexes
CREATE INDEX IF NOT EXISTS idx_classification_results_session ON classification_results(session_id);
CREATE INDEX IF NOT EXISTS idx_document_extractions_session ON document_extractions(session_id);
CREATE INDEX IF NOT EXISTS idx_draft_generations_session ON draft_generations(session_id);
CREATE INDEX IF NOT EXISTS idx_quality_feedback_session ON quality_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_quality_feedback_action ON quality_feedback(human_action);
CREATE INDEX IF NOT EXISTS idx_quality_feedback_rating ON quality_feedback(human_rating);

-- Slack interactions indexes
CREATE INDEX IF NOT EXISTS idx_slack_interactions_session ON slack_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_slack_interactions_type ON slack_interactions(interaction_type);
CREATE INDEX IF NOT EXISTS idx_slack_interactions_user ON slack_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_slack_interactions_timestamp ON slack_interactions(created_at);

-- Prompt management indexes
CREATE INDEX IF NOT EXISTS idx_prompt_versions_name ON prompt_versions(prompt_name);
CREATE INDEX IF NOT EXISTS idx_prompt_versions_active ON prompt_versions(is_active);
CREATE INDEX IF NOT EXISTS idx_prompt_usage_session ON prompt_usage(session_id);
CREATE INDEX IF NOT EXISTS idx_prompt_usage_name ON prompt_usage(prompt_name);
CREATE INDEX IF NOT EXISTS idx_ab_test_active ON ab_test_configs(is_active);

-- Workflow indexes
CREATE INDEX IF NOT EXISTS idx_email_workflows_session ON email_workflows(session_id);
CREATE INDEX IF NOT EXISTS idx_email_workflows_state ON email_workflows(workflow_state);
CREATE INDEX IF NOT EXISTS idx_email_workflows_assigned ON email_workflows(assigned_to);

-- System metrics indexes
CREATE INDEX IF NOT EXISTS idx_system_metrics_name_timestamp ON system_metrics(metric_name, timestamp);

-- =====================================================
-- TRIGGERS AND FUNCTIONS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at columns
CREATE TRIGGER IF NOT EXISTS update_email_sessions_updated_at 
    BEFORE UPDATE ON email_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER IF NOT EXISTS update_quality_feedback_updated_at 
    BEFORE UPDATE ON quality_feedback 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER IF NOT EXISTS update_email_workflows_updated_at 
    BEFORE UPDATE ON email_workflows 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to automatically create workflow entry when session is created
CREATE OR REPLACE FUNCTION create_workflow_on_session()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO email_workflows (session_id, workflow_state, current_step, next_actions)
    VALUES (
        NEW.id, 
        'processing', 
        'email_classification',
        '{"available_actions": ["classify", "reject"]}'::jsonb
    );
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to create workflow when email session starts
CREATE TRIGGER IF NOT EXISTS create_workflow_trigger
    AFTER INSERT ON email_sessions
    FOR EACH ROW EXECUTE FUNCTION create_workflow_on_session();

-- Function to update workflow state when feedback is received
CREATE OR REPLACE FUNCTION update_workflow_on_feedback()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE email_workflows 
    SET 
        workflow_state = CASE 
            WHEN NEW.human_action = 'approved' THEN 'approved'
            WHEN NEW.human_action = 'edited' THEN 'edited'
            WHEN NEW.human_action = 'rejected' THEN 'rejected'
            ELSE workflow_state
        END,
        current_step = CASE 
            WHEN NEW.human_action = 'approved' THEN 'ready_to_send'
            WHEN NEW.human_action = 'edited' THEN 'pending_revision'
            WHEN NEW.human_action = 'rejected' THEN 'rejected'
            ELSE current_step
        END,
        updated_at = NOW()
    WHERE session_id = NEW.session_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to update workflow when feedback is provided
CREATE TRIGGER IF NOT EXISTS update_workflow_on_feedback_trigger
    AFTER INSERT ON quality_feedback
    FOR EACH ROW EXECUTE FUNCTION update_workflow_on_feedback();

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Session summary view
CREATE OR REPLACE VIEW session_summary AS
SELECT 
    es.id,
    es.sender_email,
    es.sender_name,
    es.subject,
    es.classification,
    es.status,
    es.processing_started_at,
    es.processing_completed_at,
    es.total_duration_ms,
    ew.workflow_state,
    ew.current_step,
    qf.human_action,
    qf.human_rating,
    de.client_matched,
    de.client_name,
    dg.template_adherence_score,
    dg.auto_quality_score
FROM email_sessions es
LEFT JOIN email_workflows ew ON es.id = ew.session_id
LEFT JOIN quality_feedback qf ON es.id = qf.session_id
LEFT JOIN document_extractions de ON es.id = de.session_id
LEFT JOIN draft_generations dg ON es.id = dg.session_id;

-- Active prompts view
CREATE OR REPLACE VIEW active_prompts AS
SELECT 
    pt.prompt_name,
    pt.description,
    pt.category,
    pv.id as version_id,
    pv.version,
    pv.content,
    pv.performance_score,
    pv.usage_count,
    pv.created_at,
    pv.created_by
FROM prompt_templates pt
JOIN prompt_versions pv ON pt.prompt_name = pv.prompt_name
WHERE pv.is_active = TRUE
ORDER BY pt.prompt_name;

-- Feedback analytics view
CREATE OR REPLACE VIEW feedback_analytics AS
SELECT 
    DATE_TRUNC('day', qf.created_at) as feedback_date,
    COUNT(*) as total_feedback,
    AVG(qf.human_rating) as avg_rating,
    COUNT(CASE WHEN qf.human_action = 'approved' THEN 1 END) as approved_count,
    COUNT(CASE WHEN qf.human_action = 'edited' THEN 1 END) as edited_count,
    COUNT(CASE WHEN qf.human_action = 'rejected' THEN 1 END) as rejected_count,
    AVG(qf.final_quality_score) as avg_quality_score
FROM quality_feedback qf
GROUP BY DATE_TRUNC('day', qf.created_at)
ORDER BY feedback_date DESC;