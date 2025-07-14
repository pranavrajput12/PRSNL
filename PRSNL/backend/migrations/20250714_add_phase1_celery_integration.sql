-- Migration: Add Phase 1 Celery Integration Support
-- Date: 2025-07-14
-- Description: Database schema updates for Phase 1 Celery background processing integration

-- Table for tracking task progress across all Celery workers
CREATE TABLE IF NOT EXISTS task_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(255) NOT NULL,
    entity_id VARCHAR(255) NOT NULL, -- content_id, file_id, video_id, etc.
    progress_type VARCHAR(100) NOT NULL, -- ai_analysis, file_processing, transcription, etc.
    current_value INTEGER NOT NULL DEFAULT 0,
    total_value INTEGER,
    message TEXT,
    status VARCHAR(50) DEFAULT 'in_progress', -- in_progress, completed, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(task_id)
);

-- Indexes for performance
CREATE INDEX idx_task_progress_task_id ON task_progress(task_id);
CREATE INDEX idx_task_progress_entity_id ON task_progress(entity_id);
CREATE INDEX idx_task_progress_type ON task_progress(progress_type);
CREATE INDEX idx_task_progress_status ON task_progress(status);
CREATE INDEX idx_task_progress_updated ON task_progress(updated_at DESC);

-- Table for tracking Celery task results and metadata
CREATE TABLE IF NOT EXISTS celery_task_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(255) NOT NULL UNIQUE,
    task_name VARCHAR(255) NOT NULL,
    queue_name VARCHAR(100),
    worker_name VARCHAR(255),
    status VARCHAR(50) NOT NULL, -- pending, started, success, failure, retry, revoked
    result JSONB,
    error_message TEXT,
    traceback TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    runtime_seconds FLOAT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Celery results
CREATE INDEX idx_celery_results_task_id ON celery_task_results(task_id);
CREATE INDEX idx_celery_results_status ON celery_task_results(status);
CREATE INDEX idx_celery_results_queue ON celery_task_results(queue_name);
CREATE INDEX idx_celery_results_completed ON celery_task_results(completed_at DESC);
CREATE INDEX idx_celery_results_runtime ON celery_task_results(runtime_seconds);

-- Enhanced attachments table for file processing
ALTER TABLE attachments ADD COLUMN IF NOT EXISTS processing_status VARCHAR(50) DEFAULT 'pending';
ALTER TABLE attachments ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;
ALTER TABLE attachments ADD COLUMN IF NOT EXISTS extracted_text TEXT;
ALTER TABLE attachments ADD COLUMN IF NOT EXISTS ai_analysis JSONB;
ALTER TABLE attachments ADD COLUMN IF NOT EXISTS document_type VARCHAR(100);
ALTER TABLE attachments ADD COLUMN IF NOT EXISTS key_insights JSONB;

-- Enhanced items table for AI processing results
ALTER TABLE items ADD COLUMN IF NOT EXISTS last_processed_at TIMESTAMP;
ALTER TABLE items ADD COLUMN IF NOT EXISTS ai_enhancement_status VARCHAR(50) DEFAULT 'pending';
ALTER TABLE items ADD COLUMN IF NOT EXISTS processing_metadata JSONB;

-- View for monitoring task performance
CREATE OR REPLACE VIEW task_performance_overview AS
SELECT 
    ctr.queue_name,
    ctr.task_name,
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN ctr.status = 'success' THEN 1 END) as successful_tasks,
    COUNT(CASE WHEN ctr.status = 'failure' THEN 1 END) as failed_tasks,
    COUNT(CASE WHEN ctr.status = 'pending' THEN 1 END) as pending_tasks,
    COUNT(CASE WHEN ctr.status = 'started' THEN 1 END) as running_tasks,
    AVG(ctr.runtime_seconds) as avg_runtime_seconds,
    MAX(ctr.runtime_seconds) as max_runtime_seconds,
    MIN(ctr.runtime_seconds) as min_runtime_seconds,
    AVG(ctr.retry_count) as avg_retry_count,
    MAX(ctr.created_at) as latest_task_created
FROM celery_task_results ctr
WHERE ctr.created_at >= NOW() - INTERVAL '24 hours'
GROUP BY ctr.queue_name, ctr.task_name
ORDER BY total_tasks DESC;

-- View for real-time progress monitoring
CREATE OR REPLACE VIEW active_task_progress AS
SELECT 
    tp.task_id,
    tp.entity_id,
    tp.progress_type,
    tp.current_value,
    tp.total_value,
    CASE 
        WHEN tp.total_value > 0 THEN 
            ROUND((tp.current_value::FLOAT / tp.total_value::FLOAT) * 100, 2)
        ELSE 0 
    END as progress_percentage,
    tp.message,
    tp.status,
    tp.updated_at,
    ctr.task_name,
    ctr.queue_name,
    ctr.worker_name,
    ctr.started_at
