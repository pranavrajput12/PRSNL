-- Migration: Create processing_jobs table for unified job persistence system
-- This table provides job lifecycle tracking and result storage for all processing operations

BEGIN;

-- 1. Create processing_jobs table for comprehensive job tracking
CREATE TABLE IF NOT EXISTS processing_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(255) UNIQUE NOT NULL, -- External job identifier for API coordination
    job_type VARCHAR(100) NOT NULL, -- 'media_image', 'media_video', 'media_audio', 'embedding', 'crawl_ai', etc.
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed', 'retrying'
    
    -- Associated data
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    input_data JSONB NOT NULL DEFAULT '{}', -- Original input parameters
    result_data JSONB DEFAULT '{}', -- Final processing results
    
    -- Progress tracking
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    current_stage VARCHAR(100), -- Current processing stage
    stage_message TEXT, -- Human-readable stage description
    
    -- Error handling
    error_message TEXT,
    error_details JSONB DEFAULT '{}',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Timing
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    tags TEXT[], -- For categorization and filtering
    
    -- Constraints
    CONSTRAINT chk_processing_jobs_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'retrying', 'cancelled')),
    CONSTRAINT chk_processing_jobs_type CHECK (job_type ~ '^[a-z_]+$') -- Enforce snake_case
);

-- 2. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_processing_jobs_job_id ON processing_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_type ON processing_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_item_id ON processing_jobs(item_id);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_created_at ON processing_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status_type ON processing_jobs(status, job_type);

-- 3. Create trigger to auto-update last_updated timestamp
CREATE OR REPLACE FUNCTION update_processing_jobs_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    
    -- Auto-set started_at when status changes to 'processing'
    IF OLD.status != 'processing' AND NEW.status = 'processing' THEN
        NEW.started_at = NOW();
    END IF;
    
    -- Auto-set completed_at when status changes to completed/failed
    IF OLD.status NOT IN ('completed', 'failed', 'cancelled') 
       AND NEW.status IN ('completed', 'failed', 'cancelled') THEN
        NEW.completed_at = NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER processing_jobs_update_timestamp
    BEFORE UPDATE ON processing_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_processing_jobs_timestamp();

-- 4. Create view for job statistics
CREATE OR REPLACE VIEW processing_job_stats AS
SELECT 
    job_type,
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds,
    MIN(created_at) as earliest_job,
    MAX(created_at) as latest_job
FROM processing_jobs 
WHERE started_at IS NOT NULL
GROUP BY job_type, status;

-- 5. Add helpful functions for job management
CREATE OR REPLACE FUNCTION get_job_by_id(job_id_param VARCHAR)
RETURNS processing_jobs AS $$
DECLARE
    job_record processing_jobs;
BEGIN
    SELECT * INTO job_record 
    FROM processing_jobs 
    WHERE job_id = job_id_param;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Job with ID % not found', job_id_param;
    END IF;
    
    RETURN job_record;
END;
$$ LANGUAGE plpgsql;

-- 6. Function to cleanup old completed jobs (for maintenance)
CREATE OR REPLACE FUNCTION cleanup_old_jobs(days_old INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM processing_jobs 
    WHERE status IN ('completed', 'failed', 'cancelled')
    AND completed_at < NOW() - INTERVAL '1 day' * days_old;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 7. Add comments for documentation
COMMENT ON TABLE processing_jobs IS 'Unified job tracking table for all processing operations (media, AI, etc.)';
COMMENT ON COLUMN processing_jobs.job_id IS 'External job identifier used by API clients for coordination';
COMMENT ON COLUMN processing_jobs.job_type IS 'Type of processing job (media_image, media_video, media_audio, embedding, crawl_ai)';
COMMENT ON COLUMN processing_jobs.input_data IS 'Original input parameters passed to the job';
COMMENT ON COLUMN processing_jobs.result_data IS 'Final processing results stored as JSON';
COMMENT ON COLUMN processing_jobs.progress_percentage IS 'Current progress percentage (0-100)';
COMMENT ON COLUMN processing_jobs.current_stage IS 'Human-readable current processing stage';
COMMENT ON COLUMN processing_jobs.retry_count IS 'Number of times this job has been retried';

COMMIT;