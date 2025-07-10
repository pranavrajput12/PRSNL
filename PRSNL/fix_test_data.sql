
-- Fix for test files that reference item_type instead of type
-- This script updates all test INSERT statements

UPDATE items SET type = 'article' WHERE type IS NULL;

-- No additional fixes needed since we're resetting the database
