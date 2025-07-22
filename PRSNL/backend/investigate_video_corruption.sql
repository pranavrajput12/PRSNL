-- Video Data Corruption Investigation Script
-- This script identifies mismatched titles, thumbnails, and other inconsistencies in video entries

-- ===========================================================================
-- 1. BASIC VIDEO DATA OVERVIEW
-- ===========================================================================

-- Count of video entries by type and status
SELECT 
    'Video Count by Type and Status' as analysis_type,
    type, 
    status, 
    COUNT(*) as count
FROM items 
WHERE type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
   OR url LIKE '%youtube%' 
   OR url LIKE '%youtu.be%'
   OR url LIKE '%instagram%'
   OR url LIKE '%tiktok%'
   OR platform IS NOT NULL
GROUP BY type, status
ORDER BY count DESC;

-- ===========================================================================
-- 2. IDENTIFY VIDEOS WITH SUSPICIOUS TITLE/URL MISMATCHES
-- ===========================================================================

-- Find videos where title doesn't seem to match the URL content
-- This would catch cases like Rick Astley video showing as "Building AI Applications Tutorial"
SELECT 
    'Suspicious Title/URL Mismatches' as analysis_type,
    id,
    title,
    url,
    platform,
    thumbnail_url,
    created_at,
    updated_at,
    CASE 
        WHEN url LIKE '%youtube%' AND title LIKE '%tutorial%' AND url NOT LIKE '%tutorial%' THEN 'Title suggests tutorial but URL may not'
        WHEN url LIKE '%youtube%' AND title LIKE '%AI%' AND url NOT LIKE '%AI%' THEN 'Title suggests AI content but URL may not'
        WHEN url LIKE '%rick%astley%' AND title NOT LIKE '%rick%' AND title NOT LIKE '%astley%' AND title NOT LIKE '%never%gonna%' THEN 'Rick Astley URL with non-matching title'
        WHEN url LIKE '%never%gonna%give%you%up%' AND title NOT LIKE '%rick%' AND title NOT LIKE '%astley%' AND title NOT LIKE '%never%gonna%' THEN 'Never Gonna Give You Up URL with non-matching title'
        ELSE 'Other suspicious mismatch'
    END as mismatch_type
FROM items 
WHERE (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
       OR url LIKE '%youtube%' 
       OR url LIKE '%youtu.be%'
       OR url LIKE '%instagram%'
       OR url LIKE '%tiktok%'
       OR platform IS NOT NULL)
  AND (
    -- Check for common mismatches
    (url LIKE '%rick%astley%' AND title NOT LIKE '%rick%' AND title NOT LIKE '%astley%' AND title NOT LIKE '%never%gonna%') OR
    (url LIKE '%never%gonna%give%you%up%' AND title NOT LIKE '%rick%' AND title NOT LIKE '%astley%' AND title NOT LIKE '%never%gonna%') OR
    (url LIKE '%youtube%' AND title LIKE '%tutorial%' AND url NOT LIKE '%tutorial%') OR
    (url LIKE '%youtube%' AND title LIKE '%AI%' AND url NOT LIKE '%AI%')
  );

-- ===========================================================================
-- 3. IDENTIFY DUPLICATE VIDEO ENTRIES
-- ===========================================================================

-- Find potential duplicate videos based on URL
SELECT 
    'Duplicate Videos by URL' as analysis_type,
    url,
    COUNT(*) as duplicate_count,
    STRING_AGG(id::text, ', ') as item_ids,
    STRING_AGG(title, ' | ') as titles,
    MIN(created_at) as first_created,
    MAX(created_at) as last_created
FROM items 
WHERE url IS NOT NULL 
  AND (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
       OR url LIKE '%youtube%' 
       OR url LIKE '%youtu.be%'
       OR url LIKE '%instagram%'
       OR url LIKE '%tiktok%'
       OR platform IS NOT NULL)
GROUP BY url
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- Find potential duplicate videos based on title similarity
WITH title_groups AS (
    SELECT 
        LOWER(TRIM(title)) as normalized_title,
        COUNT(*) as count,
        STRING_AGG(id::text, ', ') as item_ids,
        STRING_AGG(url, ' | ') as urls
    FROM items 
    WHERE title IS NOT NULL 
      AND (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
           OR url LIKE '%youtube%' 
           OR url LIKE '%youtu.be%'
           OR url LIKE '%instagram%'
           OR url LIKE '%tiktok%'
           OR platform IS NOT NULL)
    GROUP BY LOWER(TRIM(title))
    HAVING COUNT(*) > 1
)
SELECT 
    'Duplicate Videos by Title' as analysis_type,
    normalized_title as title,
    count as duplicate_count,
    item_ids,
    urls
