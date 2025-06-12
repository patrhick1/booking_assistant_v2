-- =====================================================
-- SLACK INTERACTION QUERIES
-- Handles all CRUD operations for Slack bot interactions
-- =====================================================

-- =====================================================
-- CREATE OPERATIONS
-- =====================================================

-- Record a new Slack interaction
INSERT INTO slack_interactions (
    session_id,
    interaction_type,
    action_value,
    user_id,
    user_name,
    channel_id,
    message_ts,
    trigger_id,
    response_time_ms,
    payload
) VALUES (
    $1, -- session_id
    $2, -- interaction_type ('button_click', 'modal_submit', etc.)
    $3, -- action_value ('approve', 'reject', 'rate_5', etc.)
    $4, -- user_id
    $5, -- user_name
    $6, -- channel_id
    $7, -- message_ts
    $8, -- trigger_id
    $9, -- response_time_ms
    $10 -- payload (JSONB)
);

-- Record quality feedback from Slack interaction
INSERT INTO quality_feedback (
    session_id,
    human_action,
    human_rating,
    slack_message_id,
    slack_channel_id,
    slack_user_id,
    slack_user_name,
    approval_timestamp,
    feedback_notes,
    interaction_metadata
) VALUES (
    $1, -- session_id
    $2, -- human_action ('approved', 'edited', 'rejected')
    $3, -- human_rating (1-5)
    $4, -- slack_message_id
    $5, -- slack_channel_id
    $6, -- slack_user_id
    $7, -- slack_user_name
    NOW(), -- approval_timestamp
    $8, -- feedback_notes
    $9  -- interaction_metadata (JSONB)
);

-- Update draft content when edited via Slack
UPDATE draft_generations 
SET 
    final_draft_content = $2,
    final_draft_length = LENGTH($2),
    updated_at = NOW()
WHERE session_id = $1;

-- =====================================================
-- READ OPERATIONS
-- =====================================================

-- Get session data for Slack interaction
SELECT 
    es.id,
    es.sender_email,
    es.sender_name,
    es.subject,
    es.classification,
    dg.draft_content,
    dg.final_draft_content,
    ew.workflow_state,
    ew.current_step
FROM email_sessions es
LEFT JOIN draft_generations dg ON es.id = dg.session_id
LEFT JOIN email_workflows ew ON es.id = ew.session_id
WHERE es.id = $1;

-- Get existing feedback for a session
SELECT 
    human_action,
    human_rating,
    slack_user_name,
    feedback_notes,
    created_at
FROM quality_feedback 
WHERE session_id = $1
ORDER BY created_at DESC;

-- Get all Slack interactions for a session
SELECT 
    interaction_type,
    action_value,
    user_name,
    created_at,
    payload
FROM slack_interactions 
WHERE session_id = $1
ORDER BY created_at ASC;

-- Get pending sessions awaiting Slack feedback
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
AND qf.id IS NULL -- No feedback yet
ORDER BY es.processing_completed_at ASC;

-- =====================================================
-- UPDATE OPERATIONS
-- =====================================================

-- Update workflow state after Slack interaction
UPDATE email_workflows 
SET 
    workflow_state = $2,
    current_step = $3,
    next_actions = $4,
    updated_at = NOW()
WHERE session_id = $1;

-- Update email session status after human action
UPDATE email_sessions 
SET 
    status = CASE 
        WHEN $2 = 'approved' THEN 'approved'
        WHEN $2 = 'rejected' THEN 'rejected'
        WHEN $2 = 'edited' THEN 'edited'
        ELSE status
    END,
    updated_at = NOW()
WHERE id = $1;

-- Mark Gmail draft as created
UPDATE quality_feedback 
SET 
    gmail_draft_created = TRUE,
    updated_at = NOW()
WHERE session_id = $1;

-- Mark Gmail draft as sent
UPDATE quality_feedback 
SET 
    gmail_draft_sent = TRUE,
    updated_at = NOW()
WHERE session_id = $1;

-- =====================================================
-- ANALYTICS QUERIES
-- =====================================================

-- Get Slack interaction statistics
SELECT 
    interaction_type,
    action_value,
    COUNT(*) as interaction_count,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(response_time_ms) as avg_response_time
FROM slack_interactions 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY interaction_type, action_value
ORDER BY interaction_count DESC;

-- Get user engagement metrics
SELECT 
    user_name,
    COUNT(*) as total_interactions,
    COUNT(DISTINCT session_id) as sessions_reviewed,
    AVG(CASE WHEN interaction_type = 'button_click' THEN response_time_ms END) as avg_response_time,
    COUNT(CASE WHEN action_value LIKE 'rate_%' THEN 1 END) as ratings_given,
    COUNT(CASE WHEN action_value = 'approve' THEN 1 END) as approvals,
    COUNT(CASE WHEN action_value = 'reject' THEN 1 END) as rejections
FROM slack_interactions 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY user_name
ORDER BY total_interactions DESC;

-- Get approval rates by classification
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
WHERE es.processing_completed_at >= NOW() - INTERVAL '30 days'
GROUP BY es.classification
ORDER BY approval_rate DESC;

-- Get quality ratings distribution
SELECT 
    human_rating,
    COUNT(*) as rating_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM quality_feedback 
WHERE human_rating IS NOT NULL
AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY human_rating
ORDER BY human_rating;

-- =====================================================
-- WORKFLOW MANAGEMENT QUERIES
-- =====================================================

-- Get sessions by workflow state
SELECT 
    ew.workflow_state,
    COUNT(*) as session_count,
    AVG(EXTRACT(EPOCH FROM (NOW() - es.processing_completed_at)) / 3600) as avg_hours_in_state
FROM email_workflows ew
JOIN email_sessions es ON ew.session_id = es.id
WHERE es.processing_completed_at >= NOW() - INTERVAL '7 days'
GROUP BY ew.workflow_state
ORDER BY session_count DESC;

-- Get overdue sessions (pending review for too long)
SELECT 
    es.id,
    es.sender_email,
    es.subject,
    es.processing_completed_at,
    EXTRACT(EPOCH FROM (NOW() - es.processing_completed_at)) / 3600 as hours_pending
FROM email_sessions es
JOIN email_workflows ew ON es.id = ew.session_id
WHERE ew.workflow_state = 'pending_review'
AND es.processing_completed_at < NOW() - INTERVAL '24 hours'
ORDER BY es.processing_completed_at ASC;

-- =====================================================
-- CLEANUP OPERATIONS
-- =====================================================

-- Delete old Slack interaction data (older than 90 days)
DELETE FROM slack_interactions 
WHERE created_at < NOW() - INTERVAL '90 days';

-- Archive completed sessions older than 6 months
-- (You might want to move to archive table instead of delete)
UPDATE email_sessions 
SET status = 'archived'
WHERE processing_completed_at < NOW() - INTERVAL '6 months'
AND status IN ('completed', 'approved', 'rejected');