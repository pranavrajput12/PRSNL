-- Migration: Add user_id foreign keys to all tables for user data isolation
-- Created: 2025-07-16
-- Purpose: Implement proper user data isolation so each user only sees their own data

-- Start transaction
BEGIN;

-- 1. Add user_id to items table
ALTER TABLE items ADD COLUMN user_id UUID;

-- 2. Add user_id to tags table
ALTER TABLE tags ADD COLUMN user_id UUID;

-- 3. Add user_id to conversations table
ALTER TABLE conversations ADD COLUMN user_id UUID;

-- 4. Add user_id to code_repositories table (if it exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'code_repositories') THEN
        ALTER TABLE code_repositories ADD COLUMN user_id UUID;
    END IF;
END $$;

-- 5. Add user_id to open_source_integrations table (if it exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'open_source_integrations') THEN
        ALTER TABLE open_source_integrations ADD COLUMN user_id UUID;
    END IF;
END $$;

-- 6. Add user_id to user_activity table
ALTER TABLE user_activity ADD COLUMN user_id UUID;

-- 7. Add user_id to video_analysis table
ALTER TABLE video_analysis ADD COLUMN user_id UUID;

-- 8. Add user_id to files table
ALTER TABLE files ADD COLUMN user_id UUID;

-- 9. Add user_id to attachments table
ALTER TABLE attachments ADD COLUMN user_id UUID;

-- 10. Add user_id to development_categories table
ALTER TABLE development_categories ADD COLUMN user_id UUID;

-- Wait to add foreign key constraints until after we populate the data
-- This prevents errors when existing data doesn't have user_id yet

-- Add indexes for performance (without NOT NULL constraints yet)
CREATE INDEX idx_items_user_id ON items(user_id);
CREATE INDEX idx_tags_user_id ON tags(user_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX idx_video_analysis_user_id ON video_analysis(user_id);
CREATE INDEX idx_files_user_id ON files(user_id);
CREATE INDEX idx_attachments_user_id ON attachments(user_id);
CREATE INDEX idx_development_categories_user_id ON development_categories(user_id);

-- Add indexes for code_repositories if it exists
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'code_repositories') THEN
        CREATE INDEX idx_code_repositories_user_id ON code_repositories(user_id);
    END IF;
END $$;

-- Add indexes for open_source_integrations if it exists
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'open_source_integrations') THEN
        CREATE INDEX idx_open_source_integrations_user_id ON open_source_integrations(user_id);
    END IF;
END $$;

COMMIT;

-- Print success message
SELECT 'User isolation columns added successfully. Run populate_user_data.sql next.' AS status;