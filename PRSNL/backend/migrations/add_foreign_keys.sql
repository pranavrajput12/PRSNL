-- Migration: Add foreign key constraints after populating user_id
-- Created: 2025-07-16
-- Purpose: Add NOT NULL constraints and foreign key relationships

-- Start transaction
BEGIN;

-- Add NOT NULL constraints (this will fail if any records have NULL user_id)
ALTER TABLE items ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE tags ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE conversations ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE user_activity ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE video_analysis ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE files ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE attachments ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE development_categories ALTER COLUMN user_id SET NOT NULL;

-- Add foreign key constraints
ALTER TABLE items ADD CONSTRAINT fk_items_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE tags ADD CONSTRAINT fk_tags_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE conversations ADD CONSTRAINT fk_conversations_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE user_activity ADD CONSTRAINT fk_user_activity_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE video_analysis ADD CONSTRAINT fk_video_analysis_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE files ADD CONSTRAINT fk_files_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE attachments ADD CONSTRAINT fk_attachments_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE development_categories ADD CONSTRAINT fk_development_categories_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Add constraints for code_repositories if it exists
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'code_repositories') THEN
        ALTER TABLE code_repositories ALTER COLUMN user_id SET NOT NULL;
        ALTER TABLE code_repositories ADD CONSTRAINT fk_code_repositories_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Add constraints for open_source_integrations if it exists
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'open_source_integrations') THEN
        ALTER TABLE open_source_integrations ALTER COLUMN user_id SET NOT NULL;
        ALTER TABLE open_source_integrations ADD CONSTRAINT fk_open_source_integrations_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Create composite indexes for better performance
CREATE INDEX idx_items_user_created ON items(user_id, created_at DESC);
CREATE INDEX idx_tags_user_name ON tags(user_id, name);
CREATE INDEX idx_conversations_user_created ON conversations(user_id, created_at DESC);

COMMIT;

-- Print success message
SELECT 'Foreign key constraints added successfully. User isolation is now active.' AS status;