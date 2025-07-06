# Task Summary

## Task Description
Update the PRSNL frontend to connect to the live backend API instead of using sample data. The backend is running at http://localhost:8000.

## Changes Made
### Files Modified:
- `/PRSNL/frontend/src/lib/api.ts` - Updated API base URL and endpoints to match backend API

### Changes Details:
1. Set API base URL to `http://localhost:8000/api` (based on actual backend API structure)
2. Verified and updated API client methods to match backend endpoints:
   - Kept item creation endpoint as `/capture` (confirmed from API docs)
   - Kept timeline endpoint as `/timeline?page=${page}` (confirmed from API docs)
   - Changed tags endpoint from `/tags/recent` to `/tags`
   - Updated search endpoint to use `query` parameter instead of `q` (`/search?query={query}`)
3. Removed the `/v1` path segment as it's not used in the actual backend API

## Setup/Testing Instructions
1. Start the backend server:
   ```
   cd backend && uvicorn main:app --reload
   ```
2. Start the frontend development server:
   ```
   cd frontend && npm run dev
   ```
3. Test the integration by:
   - Checking if the homepage loads and shows real item count
   - Verifying search page connects to backend
   - Creating new items through the UI

## Notes
- No sample data imports were found in the API client file, so no removal was necessary
- All endpoints have been updated to match the backend API structure
- The API client error handling remains unchanged