FROM title_groups
ORDER BY count DESC;

-- ===========================================================================
-- 4. IDENTIFY VIDEOS WITH BROKEN/MISSING THUMBNAILS
-- ===========================================================================

-- Videos with missing thumbnail URLs when they should have them
SELECT 
    'Videos with Missing Thumbnails' as analysis_type,
    id,
    title,
    url,
    platform,
    thumbnail_url,
    video_url,
    created_at,
    status
FROM items 
WHERE (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
       OR url LIKE '%youtube%' 
       OR url LIKE '%youtu.be%'
       OR url LIKE '%instagram%'
       OR url LIKE '%tiktok%'
       OR platform IS NOT NULL)
  AND (thumbnail_url IS NULL OR thumbnail_url = '')
  AND status = 'completed'
ORDER BY created_at DESC;

-- Videos with thumbnail URLs that don't match the expected pattern
SELECT 
    'Videos with Suspicious Thumbnail URLs' as analysis_type,
    id,
    title,
    url,
    platform,
    thumbnail_url,
    created_at,
    CASE 
        WHEN thumbnail_url LIKE '%rick%astley%' AND title NOT LIKE '%rick%' THEN 'Rick Astley thumbnail but different title'
        WHEN thumbnail_url LIKE '%youtube%' AND url NOT LIKE '%youtube%' THEN 'YouTube thumbnail but non-YouTube URL'
        WHEN thumbnail_url LIKE '%instagram%' AND url NOT LIKE '%instagram%' THEN 'Instagram thumbnail but non-Instagram URL'
        ELSE 'Other thumbnail mismatch'
    END as mismatch_type
FROM items 
WHERE thumbnail_url IS NOT NULL
  AND (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
       OR url LIKE '%youtube%' 
       OR url LIKE '%youtu.be%'
       OR url LIKE '%instagram%'
       OR url LIKE '%tiktok%'
       OR platform IS NOT NULL)
  AND (
    (thumbnail_url LIKE '%rick%astley%' AND title NOT LIKE '%rick%') OR
    (thumbnail_url LIKE '%youtube%' AND url NOT LIKE '%youtube%') OR
    (thumbnail_url LIKE '%instagram%' AND url NOT LIKE '%instagram%')
  );

-- ===========================================================================
-- 5. IDENTIFY VIDEOS WITH CONTENT/METADATA MISMATCHES
-- ===========================================================================

-- Videos where platform field doesn't match URL
SELECT 
    'Platform/URL Mismatches' as analysis_type,
    id,
    title,
    url,
    platform,
    thumbnail_url,
    created_at,
    CASE 
        WHEN platform = 'youtube' AND url NOT LIKE '%youtube%' AND url NOT LIKE '%youtu.be%' THEN 'Platform=youtube but non-YouTube URL'
        WHEN platform = 'instagram' AND url NOT LIKE '%instagram%' THEN 'Platform=instagram but non-Instagram URL'
        WHEN platform = 'tiktok' AND url NOT LIKE '%tiktok%' THEN 'Platform=tiktok but non-TikTok URL'
        WHEN platform = 'twitter' AND url NOT LIKE '%twitter%' AND url NOT LIKE '%x.com%' THEN 'Platform=twitter but non-Twitter URL'
        WHEN platform IS NULL AND (url LIKE '%youtube%' OR url LIKE '%youtu.be%') THEN 'YouTube URL but no platform set'
        WHEN platform IS NULL AND url LIKE '%instagram%' THEN 'Instagram URL but no platform set'
        WHEN platform IS NULL AND url LIKE '%tiktok%' THEN 'TikTok URL but no platform set'
        ELSE 'Other platform mismatch'
    END as mismatch_type
FROM items 
WHERE (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
       OR url LIKE '%youtube%' 
       OR url LIKE '%youtu.be%'
       OR url LIKE '%instagram%'
       OR url LIKE '%tiktok%'
       OR platform IS NOT NULL)
  AND (
    (platform = 'youtube' AND url NOT LIKE '%youtube%' AND url NOT LIKE '%youtu.be%') OR
    (platform = 'instagram' AND url NOT LIKE '%instagram%') OR
    (platform = 'tiktok' AND url NOT LIKE '%tiktok%') OR
    (platform = 'twitter' AND url NOT LIKE '%twitter%' AND url NOT LIKE '%x.com%') OR
    (platform IS NULL AND (url LIKE '%youtube%' OR url LIKE '%youtu.be%' OR url LIKE '%instagram%' OR url LIKE '%tiktok%'))
  );

