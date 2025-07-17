-- Migration: Populate user_id for existing data
-- Created: 2025-07-16
-- Purpose: Assign all existing data to the first user (admin@prsnl.local)

-- Start transaction
BEGIN;

-- Get the first user's ID (admin@prsnl.local)
-- We'll assign all existing data to this user
DO $$ 
DECLARE
    admin_user_id UUID;
BEGIN
    -- Get the admin user ID
    SELECT id INTO admin_user_id FROM users WHERE email = 'admin@prsnl.local' LIMIT 1;
    
    -- If no admin user, get the first user
    IF admin_user_id IS NULL THEN
        SELECT id INTO admin_user_id FROM users ORDER BY created_at ASC LIMIT 1;
    END IF;
    
    -- If still no user, create a default admin user
    IF admin_user_id IS NULL THEN
        INSERT INTO users (email, name, password_hash, is_active, is_verified) 
        VALUES ('admin@prsnl.local', 'Admin User', '$2b$12$dummy.hash.for.migration', TRUE, TRUE)
        RETURNING id INTO admin_user_id;
    END IF;
    
    -- Update all existing data to belong to this user
    RAISE NOTICE 'Assigning all existing data to user ID: %', admin_user_id;
    
    -- 1. Update items table
    UPDATE items SET user_id = admin_user_id WHERE user_id IS NULL;
    
    -- 2. Update tags table
    UPDATE tags SET user_id = admin_user_id WHERE user_id IS NULL;
    
    -- 3. Update conversations table (if exists)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'conversations') THEN
        UPDATE conversations SET user_id = admin_user_id WHERE user_id IS NULL;
    END IF;
    
    -- 4. Update user_activity table (if exists)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_activity') THEN
        UPDATE user_activity SET user_id = admin_user_id WHERE user_id IS NULL;
    END IF;
    
    -- 5. Update video_analysis table (if exists)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'video_analysis') THEN
        UPDATE video_analysis SET user_id = admin_user_id WHERE user_id IS NULL;
    END IF;
    
    -- 6. Update files table (if exists)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'files') THEN
        UPDATE files SET user_id = admin_user_id WHERE user_id IS NULL;
    END IF;
    
    -- 7. Update attachments table (if exists)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'attachments') THEN
        UPDATE attachments SET user_id = admin_user_id WHERE user_id IS NULL;
    END IF;
    
    -- 8. Update development_categories table (if exists)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'development_categories') THEN
        UPDATE development_categories SET user_id = admin_user_id WHERE user_id IS NULL;
    END IF;
    
    -- 9. Update code_repositories table (if exists)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'code_repositories') THEN
        EXECUTE 'UPDATE code_repositories SET user_id = $1 WHERE user_id IS NULL' USING admin_user_id;
    END IF;
    
    -- 10. Update open_source_integrations table (if exists)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'open_source_integrations') THEN
        EXECUTE 'UPDATE open_source_integrations SET user_id = $1 WHERE user_id IS NULL' USING admin_user_id;
    END IF;
    
    -- Print statistics
    RAISE NOTICE 'Updated items: %', (SELECT COUNT(*) FROM items WHERE user_id = admin_user_id);
    RAISE NOTICE 'Updated tags: %', (SELECT COUNT(*) FROM tags WHERE user_id = admin_user_id);
    
    -- Print counts for tables that exist
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'conversations') THEN
        RAISE NOTICE 'Updated conversations: %', (SELECT COUNT(*) FROM conversations WHERE user_id = admin_user_id);
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'files') THEN
        RAISE NOTICE 'Updated files: %', (SELECT COUNT(*) FROM files WHERE user_id = admin_user_id);
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'attachments') THEN
        RAISE NOTICE 'Updated attachments: %', (SELECT COUNT(*) FROM attachments WHERE user_id = admin_user_id);
    END IF;
    
END $$;

COMMIT;

-- Print success message
SELECT 'User data populated successfully. Run add_foreign_keys.sql next.' AS status;