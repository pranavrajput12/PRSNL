-- Migration: Add missing tables that are referenced in code
-- This is SAFE - only adds new tables, doesn't modify existing ones

-- 1. Attachments table (referenced in code but missing)
CREATE TABLE IF NOT EXISTS attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_type VARCHAR(100),
    file_size BIGINT,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Indexes for attachments
CREATE INDEX IF NOT EXISTS idx_attachments_item_id ON attachments(item_id);
CREATE INDEX IF NOT EXISTS idx_attachments_file_type ON attachments(file_type);

-- 2. Jobs table for background processing
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    payload JSONB DEFAULT '{}',
    result JSONB DEFAULT '{}',
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    scheduled_for TIMESTAMPTZ
);

-- Indexes for jobs
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(type);
CREATE INDEX IF NOT EXISTS idx_jobs_item_id ON jobs(item_id);
CREATE INDEX IF NOT EXISTS idx_jobs_scheduled ON jobs(scheduled_for) WHERE status = 'pending';

-- 3. User sessions table (for future auth)
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID, -- Will reference users table when created
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    last_activity TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for sessions
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);

-- 4. API keys table (for API access)
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    permissions JSONB DEFAULT '{}',
    rate_limit INTEGER DEFAULT 1000,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true
);

-- Indexes for API keys
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);

-- 5. Audit log table (for security)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    request_id UUID,
    details JSONB DEFAULT '{}',
    status VARCHAR(20)
);

-- Indexes for audit logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- Add comment to track migration
COMMENT ON TABLE attachments IS 'Added in migration 007 - fixes missing table error';
COMMENT ON TABLE jobs IS 'Added in migration 007 - enables background job tracking';
COMMENT ON TABLE user_sessions IS 'Added in migration 007 - preparation for auth system';
COMMENT ON TABLE api_keys IS 'Added in migration 007 - API access management';
COMMENT ON TABLE audit_logs IS 'Added in migration 007 - security audit trail';