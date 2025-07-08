-- Migration: Make URL field nullable to support content-only captures
-- This allows capturing notes, thoughts, and other content without requiring a URL

-- Make the url column nullable
ALTER TABLE items 
ALTER COLUMN url DROP NOT NULL;

-- Add a check constraint to ensure either url or raw_content is provided
ALTER TABLE items 
ADD CONSTRAINT items_url_or_content_check 
CHECK (url IS NOT NULL OR raw_content IS NOT NULL);

-- Update the index to handle NULL values properly
DROP INDEX IF EXISTS idx_items_url;
CREATE INDEX idx_items_url ON items(url) WHERE url IS NOT NULL;

-- Add comment to document the change
COMMENT ON COLUMN items.url IS 'Optional URL of the captured item. Can be NULL for content-only captures like notes or thoughts.';