FROM task_progress tp
LEFT JOIN celery_task_results ctr ON tp.task_id = ctr.task_id
WHERE tp.status = 'in_progress'
ORDER BY tp.updated_at DESC;

-- Function to update task progress
CREATE OR REPLACE FUNCTION update_task_progress(
    p_task_id VARCHAR(255),
    p_entity_id VARCHAR(255),
    p_progress_type VARCHAR(100),
    p_current_value INTEGER,
    p_total_value INTEGER DEFAULT NULL,
    p_message TEXT DEFAULT NULL,
    p_status VARCHAR(50) DEFAULT 'in_progress'
) RETURNS UUID AS $$
DECLARE
    progress_id UUID;
BEGIN
    INSERT INTO task_progress (
        task_id, entity_id, progress_type, current_value,
        total_value, message, status, updated_at
    ) VALUES (
        p_task_id, p_entity_id, p_progress_type, p_current_value,
        p_total_value, p_message, p_status, CURRENT_TIMESTAMP
    )
    ON CONFLICT (task_id) DO UPDATE SET
        entity_id = EXCLUDED.entity_id,
        progress_type = EXCLUDED.progress_type,
        current_value = EXCLUDED.current_value,
        total_value = EXCLUDED.total_value,
        message = EXCLUDED.message,
        status = EXCLUDED.status,
        updated_at = CURRENT_TIMESTAMP
    RETURNING id INTO progress_id;
    
    RETURN progress_id;
END;
$$ LANGUAGE plpgsql;

-- Function to log Celery task results
CREATE OR REPLACE FUNCTION log_celery_task_result(
    p_task_id VARCHAR(255),
    p_task_name VARCHAR(255),
    p_queue_name VARCHAR(100),
    p_worker_name VARCHAR(255),
    p_status VARCHAR(50),
    p_result JSONB DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL,
    p_traceback TEXT DEFAULT NULL,
    p_started_at TIMESTAMP DEFAULT NULL,
    p_completed_at TIMESTAMP DEFAULT NULL,
    p_runtime_seconds FLOAT DEFAULT NULL,
    p_retry_count INTEGER DEFAULT 0
) RETURNS UUID AS $$
DECLARE
    result_id UUID;
BEGIN
    INSERT INTO celery_task_results (
        task_id, task_name, queue_name, worker_name, status,
        result, error_message, traceback, started_at, completed_at,
        runtime_seconds, retry_count
    ) VALUES (
        p_task_id, p_task_name, p_queue_name, p_worker_name, p_status,
        p_result, p_error_message, p_traceback, p_started_at, p_completed_at,
        p_runtime_seconds, p_retry_count
    )
    ON CONFLICT (task_id) DO UPDATE SET
        status = EXCLUDED.status,
        result = EXCLUDED.result,
        error_message = EXCLUDED.error_message,
        traceback = EXCLUDED.traceback,
        completed_at = EXCLUDED.completed_at,
        runtime_seconds = EXCLUDED.runtime_seconds,
        retry_count = EXCLUDED.retry_count
    RETURNING id INTO result_id;
    
    RETURN result_id;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update task progress status when tasks complete
CREATE OR REPLACE FUNCTION auto_update_progress_status() RETURNS TRIGGER AS $$
BEGIN
    -- Update progress status when Celery task completes
    IF NEW.status IN ('success', 'failure') AND OLD.status != NEW.status THEN
        UPDATE task_progress 
        SET 
            status = CASE 
                WHEN NEW.status = 'success' THEN 'completed'
                WHEN NEW.status = 'failure' THEN 'failed'
                ELSE status
            END,
            updated_at = CURRENT_TIMESTAMP
        WHERE task_id = NEW.task_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_update_progress_status
    AFTER UPDATE ON celery_task_results
    FOR EACH ROW
    EXECUTE FUNCTION auto_update_progress_status();

-- Comments for documentation
COMMENT ON TABLE task_progress IS 'Real-time progress tracking for all background tasks';
COMMENT ON TABLE celery_task_results IS 'Comprehensive logging of Celery task execution results';
COMMENT ON VIEW task_performance_overview IS 'Performance metrics for monitoring task queues';
COMMENT ON VIEW active_task_progress IS 'Real-time view of currently running tasks with progress';

-- Clean up old progress records (older than 7 days)
CREATE OR REPLACE FUNCTION cleanup_old_task_progress() RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM task_progress 
    WHERE updated_at < NOW() - INTERVAL '7 days' 
    AND status IN ('completed', 'failed');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    DELETE FROM celery_task_results 
    WHERE completed_at < NOW() - INTERVAL '30 days';
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Index for cleanup function performance
CREATE INDEX idx_task_progress_cleanup ON task_progress(updated_at, status);
CREATE INDEX idx_celery_results_cleanup ON celery_task_results(completed_at);