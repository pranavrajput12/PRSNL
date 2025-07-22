-- Fix Rick Astley Video Corruption
-- This script specifically addresses the issue where Rick Astley's "Never Gonna Give You Up"
-- video shows with the title "Building AI Applications Tutorial"

-- ===========================================================================
-- 1. IDENTIFY THE CORRUPTED RICK ASTLEY ENTRY
-- ===========================================================================

-- Find entries with Rick Astley URL but wrong title
SELECT 
    'Corrupted Rick Astley Entries' as issue_type,
    id,
    title,
    url,
    thumbnail_url,
    platform,
    status,
    created_at,
    updated_at
FROM items 
WHERE (url LIKE '%rick%astley%' 
    OR url LIKE '%never%gonna%give%you%up%'
    OR url LIKE '%dQw4w9WgXcQ%')  -- YouTube video ID for Never Gonna Give You Up
  AND title NOT LIKE '%rick%'
  AND title NOT LIKE '%astley%' 
  AND title NOT LIKE '%never%gonna%'
  AND title NOT LIKE '%give you up%'
ORDER BY created_at DESC;

-- ===========================================================================
-- 2. BACKUP THE CORRUPTED DATA BEFORE FIXING
-- ===========================================================================

-- Create a backup table for the corrupted entries
CREATE TABLE IF NOT EXISTS corrupted_video_backup AS
SELECT 
    id,
    title,
    url, 
    thumbnail_url,
    platform,
    status,
    metadata,
    created_at,
    updated_at,
    'rick_astley_title_corruption' as corruption_type,
    NOW() as backup_created_at
FROM items 
WHERE (url LIKE '%rick%astley%' 
    OR url LIKE '%never%gonna%give%you%up%'
    OR url LIKE '%dQw4w9WgXcQ%')
  AND title NOT LIKE '%rick%'
  AND title NOT LIKE '%astley%' 
  AND title NOT LIKE '%never%gonna%'
  AND title NOT LIKE '%give you up%';

-- ===========================================================================
-- 3. FIX THE CORRUPTED TITLES
-- ===========================================================================

-- Update the corrupted Rick Astley entries with the correct title
UPDATE items 
SET 
    title = 'Rick Astley - Never Gonna Give You Up (Official Video)',
    summary = 'The official video for "Never Gonna Give You Up" by Rick Astley',
    platform = 'youtube',
    status = 'pending',  -- Mark for reprocessing to get correct thumbnail
    updated_at = NOW()
WHERE (url LIKE '%rick%astley%' 
    OR url LIKE '%never%gonna%give%you%up%'
    OR url LIKE '%dQw4w9WgXcQ%')
  AND title NOT LIKE '%rick%'
  AND title NOT LIKE '%astley%' 
  AND title NOT LIKE '%never%gonna%'
  AND title NOT LIKE '%give you up%';

-- ===========================================================================
-- 4. VERIFY THE FIX
-- ===========================================================================

-- Check that the titles have been corrected
SELECT 
    'Fixed Rick Astley Entries' as verification_type,
    id,
    title,
    url,
    platform,
    status,
    updated_at
FROM items 
WHERE url LIKE '%rick%astley%' 
   OR url LIKE '%never%gonna%give%you%up%'
   OR url LIKE '%dQw4w9WgXcQ%'
ORDER BY updated_at DESC;

-- ===========================================================================
-- 5. IDENTIFY OTHER SIMILAR TITLE/URL CORRUPTIONS
-- ===========================================================================

-- Look for other videos that might have similar title/URL mismatches
WITH video_analysis AS (
    SELECT 
        id,
        title,
        url,
        platform,
        CASE 
            -- Extract video ID from YouTube URLs
            WHEN url LIKE '%youtube.com/watch?v=%' THEN 
                SUBSTRING(url FROM 'v=([^&]+)')
            WHEN url LIKE '%youtu.be/%' THEN 
                SUBSTRING(url FROM 'youtu\.be/([^?&]+)')
            ELSE NULL
        END as video_id,
        CASE 
            -- Check for common educational/tutorial patterns that might be wrong
            WHEN title LIKE '%tutorial%' OR title LIKE '%guide%' OR title LIKE '%how to%' THEN 'educational'
            WHEN title LIKE '%music%' OR title LIKE '%song%' OR title LIKE '%official%' THEN 'music'
            WHEN title LIKE '%AI%' OR title LIKE '%machine learning%' OR title LIKE '%data%' THEN 'tech'
            ELSE 'other'
        END as title_category
    FROM items 
    WHERE (type IN ('video', 'youtube') OR url LIKE '%youtube%' OR url LIKE '%youtu.be%')
      AND url IS NOT NULL 
      AND title IS NOT NULL
)
SELECT 
    'Potential Title/URL Mismatches' as analysis_type,
    id,
    title,
    url,
    video_id,
    title_category,
    platform
FROM video_analysis
WHERE video_id IS NOT NULL
  AND (
    -- Look for educational titles on music video IDs (common corruption pattern)
    (video_id IN ('dQw4w9WgXcQ', 'oHg5SJYRHA0', 'L_jWHffIx5E') AND title_category = 'educational') OR
    -- Look for music titles on educational video IDs
    (title_category = 'music' AND url LIKE '%tutorial%') OR
    -- Look for completely mismatched content
    (title LIKE '%Building AI Applications%' AND url NOT LIKE '%AI%' AND url NOT LIKE '%tutorial%')
  );

-- ===========================================================================
-- 6. CLEANUP RECOMMENDATIONS
-- ===========================================================================

-- Generate a report of recommended actions
SELECT 
    'Cleanup Recommendations' as report_type,
    COUNT(*) as affected_entries,
    'Rick Astley corruption fixed' as action_taken,
    'Check for similar title/URL mismatches in other videos' as next_steps
FROM corrupted_video_backup
WHERE corruption_type = 'rick_astley_title_corruption';

-- Count of entries that need reprocessing
SELECT 
    'Reprocessing Queue' as report_type,
    COUNT(*) as entries_pending_reprocessing
FROM items 
WHERE status = 'pending' 
  AND (url LIKE '%rick%astley%' 
    OR url LIKE '%never%gonna%give%you%up%'
    OR url LIKE '%dQw4w9WgXcQ%');