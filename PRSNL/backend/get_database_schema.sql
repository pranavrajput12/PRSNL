-- Run this query on your old working PRSNL database to get complete schema information

-- 1. Get all tables
SELECT '-- TABLES' as section;
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- 2. Get all columns for each table with data types
SELECT '-- TABLE COLUMNS' as section;
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
ORDER BY table_name, ordinal_position;

-- 3. Get all indexes
SELECT '-- INDEXES' as section;
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- 4. Get all foreign key constraints
SELECT '-- FOREIGN KEYS' as section;
SELECT
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public';

-- 5. Get complete CREATE TABLE statements for items table and development-related tables
SELECT '-- CREATE TABLE STATEMENTS' as section;
SELECT 
    'CREATE TABLE ' || table_name || ' (' || E'\n' ||
    string_agg(
        '    ' || column_name || ' ' || 
        data_type || 
        CASE 
            WHEN character_maximum_length IS NOT NULL 
            THEN '(' || character_maximum_length || ')' 
            ELSE '' 
        END ||
        CASE 
            WHEN is_nullable = 'NO' 
            THEN ' NOT NULL' 
            ELSE '' 
        END ||
        CASE 
            WHEN column_default IS NOT NULL 
            THEN ' DEFAULT ' || column_default 
            ELSE '' 
        END,
        E',\n' ORDER BY ordinal_position
    ) || E'\n);' as create_statement
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name IN ('items', 'development_categories', 'tags', 'item_tags', 'users', 'attachments', 'content_urls')
GROUP BY table_name
ORDER BY table_name;

-- 6. Check if specific development columns exist in items table
SELECT '-- DEVELOPMENT COLUMNS CHECK' as section;
SELECT 
    column_name,
    data_type,
    'EXISTS' as status
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'items'
AND column_name IN ('programming_language', 'project_category', 'difficulty_level', 
                    'is_career_related', 'learning_path', 'code_snippets', 
                    'repository_metadata', 'processed_content', 'search_vector', 
                    'embedding', 'raw_content', 'platform', 'url', 'summary', 
                    'status', 'duration')
ORDER BY column_name;

-- 7. Get sample data from development_categories if it exists
SELECT '-- DEVELOPMENT CATEGORIES DATA' as section;
SELECT * FROM development_categories ORDER BY name LIMIT 20;

-- 8. Get any triggers
SELECT '-- TRIGGERS' as section;
SELECT 
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement
FROM information_schema.triggers
WHERE trigger_schema = 'public'
ORDER BY event_object_table, trigger_name;