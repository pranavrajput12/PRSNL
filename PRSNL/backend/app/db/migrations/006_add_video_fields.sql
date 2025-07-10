-- Add video-specific columns to items table
ALTER TABLE items 
ADD COLUMN IF NOT EXISTS type VARCHAR(50) DEFAULT 'bookmark',
ADD COLUMN IF NOT EXISTS platform VARCHAR(50),
ADD COLUMN IF NOT EXISTS duration INTEGER,
ADD COLUMN IF NOT EXISTS thumbnail_url TEXT,
ADD COLUMN IF NOT EXISTS file_path TEXT;

-- Create index on type for faster queries
CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);