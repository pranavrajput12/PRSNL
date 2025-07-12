# PRSNL Permalink System Testing Guide

This comprehensive guide covers testing the new permalink system implementation with detailed instructions and troubleshooting steps.

## Overview

The new permalink system implements a simplified URL structure:
- **Content URLs:** `/c/{category}/{slug}` (dev, learn, media, ideas)
- **Tool Pages:** `/p/{tool}` (timeline, insights, chat, visual, code)
- **System Pages:** `/s/{page}` (import, settings, docs)

## Quick Start

```bash
# Run all tests
./run_permalink_tests.sh

# Or run individual test components
cd backend && python test_permalink_migration.py
cd backend && python test_permalink_api.py
cd frontend && node test_permalink_routes.js
```

## Test Components

### 1. Migration Verification (`test_permalink_migration.py`)

Verifies that the database migration was successful and data integrity is maintained.

**What it tests:**
- Database table structure (content_urls, url_redirects)
- Migration completeness (how many items were migrated)
- Slug uniqueness and format validation
- Category classification accuracy
- Redirect configuration

**Running manually:**
```bash
cd backend
python test_permalink_migration.py
```

**Expected output:**
```
🔍 Starting permalink system verification...
📋 Verifying database structure...
✅ Database structure verification complete
📊 Verifying migration results...
📈 Migration stats:
   Total items: 150
   Migrated items: 143
   Items without URLs: 7
   Migration percentage: 95.3%
✅ All checks passed! The permalink system is working correctly.
```

### 2. API Testing (`test_permalink_api.py`)

Comprehensive testing of all new API endpoints with edge cases and error handling.

**What it tests:**
- Content retrieval endpoints (`/api/content/{category}/{slug}`)
- Category listing endpoints (`/api/content/category/{category}`)
- Legacy redirect endpoints (`/api/legacy-redirect/*`)
- Search and popular content endpoints
- Admin statistics endpoints
- Error handling and validation
- Performance and concurrent requests

**Running manually:**
```bash
cd backend
python test_permalink_api.py
```

**Expected output:**
```
🧪 Starting comprehensive API testing...
✅ API is available
📄 Testing content endpoints...
  ✅ GET /api/content/dev/sample-slug
  ✅ GET /api/content/invalid/slug
📁 Testing category endpoints...
  ✅ GET /api/content/category/dev
  ✅ GET /api/content/category/dev?page=1&limit=5
📊 All tests passed! The permalink API is working correctly.
```

### 3. Frontend Route Testing (`test_permalink_routes.js`)

Tests frontend routes, redirects, and user experience elements using Puppeteer.

**Prerequisites:**
```bash
cd frontend
npm install puppeteer --save-dev
```

**What it tests:**
- Content route loading (`/c/{category}`, `/c/{category}/{slug}`)
- Tool route functionality (`/p/{tool}`)
- System page accessibility (`/s/{page}`)
- Legacy redirect behavior
- Error page handling (404s)
- SEO meta tags and canonical URLs
- Mobile and desktop responsiveness

**Running manually:**
```bash
cd frontend
node test_permalink_routes.js
```

**Expected output:**
```
🚀 Starting Frontend Route Testing Suite
🔍 Testing frontend availability...
✅ Frontend is available
📄 Testing content routes...
  ✅ GET /c/dev
  ✅ GET /c/learn
🛠️ Testing tool routes...
  ✅ GET /p/timeline
  ✅ GET /p/insights
✅ All tests passed! The frontend routes are working correctly.
```

### 4. Admin Migration Tools (`admin_permalink_migration.py`)

Administrative tools for managing and fixing permalink system issues.

**Available commands:**
```bash
cd backend

# Migrate items that weren't included in initial migration
python admin_permalink_migration.py migrate-unmigrated --limit 50

# Fix duplicate slugs
python admin_permalink_migration.py fix-duplicates

# Regenerate slugs for a specific category
python admin_permalink_migration.py regenerate-category --category dev

# Create bulk redirects
python admin_permalink_migration.py create-redirects

# Validate all slugs
python admin_permalink_migration.py validate-slugs

# Get current statistics
python admin_permalink_migration.py stats
```

## System Requirements

### Backend Requirements
- Python 3.8+
- PostgreSQL 12+ with uuid-ossp extension
- All Python dependencies installed (`pip install -r requirements.txt`)
- Backend server running on `http://localhost:8000`

### Frontend Requirements (for frontend tests)
- Node.js 16+
- SvelteKit development server running on `http://localhost:5173`
- Puppeteer package (`npm install puppeteer --save-dev`)

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```
❌ Cannot connect to API: Connection refused
```

**Solution:**
- Verify PostgreSQL is running: `pg_ctl status`
- Check database credentials in `.env` file
- Ensure database exists and migrations have run
- Test connection: `psql $DATABASE_URL`

#### 2. Migration Issues
```
⚠️ Only 60.0% of items were migrated to new URL structure
```

**Causes and Solutions:**
- **Missing titles:** Items without titles can't generate slugs
  ```bash
  # Check for items with missing titles
  SELECT COUNT(*) FROM items WHERE title IS NULL OR title = '';
  
  # Fix by updating titles or excluding from migration
  UPDATE items SET title = 'Untitled Item ' || id::text WHERE title IS NULL;
  ```

- **Database constraints:** Check for foreign key or constraint violations
  ```bash
  # Run migration script to see detailed errors
  python admin_permalink_migration.py migrate-unmigrated --limit 10
  ```

#### 3. Duplicate Slug Errors
```
❌ Duplicate slug "example-slug" in category "dev" (3 instances)
```

