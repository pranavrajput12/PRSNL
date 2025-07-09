# PRSNL Video System Technical Documentation

## Overview

The PRSNL video system implements a streaming-first architecture with metadata-only processing and download-on-demand functionality. This document provides detailed technical information about the implementation.

## Architecture

### Core Components

1. **Video Capture**: Metadata extraction without downloading
2. **Streaming Player**: Embedded video playback with fallback options
3. **Download Manager**: On-demand video downloading for offline viewing
4. **Metadata Storage**: JSONB-based metadata storage in PostgreSQL

### Data Flow

```
User URL → Video Detection → Metadata Extraction → Database Storage → Frontend Display
                                      ↓
                              AI Analysis → Enhanced Metadata
                                      ↓
                              Background Processing → Tags/Summary
```

## Backend Implementation

### Core Files

#### `/backend/app/api/capture.py`
- **Purpose**: Handles video capture and metadata processing
- **Key Functions**:
  - `process_video_metadata_only()`: Extracts video metadata without downloading
  - `process_video_item()`: Downloads video for offline viewing (on-demand)
- **Database Updates**: Stores metadata in `items.metadata->video_metadata`

#### `/backend/app/api/videos.py`
- **Purpose**: Video-specific API endpoints
- **Key Endpoints**:
  - `GET /videos/{id}/stream-url`: Returns streaming/embed URLs
  - `POST /videos/{id}/download`: Initiates video download
  - `GET /videos/{id}/metadata`: Returns video metadata
  - `GET /videos/{id}/stream`: Streams downloaded video files

#### `/backend/app/api/items.py`
- **Purpose**: General item retrieval with video metadata extraction
- **Key Features**:
  - Extracts platform from `metadata->'video_metadata'->'platform'`
  - Extracts thumbnails from `metadata->'video_metadata'->'thumbnail'`
  - Extracts duration from `metadata->'video_metadata'->'video_info'->'duration'`

#### `/backend/app/api/timeline.py`
- **Purpose**: Timeline/library view with video thumbnails
- **Key Features**:
  - Uses COALESCE for robust metadata extraction
  - Properly handles thumbnail URL transformations
  - Includes platform and duration information

### Database Schema

#### Items Table
```sql
CREATE TABLE items (
    id UUID PRIMARY KEY,
    title TEXT,
    url TEXT,
    summary TEXT,
    content TEXT,
    type TEXT,  -- 'video', 'article', 'bookmark'
    status TEXT,
    metadata JSONB,
    thumbnail_url TEXT,
    video_url TEXT,
    duration INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### Video Metadata Structure
```json
{
  "type": "video",
  "media_info": {
    "platform": "youtube",
    "embed_url": "https://www.youtube.com/embed/VIDEO_ID"
  },
  "video_metadata": {
    "platform": "youtube",
    "embed_url": "https://www.youtube.com/embed/VIDEO_ID",
    "streaming_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "downloaded": false,
    "video_info": {
      "title": "Video Title",
      "duration": 123,
      "thumbnail": "https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg",
      "platform": "youtube"
    },
    "ai_analysis": {
      "summary": "AI-generated summary",
      "tags": ["tag1", "tag2"],
      "key_points": ["point1", "point2"],
      "sentiment": "positive"
    }
  }
}
```

### API Endpoints

#### Video Stream URL
```
GET /api/videos/{id}/stream-url
```

**Response:**
```json
{
  "type": "streaming",
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "embed_url": "https://www.youtube.com/embed/VIDEO_ID"
}
```

#### Video Download
```
POST /api/videos/{id}/download
```

**Response:**
```json
{
  "message": "Video download started",
  "status": "download_started",
  "video_id": "uuid"
}
```

#### Video Metadata
```
GET /api/videos/{id}/metadata
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Video Title",
  "platform": "youtube",
  "duration": 123,
  "thumbnail_path": "https://...",
  "metadata": { ... }
}
```

## Frontend Implementation

### Core Components

#### `/frontend/src/lib/components/StreamingVideoPlayer.svelte`
- **Purpose**: Main video player component
- **Features**:
  - Handles both embedded and local video playback
  - Automatic platform detection
  - Loading states and error handling
  - Progressive enhancement

**Key Props:**
```typescript
export let videoId: string;
export let title: string = '';
export let thumbnail: string | undefined = undefined;
export let duration: number | undefined = undefined;
export let platform: string | undefined = undefined;
export let showControls: boolean = true;
```

**Video Loading Logic:**
```typescript
async function loadVideoData() {
  const response = await fetch(`/api/videos/${videoId}/stream-url`);
  const videoData = await response.json();
  
  if (videoData.type === 'local') {
    // Use local video file
    streamUrl = videoData.url;
    useEmbed = false;
  } else {
    // Use streaming/embed
    streamUrl = videoData.url;
    embedUrl = videoData.embed_url;
    useEmbed = platform === 'youtube' && embedUrl;
  }
}
```

#### Individual Video Pages
- **File**: `/frontend/src/routes/videos/[id]/+page.svelte`
- **Features**:
  - Video player integration
  - Download button functionality
  - Metadata display
  - Transcript and summary tabs

### Video Display Logic

#### YouTube Videos
1. **Thumbnail Display**: Shows YouTube thumbnail with play overlay
2. **Platform Badge**: Shows "YouTube" badge
3. **Duration**: Shows video duration
4. **Streaming Badge**: Shows "Streaming" indicator
5. **Embed Playback**: Uses iframe with YouTube embed URL

#### Downloaded Videos
1. **Local File**: Uses HTML5 video element
2. **Download Badge**: Shows "Downloaded" indicator
3. **Direct Playback**: No external dependencies

## Platform Support

### YouTube
- **Detection**: URL pattern matching
- **Metadata**: yt-dlp extraction
- **Thumbnails**: `https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg`
- **Embed**: `https://www.youtube.com/embed/VIDEO_ID`
- **Status**: ✅ Fully functional

