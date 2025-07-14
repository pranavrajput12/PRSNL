-- Phase 2: Agent Monitoring and Performance Tracking Migration
-- Date: 2025-07-14
-- Purpose: Add tables for real-time agent monitoring and performance tracking

-- Agent Performance Metrics table
CREATE TABLE IF NOT EXISTS agent_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id TEXT UNIQUE NOT NULL,
    agent_type TEXT NOT NULL,
    status TEXT NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    success_rate FLOAT,
    error_count INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    memory_usage_mb FLOAT,
    cpu_usage_percent FLOAT,
    queue_name TEXT DEFAULT 'default',
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Workflow Performance Metrics table
CREATE TABLE IF NOT EXISTS workflow_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id TEXT UNIQUE NOT NULL,
    workflow_type TEXT NOT NULL,
    total_agents INTEGER NOT NULL,
    completed_agents INTEGER DEFAULT 0,
    failed_agents INTEGER DEFAULT 0,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    overall_success_rate FLOAT DEFAULT 0.0,
    total_duration_ms INTEGER,
    bottleneck_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agent Synthesis Results table (for coordination tracking)
CREATE TABLE IF NOT EXISTS agent_synthesis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    synthesis_type TEXT NOT NULL,
    agent_results JSONB NOT NULL DEFAULT '{}',
    synthesis_output JSONB NOT NULL DEFAULT '{}',
    successful_agents_count INTEGER DEFAULT 0,
    failed_agents TEXT[] DEFAULT '{}',
    overall_confidence FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agent Workflows table (for workflow tracking)
CREATE TABLE IF NOT EXISTS agent_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    workflow_name TEXT NOT NULL,
    workflow_type TEXT NOT NULL,
    workflow_config JSONB NOT NULL DEFAULT '{}',
    status TEXT DEFAULT 'created',
    execution_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance Alerts table
CREATE TABLE IF NOT EXISTS performance_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type TEXT NOT NULL,
    agent_type TEXT,
    task_id TEXT,
    workflow_id TEXT,
    alert_data JSONB NOT NULL DEFAULT '{}',
    severity TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance optimization