**Solution:**
```bash
# Automatically fix duplicates
python admin_permalink_migration.py fix-duplicates

# Or manually check and fix
SELECT category, slug, COUNT(*) FROM content_urls 
GROUP BY category, slug HAVING COUNT(*) > 1;
```

#### 4. Frontend Route Failures
```
❌ GET /c/dev: Page shows error state
```

**Debugging steps:**
1. Check if backend API is responding: `curl http://localhost:8000/api/content/category/dev`
2. Inspect browser console for JavaScript errors
3. Verify SvelteKit server is running without errors
4. Test API connectivity from frontend

#### 5. Legacy Redirect Issues
```
❌ Broken redirect: /items/123 → /c/dev/non-existent-slug
```

**Solution:**
```bash
# Check for broken redirects
SELECT ur.old_path, ur.new_path
FROM url_redirects ur
WHERE ur.active = true
AND ur.new_path LIKE '/c/%'
AND NOT EXISTS (
    SELECT 1 FROM content_urls cu
    WHERE ur.new_path = '/c/' || cu.category || '/' || cu.slug
);

# Recreate redirects for all content
python admin_permalink_migration.py create-redirects
```

### Performance Issues

#### Slow API Responses
```
⚠️ 3 endpoints are slow (>5s)
```

**Optimization steps:**
1. Check database indexes:
   ```sql
   -- Ensure these indexes exist
   CREATE INDEX IF NOT EXISTS idx_content_urls_category_slug ON content_urls(category, slug);
   CREATE INDEX IF NOT EXISTS idx_content_urls_content_id ON content_urls(content_id);
   CREATE INDEX IF NOT EXISTS idx_content_urls_views ON content_urls(views DESC);
   ```

2. Monitor database query performance:
   ```sql
   -- Enable query logging
   ALTER SYSTEM SET log_statement = 'all';
   SELECT pg_reload_conf();
   ```

3. Check application logs for slow queries and optimize

## Manual Testing Scenarios

### 1. Content URL Flow
1. Navigate to `/c/dev` - should show development content
2. Click on a content item - should navigate to `/c/dev/{slug}`
3. Verify breadcrumbs and related content display
4. Check SEO meta tags in page source

### 2. Legacy Redirect Flow
1. Find an item ID from your database: `SELECT id FROM items LIMIT 1;`
2. Navigate to `/items/{id}` - should redirect to `/c/{category}/{slug}`
3. Check that redirect is permanent (301 status)
4. Verify content loads correctly after redirect

### 3. Error Handling
1. Navigate to `/c/invalid-category/slug` - should show 404
2. Navigate to `/c/dev/non-existent-slug` - should show 404
3. Verify error pages are user-friendly and include navigation

### 4. Search and Discovery
1. Test category filtering: `/c/dev?search=python`
2. Test sorting: `/c/dev?sort=popular`
3. Test pagination: `/c/dev?page=2&limit=10`
4. Verify popular content endpoint: `/api/content/popular`

## Validation Checklist

Before deploying the permalink system, ensure:

- [ ] **Database Migration**
  - [ ] All tables created successfully
  - [ ] Required indexes are present
  - [ ] >95% of items migrated
  - [ ] No duplicate slugs exist

- [ ] **API Endpoints**
  - [ ] All content endpoints respond correctly
  - [ ] Legacy redirects work for existing bookmarks
  - [ ] Error handling returns appropriate status codes
  - [ ] Performance is acceptable (<2s response times)

- [ ] **Frontend Routes**
  - [ ] All new routes load correctly
  - [ ] Legacy redirects work from frontend
  - [ ] Error pages display properly
  - [ ] SEO meta tags are generated correctly

- [ ] **Integration**
  - [ ] Backend and frontend communicate properly
  - [ ] Search and filtering work correctly
  - [ ] Navigation and breadcrumbs function
  - [ ] Mobile responsive design works

## Monitoring and Maintenance

### Ongoing Monitoring
1. **404 Errors:** Monitor for increased 404s that might indicate broken redirects
2. **Database Growth:** Watch content_urls table size and query performance
3. **Search Performance:** Monitor search response times as content grows
4. **Slug Conflicts:** Watch for duplicate slug generation

### Regular Maintenance
1. **Monthly:** Run validation script to check for data integrity issues
2. **Quarterly:** Review and clean up unused redirects
3. **As needed:** Re-categorize content if classification rules change
4. **Before major releases:** Run full test suite

## Getting Help

If you encounter issues not covered in this guide:

1. **Check logs:** Review backend logs for detailed error messages
2. **Run diagnostics:** Use the admin script to get current system statistics
3. **Test individually:** Run each test component separately to isolate issues
4. **Database inspection:** Query tables directly to understand data state

For persistent issues, gather:
- Test output and error messages
- Database statistics (`python admin_permalink_migration.py stats`)
- Server logs from the time of the issue
- Browser console errors (for frontend issues)

## Advanced Configuration

### Custom Categories
To add new categories, update:
1. `SmartSlugGenerator.VALID_CATEGORIES` in `backend/app/services/slug_generator.py`
2. Database constraint: `ALTER TABLE content_urls DROP CONSTRAINT valid_category;`
3. Frontend route handling in `frontend/src/routes/c/[category]/`

### Custom Slug Rules
Modify slug generation in `SmartSlugGenerator._generate_base_slug()`:
- Adjust stop words list
- Modify character replacement rules
- Change length limits or validation patterns

### Performance Tuning
For high-traffic deployments:
1. Add Redis caching for popular content queries
2. Implement database connection pooling
3. Add CDN for static assets and thumbnails
4. Consider read replicas for search-heavy workloads