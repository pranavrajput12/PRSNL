# WINDSURF TASKS - Frontend Specialist

## Current Context
The PRSNL project has just added Instagram video download support. The backend can now process videos, store them, and serve them to the frontend. A VideoPlayer component has been created but needs testing and potential enhancements.

## Important Files to Review First
1. `/PRSNL/frontend/src/lib/components/VideoPlayer.svelte` - New video player component
2. `/PRSNL/frontend/src/routes/timeline/+page.svelte` - Updated to display videos
3. `/PRSNL/backend/app/db/migrations/002_add_video_support.sql` - Database schema for videos
4. `/SESSION_CONTINUITY.md` - Current project state

## Task 1: Video Display Enhancement
**Priority**: HIGH  
**Task ID**: WINDSURF-2025-07-06-001  
**Description**: Enhance the video display experience in the timeline

**Requirements**:
1. Test VideoPlayer component with various video formats
2. Add loading states for video thumbnails
3. Implement lazy loading for videos in timeline
4. Add video duration overlay on thumbnails
5. Ensure responsive design works on mobile
6. Add keyboard shortcuts for video playback (space to play/pause)

**Files to Modify**:
- `/PRSNL/frontend/src/lib/components/VideoPlayer.svelte`
- `/PRSNL/frontend/src/routes/timeline/+page.svelte`
- Create: `/PRSNL/frontend/src/lib/stores/media.ts` (if needed)

## Task 2: Capture Page Video Support
**Priority**: HIGH  
**Task ID**: WINDSURF-2025-07-06-002  
**Description**: Update capture page to show video preview when Instagram URL is entered

**Requirements**:
1. Detect Instagram video URLs in capture form
2. Show video type indicator
3. Display estimated download time
4. Add video-specific capture options (quality selection if applicable)
5. Show preview thumbnail if available

**Files to Modify**:
- `/PRSNL/frontend/src/routes/capture/+page.svelte`
- `/PRSNL/frontend/src/lib/utils/url.ts` (create if needed)

## Task 3: Search Results Video Support
**Priority**: MEDIUM  
**Task ID**: WINDSURF-2025-07-06-003  
**Description**: Update search results to properly display video items

**Requirements**:
1. Add video type filter to search page
2. Show video duration in search results
3. Display platform icon (Instagram, YouTube, etc.)
4. Implement video preview on hover
5. Add "Play" button overlay on video thumbnails

**Files to Modify**:
- `/PRSNL/frontend/src/routes/search/+page.svelte`
- Update search filters UI

## Task 4: Performance Optimization
**Priority**: MEDIUM  
**Task ID**: WINDSURF-2025-07-06-004  
**Description**: Optimize frontend performance for video content

**Requirements**:
1. Implement virtual scrolling for timeline with videos
2. Add intersection observer for lazy video loading
3. Optimize thumbnail loading with progressive images
4. Add video preloading strategies
5. Monitor and log performance metrics

**Files to Review/Modify**:
- All pages displaying videos
- Consider using Svelte stores for video state management

## Testing Checklist
- [ ] Test with slow network (throttle to 3G)
- [ ] Test with multiple videos on same page
- [ ] Test responsive design on mobile devices
- [ ] Test keyboard navigation
- [ ] Test with videos of different sizes
- [ ] Test error states (failed video loads)

## Notes
- Frontend runs on port 3002 (not in Docker)
- Backend API is at http://localhost:8000
- Use the proxy configuration in vite.config.ts
- Maintain Manchester United red (#dc143c) theme
- DO NOT use git commands directly - update MODEL_ACTIVITY_LOG.md instead

## Success Criteria
- All video content displays smoothly
- No performance degradation with multiple videos
- Consistent UI/UX across all pages
- Mobile experience is excellent
- All keyboard shortcuts work