-- Video Corruption Monitoring and Prevention Queries
-- Use these queries regularly to monitor for video data corruption

-- ===========================================================================
-- 1. DAILY VIDEO HEALTH CHECK
-- ===========================================================================

-- Query to run daily to check for new corruption issues
SELECT 
    'Daily Video Health Check' as check_type,
    COUNT(*) as total_videos_today,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_today,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_today,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_today,
    ROUND(100.0 * COUNT(CASE WHEN status = 'failed' THEN 1 END) / COUNT(*), 2) as failure_rate_percent
FROM items 
WHERE (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
       OR url LIKE '%youtube%' 
       OR url LIKE '%youtu.be%'
       OR url LIKE '%instagram%'
       OR url LIKE '%tiktok%'
       OR platform IS NOT NULL)
  AND DATE(created_at) = CURRENT_DATE;

-- ===========================================================================
-- 2. TITLE/URL MISMATCH DETECTION
-- ===========================================================================

-- Detect potential title/URL mismatches for YouTube videos
SELECT 
    'Title/URL Mismatch Detection' as check_type,
    id,
    title,
    url,
    platform,
    status,
    created_at,
    CASE 
        WHEN url LIKE '%dQw4w9WgXcQ%' THEN 'Rick Astley - Never Gonna Give You Up'
        WHEN url LIKE '%oHg5SJYRHA0%' THEN 'RickRoll'  
        WHEN url LIKE '%L_jWHffIx5E%' THEN 'Darude - Sandstorm'
        WHEN url LIKE '%kffacxfA7G4%' THEN 'Baby Shark Dance'
        ELSE 'Unknown video'
    END as expected_title_keywords
FROM items 
WHERE url LIKE '%youtube%'
  AND (
    (url LIKE '%dQw4w9WgXcQ%' AND title NOT LIKE '%rick%' AND title NOT LIKE '%astley%' AND title NOT LIKE '%never%gonna%') OR
    (url LIKE '%oHg5SJYRHA0%' AND title NOT LIKE '%rick%') OR
    (url LIKE '%L_jWHffIx5E%' AND title NOT LIKE '%sandstorm%' AND title NOT LIKE '%darude%') OR
    (url LIKE '%kffacxfA7G4%' AND title NOT LIKE '%baby%shark%')
  )
  AND created_at > NOW() - INTERVAL '7 days';

-- ===========================================================================
-- 3. PROCESSING QUEUE MONITORING
-- ===========================================================================

-- Monitor videos stuck in processing for too long
SELECT 
    'Stuck Processing Jobs' as check_type,
    id,
    title,
    url,
    status,
    created_at,
    updated_at,
    ROUND(EXTRACT(EPOCH FROM (NOW() - updated_at)) / 3600, 2) as hours_stuck
FROM items 
WHERE status IN ('processing', 'pending')
  AND (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
       OR url LIKE '%youtube%' 
       OR platform IS NOT NULL)
  AND updated_at < NOW() - INTERVAL '4 hours'
ORDER BY updated_at ASC;

-- ===========================================================================
-- 4. DUPLICATE VIDEO DETECTION
-- ===========================================================================

-- Find duplicate videos created today
SELECT 
    'Today Duplicate Detection' as check_type,
    url,
    COUNT(*) as duplicate_count,
    STRING_AGG(id::text, ', ') as duplicate_ids,
    STRING_AGG(title, ' | ') as titles
FROM items 
WHERE url IS NOT NULL 
  AND (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
       OR url LIKE '%youtube%' 
       OR platform IS NOT NULL)
  AND DATE(created_at) = CURRENT_DATE
GROUP BY url
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- ===========================================================================
-- 5. METADATA CONSISTENCY CHECKS  
-- ===========================================================================

-- Check for videos missing essential metadata
SELECT 
    'Missing Metadata Check' as check_type,
    id,
    title,
    url,
    platform,
    status,
    CASE 
        WHEN platform IS NULL THEN 'Missing platform'
        WHEN thumbnail_url IS NULL OR thumbnail_url = '' THEN 'Missing thumbnail'
        WHEN duration IS NULL THEN 'Missing duration'
        ELSE 'Other issue'
    END as missing_field
FROM items 
WHERE (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
       OR url LIKE '%youtube%' 
       OR platform IS NOT NULL)
  AND (
    platform IS NULL OR
    (thumbnail_url IS NULL OR thumbnail_url = '') OR
    duration IS NULL
  )
  AND status = 'completed'
  AND created_at > NOW() - INTERVAL '7 days';

-- ===========================================================================
-- 6. FAILURE PATTERN ANALYSIS
-- ===========================================================================

-- Analyze failure patterns to identify systematic issues
SELECT 
    'Failure Pattern Analysis' as check_type,
    DATE(created_at) as failure_date,
    COUNT(*) as total_failures,
    STRING_AGG(DISTINCT SUBSTRING(url FROM 'https?://[^/]+'), ', ') as failed_domains,
    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_failure_time_seconds
FROM items 
WHERE status = 'failed'
  AND (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
       OR url LIKE '%youtube%' 
       OR platform IS NOT NULL)
  AND created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY failure_date DESC;