### Vimeo
- **Detection**: URL pattern matching
- **Metadata**: yt-dlp extraction
- **Thumbnails**: Vimeo API
- **Embed**: `https://player.vimeo.com/video/VIDEO_ID`
- **Status**: 🔄 Prepared, needs testing

### Twitter
- **Detection**: URL pattern matching
- **Metadata**: yt-dlp extraction
- **Limitations**: Authentication may be required
- **Status**: 🔄 Prepared, needs testing

## Error Handling

### Backend Errors
1. **Video Not Found**: 404 HTTP error
2. **Metadata Extraction Failed**: Validation error
3. **Download Failure**: Background task error
4. **Invalid URL**: Validation error

### Frontend Errors
1. **Loading State**: Shows spinner during video data fetch
2. **Error State**: Shows error message with retry button
3. **Fallback**: Graceful degradation for unsupported videos

## Performance Considerations

### Metadata-Only Processing
- **Benefit**: Fast content capture without downloading
- **Implementation**: `process_video_metadata_only()` function
- **Storage**: Minimal database storage for metadata

### Streaming-First Approach
- **Benefit**: Immediate video access
- **Implementation**: Embed URLs for supported platforms
- **Fallback**: Direct URL streaming for unsupported platforms

### Download on Demand
- **Benefit**: Offline viewing when needed
- **Implementation**: Background task with progress tracking
- **Storage**: Local file system with database references

## Configuration

### Environment Variables
```bash
# Video processing
YOUTUBE_API_KEY=optional_youtube_api_key
VIMEO_API_KEY=optional_vimeo_api_key

# Storage
MEDIA_ROOT=/app/media
MAX_VIDEO_SIZE=500MB
```

### Database Configuration
```python
# PostgreSQL connection
DATABASE_URL=postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl

# JSONB settings
JSONB_METADATA_EXTRACTION=true
```

## Testing

### Unit Tests
- Video metadata extraction
- URL validation
- Database operations
- API endpoint responses

### Integration Tests
- End-to-end video capture
- Frontend video playback
- Download functionality
- Error scenarios

### Manual Testing
```bash
# Test video capture
curl -X POST "http://localhost:8000/api/capture" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "tags": ["test"]}'

# Test stream URL
curl "http://localhost:8000/api/videos/{id}/stream-url"

# Test download
curl -X POST "http://localhost:8000/api/videos/{id}/download"
```

## Troubleshooting

### Common Issues

#### Videos Not Playing
1. Check API endpoint responses
2. Verify metadata structure in database
3. Check browser console for errors
4. Verify embed URLs are valid

#### Thumbnails Not Showing
1. Check thumbnail URL extraction in SQL queries
2. Verify COALESCE logic in timeline.py
3. Check frontend image loading
4. Verify YouTube thumbnail URLs

#### Download Failures
1. Check yt-dlp installation
2. Verify ffmpeg availability
3. Check disk space
4. Monitor background task logs

### Debug Commands
```bash
# Check video metadata
psql "postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl" -c "
SELECT id, title, metadata->'video_metadata'->'platform' as platform
FROM items WHERE type = 'video';"

# Test API endpoints
curl -v "http://localhost:8000/api/videos/{id}/stream-url"

# Check logs
tail -f /var/log/prsnl/video_processing.log
```

## Future Enhancements

### Planned Features
1. **Video Chapters**: Support for video chapters and timestamps
2. **Quality Selection**: Multiple quality options for streaming
3. **Playlist Support**: YouTube playlist capture
4. **Live Streaming**: Support for live video content
5. **Advanced Analytics**: Video viewing statistics

### Technical Improvements
1. **Caching**: Redis caching for video metadata
2. **CDN Integration**: CDN for video delivery
3. **Transcoding**: Automatic video transcoding
4. **Backup Storage**: Cloud storage for video files
5. **API Rate Limiting**: Better rate limiting for video platforms

---

**Documentation Version**: 1.0
**Last Updated**: 2025-07-09
**Next Review**: After major system changes