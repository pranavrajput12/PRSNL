-- Add content classification columns to items table
ALTER TABLE items 
ADD COLUMN IF NOT EXISTS content_type VARCHAR(50) DEFAULT 'auto',
ADD COLUMN IF NOT EXISTS enable_summarization BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS video_url TEXT,
ADD COLUMN IF NOT EXISTS highlight TEXT;

-- Create index on content_type for faster queries
CREATE INDEX IF NOT EXISTS idx_items_content_type ON items(content_type);