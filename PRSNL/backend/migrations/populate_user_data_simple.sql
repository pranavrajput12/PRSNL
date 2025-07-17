-- Migration: Populate user_id for existing data (only tables with user_id column)
-- Created: 2025-07-16
-- Purpose: Assign all existing data to the first user (admin@prsnl.local)

-- Start transaction
BEGIN;

-- Get the first user's ID (admin@prsnl.local)
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
    
    -- Update only the main tables we care about
    UPDATE items SET user_id = admin_user_id WHERE user_id IS NULL;
    UPDATE tags SET user_id = admin_user_id WHERE user_id IS NULL;
    
    -- Print statistics
    RAISE NOTICE 'Updated items: %', (SELECT COUNT(*) FROM items WHERE user_id = admin_user_id);
    RAISE NOTICE 'Updated tags: %', (SELECT COUNT(*) FROM tags WHERE user_id = admin_user_id);
    
END $$;

COMMIT;

-- Verify the data is populated
SELECT 
    'items' as table_name,
    COUNT(*) as total_rows, 
    COUNT(user_id) as rows_with_user_id,
    COUNT(DISTINCT user_id) as unique_users
FROM items
UNION ALL
SELECT 
    'tags' as table_name,
    COUNT(*) as total_rows, 
    COUNT(user_id) as rows_with_user_id,
    COUNT(DISTINCT user_id) as unique_users
FROM tags;

-- Print success message
SELECT 'User data populated successfully for items and tags.' AS status;