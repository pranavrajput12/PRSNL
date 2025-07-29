-- Migration: Add category column to items table for three-tier categorization system
-- Date: 2025-01-28
-- Purpose: Support the new Library categorization feature (development, learning, work, personal, reference)

-- Add category column to items table
ALTER TABLE items 
ADD COLUMN IF NOT EXISTS category VARCHAR(50);

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);

-- Set initial categories based on existing content types and metadata
UPDATE items 
SET category = CASE
    -- Development category
    WHEN type IN ('code', 'repository', 'development') THEN 'development'
    WHEN project_category IS NOT NULL THEN 'development'
    WHEN programming_language IS NOT NULL THEN 'development'
    WHEN url LIKE '%github.com%' THEN 'development'
    WHEN url LIKE '%gitlab.com%' THEN 'development'
    WHEN url LIKE '%stackoverflow.com%' THEN 'development'
    
    -- Learning category
    WHEN type IN ('video', 'course', 'tutorial') THEN 'learning'
    WHEN url LIKE '%youtube.com%' AND (
        title ILIKE '%tutorial%' OR 
        title ILIKE '%learn%' OR 
        title ILIKE '%course%' OR
        title ILIKE '%guide%'
    ) THEN 'learning'
    WHEN url LIKE '%udemy.com%' THEN 'learning'
    WHEN url LIKE '%coursera.com%' THEN 'learning'
    WHEN learning_path IS NOT NULL THEN 'learning'
    
    -- Work category
    WHEN is_career_related = true THEN 'work'
    WHEN title ILIKE '%job%' OR title ILIKE '%career%' THEN 'work'
    WHEN title ILIKE '%interview%' OR title ILIKE '%resume%' THEN 'work'
    WHEN type = 'document' AND (
        title ILIKE '%project%' OR 
        title ILIKE '%proposal%' OR
        title ILIKE '%report%'
    ) THEN 'work'
    
    -- Personal category
    WHEN type = 'recipe' THEN 'personal'
    WHEN url LIKE '%reddit.com%' THEN 'personal'
    WHEN url LIKE '%twitter.com%' THEN 'personal'
    WHEN metadata->>'platform' IN ('twitter', 'reddit', 'instagram') THEN 'personal'
    
    -- Reference category (default for articles, bookmarks, documents)
    WHEN type IN ('article', 'bookmark', 'document') THEN 'reference'
    WHEN url LIKE '%wikipedia.org%' THEN 'reference'
    WHEN url LIKE '%docs.%' THEN 'reference'
    WHEN url LIKE '%documentation%' THEN 'reference'
    
    -- Default to reference for anything else
    ELSE 'reference'
END
WHERE category IS NULL;

-- Add comment explaining the column
COMMENT ON COLUMN items.category IS 'High-level content category for three-tier organization: development, learning, work, personal, reference';

-- Create a function to automatically set category for new items
CREATE OR REPLACE FUNCTION set_item_category()
RETURNS TRIGGER AS $$
BEGIN
    -- Only set if category is null
    IF NEW.category IS NULL THEN
        NEW.category = CASE
            -- Development
            WHEN NEW.type IN ('code', 'repository', 'development') THEN 'development'
            WHEN NEW.project_category IS NOT NULL THEN 'development'
            WHEN NEW.programming_language IS NOT NULL THEN 'development'
            WHEN NEW.url LIKE '%github.com%' THEN 'development'
            
            -- Learning
            WHEN NEW.type IN ('video', 'course', 'tutorial') THEN 'learning'
            WHEN NEW.learning_path IS NOT NULL THEN 'learning'
            
            -- Work
            WHEN NEW.is_career_related = true THEN 'work'
            
            -- Personal
            WHEN NEW.type = 'recipe' THEN 'personal'
            WHEN NEW.metadata->>'platform' IN ('twitter', 'reddit', 'instagram') THEN 'personal'
            
            -- Reference (default)
            ELSE 'reference'
        END;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-set category
DROP TRIGGER IF EXISTS auto_set_category ON items;
CREATE TRIGGER auto_set_category
    BEFORE INSERT ON items
    FOR EACH ROW
    EXECUTE FUNCTION set_item_category();

-- Verify the migration
DO $$
DECLARE
    category_counts RECORD;
BEGIN
    -- Check category distribution
    FOR category_counts IN 
        SELECT category, COUNT(*) as count 
        FROM items 
        GROUP BY category 
        ORDER BY count DESC
    LOOP
        RAISE NOTICE 'Category: %, Count: %', category_counts.category, category_counts.count;
    END LOOP;
    
    -- Check if any nulls remain
    SELECT COUNT(*) INTO category_counts FROM items WHERE category IS NULL;
    IF category_counts.count > 0 THEN
        RAISE WARNING 'Found % items with NULL category', category_counts.count;
    ELSE
        RAISE NOTICE 'All items have been categorized successfully';
    END IF;
END $$;