-- Agent Performance Metrics indexes
CREATE INDEX IF NOT EXISTS idx_agent_performance_metrics_task_id ON agent_performance_metrics(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_performance_metrics_agent_type ON agent_performance_metrics(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_performance_metrics_status ON agent_performance_metrics(status);
CREATE INDEX IF NOT EXISTS idx_agent_performance_metrics_start_time ON agent_performance_metrics(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_agent_performance_metrics_duration ON agent_performance_metrics(duration_ms DESC);
CREATE INDEX IF NOT EXISTS idx_agent_performance_metrics_success_rate ON agent_performance_metrics(success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_agent_performance_metrics_queue ON agent_performance_metrics(queue_name);

-- Workflow Performance Metrics indexes
CREATE INDEX IF NOT EXISTS idx_workflow_performance_metrics_workflow_id ON workflow_performance_metrics(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_performance_metrics_type ON workflow_performance_metrics(workflow_type);
CREATE INDEX IF NOT EXISTS idx_workflow_performance_metrics_start_time ON workflow_performance_metrics(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_performance_metrics_success_rate ON workflow_performance_metrics(overall_success_rate DESC);

-- Agent Synthesis Results indexes
CREATE INDEX IF NOT EXISTS idx_agent_synthesis_results_user_id ON agent_synthesis_results(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_synthesis_results_type ON agent_synthesis_results(synthesis_type);
CREATE INDEX IF NOT EXISTS idx_agent_synthesis_results_created_at ON agent_synthesis_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_synthesis_results_confidence ON agent_synthesis_results(overall_confidence DESC);

-- Agent Workflows indexes
CREATE INDEX IF NOT EXISTS idx_agent_workflows_user_id ON agent_workflows(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_workflows_type ON agent_workflows(workflow_type);
CREATE INDEX IF NOT EXISTS idx_agent_workflows_status ON agent_workflows(status);
CREATE INDEX IF NOT EXISTS idx_agent_workflows_created_at ON agent_workflows(created_at DESC);

-- Performance Alerts indexes
CREATE INDEX IF NOT EXISTS idx_performance_alerts_type ON performance_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_agent_type ON performance_alerts(agent_type);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_status ON performance_alerts(status);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_severity ON performance_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_created_at ON performance_alerts(created_at DESC);

-- Views for monitoring and reporting

-- Agent Performance Summary View
CREATE OR REPLACE VIEW agent_performance_summary AS
SELECT 
    agent_type,
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks,
    ROUND(AVG(duration_ms), 2) as avg_duration_ms,
    ROUND(AVG(success_rate), 3) as avg_success_rate,
    ROUND(AVG(retry_count), 2) as avg_retry_count,
    MAX(duration_ms) as max_duration_ms,
    MIN(duration_ms) as min_duration_ms,
    COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as tasks_last_24h
FROM agent_performance_metrics
GROUP BY agent_type
ORDER BY total_tasks DESC;

-- Workflow Performance Summary View
CREATE OR REPLACE VIEW workflow_performance_summary AS
SELECT 
    workflow_type,
    COUNT(*) as total_workflows,
    COUNT(CASE WHEN overall_success_rate >= 0.8 THEN 1 END) as successful_workflows,
    ROUND(AVG(overall_success_rate), 3) as avg_success_rate,
    ROUND(AVG(total_duration_ms), 2) as avg_duration_ms,
    ROUND(AVG(total_agents), 2) as avg_agents_per_workflow,
    MAX(total_duration_ms) as max_duration_ms,
    COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as workflows_last_24h
FROM workflow_performance_metrics
GROUP BY workflow_type
ORDER BY total_workflows DESC;

-- Real-time Active Tasks View
CREATE OR REPLACE VIEW active_tasks_view AS
SELECT 
    apm.task_id,
    apm.agent_type,
    apm.status,
    apm.start_time,
    apm.queue_name,
    apm.priority,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - apm.start_time)) * 1000 as current_duration_ms,
    tp.current_value as progress,
    tp.total_value as total_progress,
    tp.message as current_message
FROM agent_performance_metrics apm
LEFT JOIN task_progress tp ON apm.task_id = tp.task_id
WHERE apm.end_time IS NULL
ORDER BY apm.start_time ASC;

-- Performance Alerts Summary View
CREATE OR REPLACE VIEW performance_alerts_summary AS
SELECT 
    alert_type,
    COUNT(*) as total_alerts,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_alerts,
    COUNT(CASE WHEN severity = 'high' THEN 1 END) as high_severity,
    COUNT(CASE WHEN severity = 'medium' THEN 1 END) as medium_severity,
    COUNT(CASE WHEN severity = 'low' THEN 1 END) as low_severity,
    COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as alerts_last_24h
FROM performance_alerts
GROUP BY alert_type
ORDER BY total_alerts DESC;

-- Functions for monitoring and analysis

-- Function to get agent performance trends
CREATE OR REPLACE FUNCTION get_agent_performance_trends(
    agent_type_param TEXT DEFAULT NULL,
    hours_back INTEGER DEFAULT 24
)
RETURNS TABLE (
    hour_bucket TIMESTAMP,
    agent_type TEXT,
    total_tasks BIGINT,
    success_rate NUMERIC,
    avg_duration_ms NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        date_trunc('hour', apm.created_at) as hour_bucket,
        apm.agent_type,
        COUNT(*) as total_tasks,
        ROUND(AVG(apm.success_rate), 3) as success_rate,
        ROUND(AVG(apm.duration_ms), 2) as avg_duration_ms
    FROM agent_performance_metrics apm
    WHERE apm.created_at >= CURRENT_TIMESTAMP - (hours_back || ' hours')::INTERVAL
        AND (agent_type_param IS NULL OR apm.agent_type = agent_type_param)
        AND apm.end_time IS NOT NULL
    GROUP BY date_trunc('hour', apm.created_at), apm.agent_type
    ORDER BY hour_bucket DESC, apm.agent_type;
END;
$$ LANGUAGE plpgsql;

-- Function to detect performance anomalies
CREATE OR REPLACE FUNCTION detect_performance_anomalies(
    threshold_duration_ms INTEGER DEFAULT 300000,
    threshold_success_rate FLOAT DEFAULT 0.8
)
RETURNS TABLE (
    agent_type TEXT,
    issue_type TEXT,
    current_value NUMERIC,
    threshold_value NUMERIC,
    task_count BIGINT
) AS $$
BEGIN
    -- Long duration anomalies
    RETURN QUERY
    SELECT 
        apm.agent_type,
        'long_duration'::TEXT as issue_type,
        ROUND(AVG(apm.duration_ms), 2) as current_value,
        threshold_duration_ms::NUMERIC as threshold_value,
        COUNT(*) as task_count
    FROM agent_performance_metrics apm
    WHERE apm.created_at >= CURRENT_TIMESTAMP - INTERVAL '6 hours'
        AND apm.duration_ms > threshold_duration_ms
    GROUP BY apm.agent_type
    HAVING COUNT(*) >= 3;

    -- Low success rate anomalies
    RETURN QUERY
    SELECT 
        apm.agent_type,
        'low_success_rate'::TEXT as issue_type,
        ROUND(AVG(apm.success_rate), 3) as current_value,
        threshold_success_rate::NUMERIC as threshold_value,
        COUNT(*) as task_count
    FROM agent_performance_metrics apm
    WHERE apm.created_at >= CURRENT_TIMESTAMP - INTERVAL '6 hours'
        AND apm.end_time IS NOT NULL
    GROUP BY apm.agent_type
    HAVING AVG(apm.success_rate) < threshold_success_rate
        AND COUNT(*) >= 5;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old performance data
CREATE OR REPLACE FUNCTION cleanup_old_performance_data(retention_days INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Clean up old agent performance metrics
    DELETE FROM agent_performance_metrics 
    WHERE created_at < CURRENT_TIMESTAMP - (retention_days || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up old workflow metrics
    DELETE FROM workflow_performance_metrics 
    WHERE created_at < CURRENT_TIMESTAMP - (retention_days || ' days')::INTERVAL;
    
    -- Clean up resolved alerts older than retention period
    DELETE FROM performance_alerts 
    WHERE status = 'resolved' 
        AND resolved_at < CURRENT_TIMESTAMP - (retention_days || ' days')::INTERVAL;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Triggers for maintaining updated_at timestamps

-- Workflow Performance Metrics trigger
CREATE OR REPLACE FUNCTION update_workflow_performance_metrics_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_workflow_performance_metrics_updated_at
    BEFORE UPDATE ON workflow_performance_metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_workflow_performance_metrics_updated_at();

-- Agent Workflows trigger
CREATE OR REPLACE FUNCTION update_agent_workflows_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_agent_workflows_updated_at
    BEFORE UPDATE ON agent_workflows
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_workflows_updated_at();

-- Comments for documentation
COMMENT ON TABLE agent_performance_metrics IS 'Real-time performance metrics for individual agent tasks';
COMMENT ON TABLE workflow_performance_metrics IS 'Performance metrics for multi-agent workflows and coordination';
COMMENT ON TABLE agent_synthesis_results IS 'Results from intelligent agent synthesis and coordination';
COMMENT ON TABLE agent_workflows IS 'Workflow definitions and execution tracking';
COMMENT ON TABLE performance_alerts IS 'Performance alerts and monitoring notifications';

COMMENT ON VIEW agent_performance_summary IS 'Aggregated performance summary by agent type';
COMMENT ON VIEW workflow_performance_summary IS 'Aggregated performance summary by workflow type';
COMMENT ON VIEW active_tasks_view IS 'Real-time view of currently active agent tasks';
COMMENT ON VIEW performance_alerts_summary IS 'Summary of performance alerts by type and severity';

COMMENT ON FUNCTION get_agent_performance_trends IS 'Get hourly performance trends for agents';
COMMENT ON FUNCTION detect_performance_anomalies IS 'Detect performance anomalies based on thresholds';
COMMENT ON FUNCTION cleanup_old_performance_data IS 'Clean up old performance data beyond retention period';

-- Grant necessary permissions (adjust based on your user setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_app_user;