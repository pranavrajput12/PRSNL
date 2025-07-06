# GEMINI TASKS - Backend/Infrastructure Specialist

## Current Context
The PRSNL project has just added Instagram video download support using yt-dlp. The video processing pipeline is implemented but needs optimization, testing, and infrastructure improvements. Videos are stored locally in the Docker container.

## Important Files to Review First
1. `/PRSNL/backend/app/services/video_processor.py` - Video download implementation
2. `/PRSNL/backend/app/api/capture.py` - Updated capture endpoint
3. `/PRSNL/backend/app/db/migrations/002_add_video_support.sql` - Video schema
4. `/PRSNL/docker-compose.yml` - Container configuration
5. `/SESSION_CONTINUITY.md` - Current project state

## Task 1: Video Processing Pipeline Optimization
**Priority**: HIGH  
**Task ID**: GEMINI-2025-07-06-001  
**Description**: Optimize video processing for performance and reliability

**Requirements**:
1. Add video format validation before download
2. Implement video compression for large files
3. Add progress tracking for video downloads
4. Implement retry logic for failed downloads
5. Add video metadata extraction (resolution, codec, bitrate)
6. Create background job queue for video processing

**Files to Modify**:
- `/PRSNL/backend/app/services/video_processor.py`
- `/PRSNL/backend/app/core/background_tasks.py` (create)
- `/PRSNL/backend/app/api/capture.py`

**Implementation Notes**:
```python
# Add to video_processor.py
- Video size limits (e.g., max 500MB)
- Format conversion to MP4 if needed
- Thumbnail generation at multiple sizes
- Progress callbacks for download status
```

## Task 2: Storage Management System
**Priority**: HIGH  
**Task ID**: GEMINI-2025-07-06-002  
**Description**: Implement robust storage management for media files

**Requirements**:
1. Create storage quota system per user (future-proofing)
2. Implement file cleanup for orphaned videos
3. Add storage metrics endpoint
4. Create backup strategy for media files
5. Implement CDN-ready file structure

**Files to Create/Modify**:
- `/PRSNL/backend/app/services/storage_manager.py` (create)
- `/PRSNL/backend/app/api/admin.py` (create admin endpoints)
- Update `/PRSNL/backend/app/config.py` with storage settings

**Storage Structure**:
```
/app/media/
├── videos/
│   ├── 2025/
│   │   ├── 01/
│   │   │   └── {uuid}.mp4
├── thumbnails/
│   ├── 2025/
│   │   ├── 01/
│   │   │   ├── {uuid}_small.jpg
│   │   │   ├── {uuid}_medium.jpg
│   │   │   └── {uuid}_large.jpg
└── temp/
    └── processing/
```

## Task 3: Video API Endpoints
**Priority**: MEDIUM  
**Task ID**: GEMINI-2025-07-06-003  
**Description**: Create dedicated video management endpoints

**Requirements**:
1. GET `/api/videos/{id}/stream` - Video streaming endpoint
2. GET `/api/videos/{id}/metadata` - Video metadata
3. POST `/api/videos/{id}/transcode` - Request different quality
4. DELETE `/api/videos/{id}` - Delete video and cleanup
5. GET `/api/storage/stats` - Storage usage statistics

**Files to Create/Modify**:
- `/PRSNL/backend/app/api/videos.py` (create)
- `/PRSNL/backend/app/models/video.py` (create Pydantic models)
- Update `/PRSNL/backend/app/main.py` to include new router

## Task 4: Platform Support Extension
**Priority**: MEDIUM  
**Task ID**: GEMINI-2025-07-06-004  
**Description**: Extend video support beyond Instagram

**Requirements**:
1. Add YouTube support (using yt-dlp)
2. Add Twitter/X video support
3. Add TikTok support
4. Create platform-specific processors
5. Implement platform detection service

**Files to Modify**:
- `/PRSNL/backend/app/services/video_processor.py`
- Create: `/PRSNL/backend/app/services/platforms/` directory
  - `instagram.py`
  - `youtube.py`
  - `twitter.py`
  - `tiktok.py`

## Task 5: Telegram Bot Integration
**Priority**: HIGH  
**Task ID**: GEMINI-2025-07-06-005  
**Description**: Implement Telegram bot for capturing links and videos

**Requirements**:
1. Create Telegram bot service
2. Add webhook endpoint for Telegram updates
3. Process text messages with URLs
4. Handle video/image messages
5. Integrate with existing capture engine
6. Add user authentication/whitelist

**Files to Create/Modify**:
- `/PRSNL/backend/app/services/telegram_bot.py` (create)
- `/PRSNL/backend/app/api/telegram.py` (create)
- `/PRSNL/backend/app/config.py` (add Telegram settings)
- `/PRSNL/backend/requirements.txt` (add python-telegram-bot)

**Implementation Guide**:
- See `/TELEGRAM_BOT_INTEGRATION.md` for detailed implementation
- This is 100% FREE - no API costs
- Can use polling for local dev, webhook for production

## Task 6: Performance Monitoring
**Priority**: LOW  
**Task ID**: GEMINI-2025-07-06-006  
**Description**: Add comprehensive monitoring for video operations

**Requirements**:
1. Add Prometheus metrics for video operations
2. Log download times and success rates
3. Monitor storage usage trends
4. Track video processing performance
5. Create health check for video service

**Files to Create/Modify**:
- `/PRSNL/backend/app/monitoring/metrics.py` (create)
- Update health check endpoint
- Add logging configuration

## Testing Requirements
- [ ] Test with videos > 100MB
- [ ] Test concurrent video downloads
- [ ] Test storage cleanup procedures
- [ ] Test video streaming performance
- [ ] Test error handling for invalid URLs
- [ ] Load test with 10+ simultaneous downloads

## Infrastructure Considerations
1. **Docker Volume**: Currently using local volume, consider named volumes
2. **Backup Strategy**: Implement automated backup for media files
3. **Scaling**: Prepare for horizontal scaling of video processors
4. **Caching**: Implement Redis for video metadata caching
5. **CDN Ready**: Structure files for easy CDN integration

## Notes
- Backend runs in Docker container
- Media files stored at `/app/media/` inside container
- Use PostgreSQL for metadata, filesystem for media
- Maintain high performance (sub-second response times)
- DO NOT use git commands directly - update MODEL_ACTIVITY_LOG.md instead

## Success Criteria
- Video processing is reliable and fast
- Storage is efficiently managed
- All platforms supported smoothly
- System scales with load
- Comprehensive monitoring in place