-- ===========================================================================
-- 6. IDENTIFY VIDEOS WITH BROKEN OR NON-FUNCTIONAL ENTRIES
-- ===========================================================================

-- Videos with failed status or processing errors
SELECT 
    'Failed or Broken Video Entries' as analysis_type,
    id,
    title,
    url,
    platform,
    status,
    type,
    created_at,
    updated_at,
    video_url,
    thumbnail_url
FROM items 
WHERE (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
       OR url LIKE '%youtube%' 
       OR url LIKE '%youtu.be%'
       OR url LIKE '%instagram%'
       OR url LIKE '%tiktok%'
       OR platform IS NOT NULL)
  AND status IN ('failed', 'error', 'processing')
ORDER BY updated_at DESC;

-- Videos with missing essential fields
SELECT 
    'Videos with Missing Essential Fields' as analysis_type,
    id,
    title,
    url,
    platform,
    status,
    video_url,
    thumbnail_url,
    created_at,
    CASE 
        WHEN title IS NULL OR title = '' THEN 'Missing title'
        WHEN url IS NULL OR url = '' THEN 'Missing URL'
        WHEN platform IS NULL AND (url LIKE '%youtube%' OR url LIKE '%instagram%' OR url LIKE '%tiktok%') THEN 'Missing platform'
        ELSE 'Other missing field'
    END as missing_field
FROM items 
WHERE (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
       OR url LIKE '%youtube%' 
       OR url LIKE '%youtu.be%'
       OR url LIKE '%instagram%'
       OR url LIKE '%tiktok%'
       OR platform IS NOT NULL)
  AND (
    title IS NULL OR title = '' OR
    url IS NULL OR url = '' OR
    (platform IS NULL AND (url LIKE '%youtube%' OR url LIKE '%instagram%' OR url LIKE '%tiktok%'))
  );

-- ===========================================================================
-- 7. SPECIFIC CHECK FOR RICK ASTLEY / NEVER GONNA GIVE YOU UP CORRUPTION
-- ===========================================================================

-- Based on the screenshot showing Rick Astley's video with wrong title
SELECT 
    'Rick Astley Video Corruption Check' as analysis_type,
    id,
    title,
    url,
    platform,
    thumbnail_url,
    video_url,
    created_at,
    updated_at,
    CASE 
        WHEN url LIKE '%rick%astley%' OR url LIKE '%never%gonna%give%you%up%' THEN 'Rick Astley URL'
        WHEN title LIKE '%rick%astley%' OR title LIKE '%never%gonna%' THEN 'Rick Astley title'
        WHEN thumbnail_url LIKE '%rick%astley%' THEN 'Rick Astley thumbnail'
        ELSE 'Other'
    END as rick_astley_indicator
FROM items 
WHERE (
    url LIKE '%rick%astley%' OR 
    url LIKE '%never%gonna%give%you%up%' OR
    title LIKE '%rick%astley%' OR 
    title LIKE '%never%gonna%' OR
    thumbnail_url LIKE '%rick%astley%' OR
    (title LIKE '%Building AI Applications Tutorial%' AND url LIKE '%rick%astley%')
)
ORDER BY created_at DESC;

-- ===========================================================================
-- 8. SUMMARY STATISTICS
-- ===========================================================================

-- Overall video corruption summary
SELECT 
    'Video Corruption Summary' as analysis_type,
    COUNT(*) as total_video_entries,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_videos,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_videos,
    COUNT(CASE WHEN thumbnail_url IS NULL OR thumbnail_url = '' THEN 1 END) as missing_thumbnails,
    COUNT(CASE WHEN platform IS NULL THEN 1 END) as missing_platform,
    COUNT(CASE WHEN title IS NULL OR title = '' THEN 1 END) as missing_titles
FROM items 
WHERE (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
       OR url LIKE '%youtube%' 
       OR url LIKE '%youtu.be%'
       OR url LIKE '%instagram%'
       OR url LIKE '%tiktok%'
       OR platform IS NOT NULL);