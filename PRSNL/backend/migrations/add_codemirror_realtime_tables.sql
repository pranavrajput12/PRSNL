-- CodeMirror Real-time Sync Tables
-- Enterprise-grade event sourcing and connection tracking

-- Table for tracking sync events (event sourcing pattern)
CREATE TABLE IF NOT EXISTS codemirror_sync_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL UNIQUE,
    event_type VARCHAR(50) NOT NULL,
    source VARCHAR(20) NOT NULL, -- cli, web, system
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    repo_id UUID REFERENCES github_repos(id) ON DELETE CASCADE,
    analysis_id UUID REFERENCES codemirror_analyses(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    data JSONB NOT NULL,
    checksum VARCHAR(16), -- For data integrity verification
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX idx_sync_events_user_id ON codemirror_sync_events(user_id);
CREATE INDEX idx_sync_events_analysis_id ON codemirror_sync_events(analysis_id);
CREATE INDEX idx_sync_events_timestamp ON codemirror_sync_events(timestamp DESC);
CREATE INDEX idx_sync_events_event_type ON codemirror_sync_events(event_type);

-- Table for tracking CLI connections
CREATE TABLE IF NOT EXISTS codemirror_cli_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    machine_id VARCHAR(255),
    api_key_name VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    connected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    disconnected_at TIMESTAMPTZ,
    last_heartbeat TIMESTAMPTZ DEFAULT NOW(),
    connection_metadata JSONB DEFAULT '{}'::jsonb
);

-- Index for active connections
CREATE INDEX idx_cli_connections_active ON codemirror_cli_connections(user_id, disconnected_at);
CREATE INDEX idx_cli_connections_machine ON codemirror_cli_connections(machine_id);

-- Table for real-time analysis state (for recovery/resume)
CREATE TABLE IF NOT EXISTS codemirror_realtime_state (
    analysis_id UUID PRIMARY KEY REFERENCES codemirror_analyses(id) ON DELETE CASCADE,
    current_progress INT DEFAULT 0,
    current_stage VARCHAR(50),
    last_update TIMESTAMPTZ DEFAULT NOW(),
    state_data JSONB DEFAULT '{}'::jsonb,
    insights_detected INT DEFAULT 0,
    patterns_detected INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true
);

-- Function to clean up old sync events (keep 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_sync_events()
RETURNS void AS $$
BEGIN
    DELETE FROM codemirror_sync_events 
    WHERE created_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- Function to track CLI heartbeats
CREATE OR REPLACE FUNCTION update_cli_heartbeat(
    p_user_id UUID,
    p_machine_id VARCHAR(255)
)
RETURNS void AS $$
BEGIN
    UPDATE codemirror_cli_connections
    SET last_heartbeat = NOW()
    WHERE user_id = p_user_id 
    AND machine_id = p_machine_id
    AND disconnected_at IS NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update realtime state on analysis updates
CREATE OR REPLACE FUNCTION update_realtime_state()
RETURNS TRIGGER AS $$
BEGIN
    -- Update or create realtime state record
    INSERT INTO codemirror_realtime_state (
        analysis_id,
        current_progress,
        current_stage,
        last_update,
        state_data
    ) VALUES (
        NEW.id,
        COALESCE((NEW.results->>'progress')::int, 0),
        COALESCE(NEW.results->>'stage', 'initializing'),
        NOW(),
        COALESCE(NEW.results->'state', '{}'::jsonb)
    )
    ON CONFLICT (analysis_id) DO UPDATE SET
        current_progress = EXCLUDED.current_progress,
        current_stage = EXCLUDED.current_stage,
        last_update = EXCLUDED.last_update,
        state_data = EXCLUDED.state_data;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_realtime_state
AFTER INSERT OR UPDATE ON codemirror_analyses
FOR EACH ROW
EXECUTE FUNCTION update_realtime_state();

-- View for active analyses with real-time state
CREATE OR REPLACE VIEW codemirror_active_analyses AS
SELECT 
    ca.id,
    ca.repo_id,
    ca.analysis_type,
    ca.analysis_depth,
    ca.created_at,
    rs.current_progress,
    rs.current_stage,
    rs.last_update,
    rs.insights_detected,
    rs.patterns_detected,
    pj.status as job_status,
    gr.full_name as repository_name,
    ga.user_id
FROM codemirror_analyses ca
JOIN codemirror_realtime_state rs ON ca.id = rs.analysis_id
LEFT JOIN processing_jobs pj ON ca.job_id = pj.job_id
LEFT JOIN github_repos gr ON ca.repo_id = gr.id
LEFT JOIN github_accounts ga ON gr.account_id = ga.id
WHERE rs.is_active = true
AND (pj.status IN ('pending', 'processing') OR pj.status IS NULL);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON codemirror_sync_events TO authenticated;
GRANT SELECT, INSERT, UPDATE ON codemirror_cli_connections TO authenticated;
GRANT SELECT, INSERT, UPDATE ON codemirror_realtime_state TO authenticated;
GRANT SELECT ON codemirror_active_analyses TO authenticated;