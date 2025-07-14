-- Migration: Add Celery task tracking tables for CodeMirror
-- Date: 2025-07-14
-- Description: Enterprise-grade task tracking for distributed processing

-- Table for tracking Celery task states
CREATE TABLE IF NOT EXISTS celery_task_meta (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    result TEXT,
    date_done TIMESTAMP,
    traceback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast task lookup
CREATE INDEX idx_celery_task_meta_task_id ON celery_task_meta(task_id);
CREATE INDEX idx_celery_task_meta_status ON celery_task_meta(status);
CREATE INDEX idx_celery_task_meta_date_done ON celery_task_meta(date_done);

-- Table for task results (Celery result backend)
CREATE TABLE IF NOT EXISTS celery_task_result (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    result JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    date_done TIMESTAMP,
    traceback TEXT,
    meta JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for result backend
CREATE INDEX idx_celery_task_result_task_id ON celery_task_result(task_id);
CREATE INDEX idx_celery_task_result_status ON celery_task_result(status);

-- Table for tracking CodeMirror-specific task workflows
CREATE TABLE IF NOT EXISTS codemirror_task_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id VARCHAR(255) NOT NULL,
    workflow_type VARCHAR(100) NOT NULL, -- 'analysis', 'comparison', 'pattern_detection'
    main_task_id VARCHAR(255) NOT NULL,
    subtask_ids TEXT[], -- Array of subtask IDs
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    progress INTEGER DEFAULT 0,
    total_subtasks INTEGER DEFAULT 0,
    completed_subtasks INTEGER DEFAULT 0,
    metadata JSONB,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for workflow tracking
CREATE INDEX idx_codemirror_workflows_job_id ON codemirror_task_workflows(job_id);
CREATE INDEX idx_codemirror_workflows_main_task ON codemirror_task_workflows(main_task_id);
CREATE INDEX idx_codemirror_workflows_status ON codemirror_task_workflows(status);

-- Table for task progress updates (for real-time monitoring)
CREATE TABLE IF NOT EXISTS codemirror_task_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(255) NOT NULL,
    job_id VARCHAR(255),
    progress_type VARCHAR(50) NOT NULL, -- 'file_analysis', 'pattern_detection', etc.
    current_value INTEGER DEFAULT 0,
    total_value INTEGER,
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for progress tracking
CREATE INDEX idx_task_progress_task_id ON codemirror_task_progress(task_id);
CREATE INDEX idx_task_progress_job_id ON codemirror_task_progress(job_id);
CREATE INDEX idx_task_progress_created ON codemirror_task_progress(created_at DESC);

-- Function to update workflow progress
CREATE OR REPLACE FUNCTION update_workflow_progress()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the parent workflow when a subtask completes
    IF NEW.status IN ('SUCCESS', 'FAILURE') AND OLD.status != NEW.status THEN
        UPDATE codemirror_task_workflows
        SET 
            completed_subtasks = completed_subtasks + 1,
            progress = ROUND((completed_subtasks + 1) * 100.0 / total_subtasks),
            updated_at = CURRENT_TIMESTAMP
        WHERE NEW.task_id = ANY(subtask_ids);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update workflow progress
CREATE TRIGGER update_workflow_on_task_complete
AFTER UPDATE ON celery_task_result
FOR EACH ROW
EXECUTE FUNCTION update_workflow_progress();

-- Add Celery task tracking to processing_jobs
ALTER TABLE processing_jobs 
ADD COLUMN IF NOT EXISTS celery_task_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS celery_workflow_id UUID;

-- Add foreign key constraint
ALTER TABLE processing_jobs
ADD CONSTRAINT fk_celery_workflow
FOREIGN KEY (celery_workflow_id) 
REFERENCES codemirror_task_workflows(id)
ON DELETE SET NULL;

-- Create indexes for job-task correlation
CREATE INDEX idx_processing_jobs_celery_task ON processing_jobs(celery_task_id);
CREATE INDEX idx_processing_jobs_celery_workflow ON processing_jobs(celery_workflow_id);

-- View for monitoring active tasks
CREATE OR REPLACE VIEW codemirror_active_tasks AS
SELECT 
    w.id as workflow_id,
    w.job_id,
    w.workflow_type,
    w.status as workflow_status,
    w.progress,
    w.total_subtasks,
    w.completed_subtasks,
    w.started_at,
    j.item_id as user_id,
    j.job_type,
    j.input_data->>'repo_id' as repo_id,
    j.input_data->>'analysis_depth' as analysis_depth
FROM codemirror_task_workflows w
JOIN processing_jobs j ON w.job_id = j.job_id
WHERE w.status IN ('PENDING', 'STARTED', 'RETRY')
ORDER BY w.created_at DESC;

-- Table for storing analysis results from tasks
CREATE TABLE IF NOT EXISTS codemirror_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID NOT NULL,
    task_id VARCHAR(255) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL, -- 'structure', 'patterns', 'security', etc.
    results JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for analysis results
CREATE INDEX idx_analysis_results_repo_id ON codemirror_analysis_results(repo_id);
CREATE INDEX idx_analysis_results_task_id ON codemirror_analysis_results(task_id);
CREATE INDEX idx_analysis_results_type ON codemirror_analysis_results(analysis_type);
CREATE INDEX idx_analysis_results_created ON codemirror_analysis_results(created_at DESC);

-- Add comment
COMMENT ON TABLE celery_task_meta IS 'Tracks Celery task execution states for monitoring';
COMMENT ON TABLE celery_task_result IS 'Stores Celery task results for the result backend';
COMMENT ON TABLE codemirror_task_workflows IS 'Tracks CodeMirror analysis workflows and their subtasks';
COMMENT ON TABLE codemirror_task_progress IS 'Real-time progress updates for long-running tasks';
COMMENT ON TABLE codemirror_analysis_results IS 'Stores intermediate analysis results from Celery tasks';