-- ===========================================================================
-- 7. PERFORMANCE MONITORING
-- ===========================================================================

-- Monitor video processing performance
SELECT 
    'Processing Performance' as check_type,
    DATE(created_at) as process_date,
    COUNT(*) as total_videos,
    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_processing_seconds,
    MIN(EXTRACT(EPOCH FROM (updated_at - created_at))) as min_processing_seconds,
    MAX(EXTRACT(EPOCH FROM (updated_at - created_at))) as max_processing_seconds,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (updated_at - created_at))) as median_processing_seconds
FROM items 
WHERE status = 'completed'
  AND (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
       OR url LIKE '%youtube%' 
       OR platform IS NOT NULL)
  AND updated_at > created_at  -- Only count items that were actually processed
  AND created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY process_date DESC;

-- ===========================================================================
-- 8. CORRUPTION PREVENTION TRIGGERS
-- ===========================================================================

-- Create a function to validate video data before insert/update
CREATE OR REPLACE FUNCTION validate_video_data() RETURNS TRIGGER AS $$
BEGIN
    -- Validate YouTube video ID vs title consistency
    IF NEW.url LIKE '%dQw4w9WgXcQ%' THEN
        IF NEW.title IS NOT NULL AND NEW.title NOT LIKE '%rick%' AND NEW.title NOT LIKE '%astley%' AND NEW.title NOT LIKE '%never%gonna%' THEN
            RAISE NOTICE 'Potential Rick Astley video corruption detected for item %', NEW.id;
            -- Log the issue but don't prevent the insert
            INSERT INTO video_validation_log (item_id, url, title, issue, created_at) 
            VALUES (NEW.id, NEW.url, NEW.title, 'rick_astley_title_mismatch', NOW());
        END IF;
    END IF;
    
    -- Set platform if missing based on URL
    IF NEW.platform IS NULL AND NEW.url IS NOT NULL THEN
        NEW.platform = CASE
            WHEN NEW.url LIKE '%youtube%' OR NEW.url LIKE '%youtu.be%' THEN 'youtube'
            WHEN NEW.url LIKE '%instagram%' THEN 'instagram'
            WHEN NEW.url LIKE '%tiktok%' THEN 'tiktok'
            WHEN NEW.url LIKE '%twitter%' OR NEW.url LIKE '%x.com%' THEN 'twitter'
            ELSE NEW.platform
        END;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create validation log table if it doesn't exist
CREATE TABLE IF NOT EXISTS video_validation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL,
    url TEXT,
    title TEXT,
    issue TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create trigger to validate video data
DROP TRIGGER IF EXISTS video_data_validation ON items;
CREATE TRIGGER video_data_validation
    BEFORE INSERT OR UPDATE ON items
    FOR EACH ROW
    WHEN (NEW.type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') OR NEW.url LIKE '%youtube%' OR NEW.platform IS NOT NULL)
    EXECUTE FUNCTION validate_video_data();

-- ===========================================================================
-- 9. AUTOMATED CLEANUP PROCEDURES
-- ===========================================================================

-- Procedure to clean up duplicate videos (run weekly)
CREATE OR REPLACE FUNCTION cleanup_duplicate_videos() RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Remove exact duplicates, keeping the oldest one
    WITH duplicates AS (
        SELECT id, 
               ROW_NUMBER() OVER (PARTITION BY url, title ORDER BY created_at ASC) as rn
        FROM items 
        WHERE url IS NOT NULL 
          AND (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
               OR url LIKE '%youtube%' 
               OR platform IS NOT NULL)
    )
    DELETE FROM items 
    WHERE id IN (SELECT id FROM duplicates WHERE rn > 1);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    INSERT INTO video_validation_log (item_id, url, title, issue, created_at)
    VALUES (NULL, NULL, NULL, format('cleanup_duplicates_removed_%s', deleted_count), NOW());
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ===========================================================================
-- 10. DAILY MONITORING QUERY (RUN THIS DAILY)
-- ===========================================================================

-- Comprehensive daily check - run this every day to catch issues early
SELECT 
    'DAILY VIDEO CORRUPTION REPORT' as report_type,
    (SELECT COUNT(*) FROM items WHERE DATE(created_at) = CURRENT_DATE AND (type IN ('video', 'youtube') OR url LIKE '%youtube%')) as videos_added_today,
    (SELECT COUNT(*) FROM items WHERE status = 'failed' AND DATE(updated_at) = CURRENT_DATE AND (type IN ('video', 'youtube') OR url LIKE '%youtube%')) as failures_today,
    (SELECT COUNT(*) FROM video_validation_log WHERE DATE(created_at) = CURRENT_DATE) as validation_issues_today,
    (SELECT COUNT(*) FROM items WHERE status IN ('processing', 'pending') AND updated_at < NOW() - INTERVAL '4 hours' AND (type IN ('video', 'youtube') OR url LIKE '%youtube%')) as stuck_processing_jobs,
    CURRENT_DATE as report_date;

-- To use these queries:
-- 1. Run the daily monitoring query every morning
-- 2. Check for title/URL mismatches weekly  
-- 3. Monitor stuck processing jobs hourly
-- 4. Run cleanup procedures weekly
-- 5. Review validation logs when issues are detected