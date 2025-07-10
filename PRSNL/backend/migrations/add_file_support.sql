-- Migration: Add file support to PRSNL database
-- This migration adds tables and columns to support file uploads and processing

BEGIN;

-- Create files table to store file metadata
CREATE TABLE IF NOT EXISTS files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64) NOT NULL UNIQUE,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_extension VARCHAR(10) NOT NULL,
    file_category VARCHAR(20) NOT NULL, -- 'document', 'image', 'pdf', 'office', 'text'
    
    -- Extracted content
    extracted_text TEXT,
    text_file_path TEXT,
    word_count INTEGER DEFAULT 0,
    page_count INTEGER DEFAULT 0,
    extraction_method VARCHAR(50),
    
    -- Image-specific fields
    thumbnail_path TEXT,
    image_width INTEGER,
    image_height INTEGER,
    
    -- Processing metadata
    processing_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    processing_error TEXT,
    processed_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT files_item_id_fkey FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_files_item_id ON files(item_id);
CREATE INDEX idx_files_file_hash ON files(file_hash);
CREATE INDEX idx_files_file_category ON files(file_category);
CREATE INDEX idx_files_processing_status ON files(processing_status);
CREATE INDEX idx_files_created_at ON files(created_at);

-- Add file-related columns to items table
ALTER TABLE items ADD COLUMN IF NOT EXISTS has_files BOOLEAN DEFAULT FALSE;
ALTER TABLE items ADD COLUMN IF NOT EXISTS file_count INTEGER DEFAULT 0;

-- Update items table to include content_type if not exists
ALTER TABLE items ADD COLUMN IF NOT EXISTS content_type VARCHAR(20) DEFAULT 'auto';

-- Create function to update file count
CREATE OR REPLACE FUNCTION update_item_file_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE items 
        SET file_count = file_count + 1,
            has_files = TRUE
        WHERE id = NEW.item_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE items 
        SET file_count = GREATEST(file_count - 1, 0),
            has_files = (file_count - 1 > 0)
        WHERE id = OLD.item_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update file count
CREATE TRIGGER trigger_update_item_file_count
    AFTER INSERT OR DELETE ON files
    FOR EACH ROW
    EXECUTE FUNCTION update_item_file_count();

-- Create file_processing_log table for tracking processing history
CREATE TABLE IF NOT EXISTS file_processing_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    processing_step VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'started', 'completed', 'failed'
    message TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT file_processing_log_file_id_fkey FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

CREATE INDEX idx_file_processing_log_file_id ON file_processing_log(file_id);
CREATE INDEX idx_file_processing_log_created_at ON file_processing_log(created_at);

-- Update attachments table to support file references
ALTER TABLE attachments ADD COLUMN IF NOT EXISTS file_id UUID REFERENCES files(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_attachments_file_id ON attachments(file_id);

-- Add file storage statistics view
CREATE OR REPLACE VIEW file_storage_stats AS
SELECT 
    file_category,
    COUNT(*) as file_count,
    SUM(file_size) as total_size_bytes,
    ROUND(SUM(file_size) / 1024.0 / 1024.0, 2) as total_size_mb,
    AVG(file_size) as avg_size_bytes,
    MIN(created_at) as first_file_date,
    MAX(created_at) as last_file_date
FROM files
GROUP BY file_category;

-- Add processing statistics view
CREATE OR REPLACE VIEW file_processing_stats AS
SELECT 
    processing_status,
    file_category,
    COUNT(*) as count,
    AVG(word_count) as avg_word_count,
    AVG(page_count) as avg_page_count,
    COUNT(CASE WHEN extraction_method = 'tesseract_ocr' THEN 1 END) as ocr_processed,
    COUNT(CASE WHEN extraction_method = 'pypdf2' THEN 1 END) as pdf_processed,
    COUNT(CASE WHEN extraction_method = 'python-docx' THEN 1 END) as docx_processed
FROM files
GROUP BY processing_status, file_category;

-- Add recent files view
CREATE OR REPLACE VIEW recent_files AS
SELECT 
    f.id,
    f.item_id,
    f.original_filename,
    f.file_category,
    f.file_size,
    f.processing_status,
    f.created_at,
    i.title as item_title,
    i.url as item_url,
    CASE 
        WHEN f.word_count > 0 THEN f.word_count
        ELSE 0
    END as word_count
FROM files f
JOIN items i ON f.item_id = i.id
ORDER BY f.created_at DESC;

-- Function to get file content summary
CREATE OR REPLACE FUNCTION get_file_content_summary(file_id UUID)
RETURNS TABLE (
    filename TEXT,
    category TEXT,
    size_mb NUMERIC,
    word_count INTEGER,
    page_count INTEGER,
    extraction_method TEXT,
    processing_status TEXT,
    has_thumbnail BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.original_filename::TEXT,
        f.file_category::TEXT,
        ROUND(f.file_size / 1024.0 / 1024.0, 2) as size_mb,
        f.word_count,
        f.page_count,
        f.extraction_method::TEXT,
        f.processing_status::TEXT,
        (f.thumbnail_path IS NOT NULL) as has_thumbnail,
        f.created_at
    FROM files f
    WHERE f.id = file_id;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up orphaned files
CREATE OR REPLACE FUNCTION cleanup_orphaned_files()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete files that reference non-existent items
    DELETE FROM files 
    WHERE item_id NOT IN (SELECT id FROM items);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Add updated_at trigger for files table
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_files_updated_at
    BEFORE UPDATE ON files
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;