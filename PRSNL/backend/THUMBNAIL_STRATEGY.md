# PRSNL Thumbnail Strategy - Hybrid Approach

## Overview
We use a hybrid approach combining URL-based thumbnails for external content (YouTube) and file-based thumbnails for local/generated content.

## Current Implementation (2025-07-22)

### 1. YouTube Videos (URL-based)
- **Storage**: URLs stored in `thumbnail_url` column
- **Format**: `https://img.youtube.com/vi/{VIDEO_ID}/maxresdefault.jpg`
- **Extraction**: Parse video ID from YouTube URL
- **Benefits**:
  - No storage required
  - Always up-to-date
  - Multiple resolutions available (maxresdefault, hqdefault, mqdefault, sddefault)
  - Zero processing time

### 2. Local Videos (Future - File-based)
When implemented, will follow:
- **Storage**: `/app/media/thumbnails/{video_id}/`
- **Sizes**: small (320x180), medium (640x360), large (1280x720)
- **Generation**: Using ffmpeg at 5-second mark
- **Serving**: Via `/media/` static route

## Database Schema
```sql
-- Current implementation
items.thumbnail_url TEXT -- Stores YouTube URLs directly

-- Future enhancement for local files
items.thumbnail_path TEXT -- For local file paths
```

## Implementation Details

### YouTube Thumbnail Generation
```sql
-- Automatic thumbnail generation for YouTube videos
UPDATE items 
SET thumbnail_url = CONCAT(
  'https://img.youtube.com/vi/', 
  SUBSTRING(url FROM 'v=([A-Za-z0-9_-]+)'), 
  '/maxresdefault.jpg'
)
WHERE type IN ('video', 'youtube') 
  AND url LIKE '%youtube.com/watch?v=%';
```

### Frontend Usage
```svelte
{#if video.thumbnail_url}
  <img src={video.thumbnail_url} alt={video.title} />
{:else}
  <div class="thumbnail-placeholder">
    <Icon name="video" size="large" />
  </div>
{/if}
```

## Benefits of Hybrid Approach

### For YouTube/External Content:
- ✅ No storage costs
- ✅ No processing overhead
- ✅ Always available
- ✅ Multiple quality options

### For Local Content (When Implemented):
- ✅ Full control
- ✅ Custom thumbnails
- ✅ Works offline
- ✅ Privacy-preserving

## Future Enhancements

1. **Local Video Processing**
   - Implement ffmpeg thumbnail generation
   - Create multiple sizes for responsive display
   - Store in organized directory structure

2. **Custom Thumbnails**
   - Allow user uploads
   - AI-generated thumbnails
   - Frame selection UI

3. **Fallback Chain**
   - Try external URL first
   - Fall back to local file
   - Show placeholder if neither exists

## Migration Notes
- All existing YouTube videos have been updated with thumbnail URLs
- No file storage currently implemented
- Frontend already supports both approaches