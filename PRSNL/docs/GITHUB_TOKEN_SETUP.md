# 🔑 GitHub Token Setup for PRSNL Preview System

## 📋 Overview

The PRSNL system uses GitHub API to generate rich previews of GitHub repositories, including repository metadata and README content. To avoid rate limits and ensure consistent functionality, proper GitHub token authentication is required.

## 🎯 Why GitHub Token is Needed

### Without Token (Rate Limited):
- **60 requests per hour** from your IP address
- README content often fails to load
- Preview generation becomes unreliable
- Users see "GitHub API rate limit reached" messages

### With Token (Authenticated):
- **5000 requests per hour** per token
- Reliable README content fetching
- Consistent preview generation
- Full repository metadata access

## 🔧 Step-by-Step Setup

### 1. Create GitHub Personal Access Token

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click **"Generate new token"** > **"Generate new token (classic)"**
3. Configure the token:
   - **Note**: `PRSNL GitHub Preview System`
   - **Expiration**: 90 days (or "No expiration" if preferred)
   - **Scopes**: Select **`public_repo`** (read access to public repositories)

### 2. Configure Token in PRSNL

1. Copy the generated token (starts with `ghp_`)
2. Open `/Users/pronav/Personal Knowledge Base/PRSNL/backend/.env`
3. Update the `GITHUB_TOKEN` line:
   ```bash
   GITHUB_TOKEN=ghp_your_actual_token_here
   ```
4. Save the file

### 3. Restart Backend

```bash
# If running locally
cd "/Users/pronav/Personal Knowledge Base/PRSNL/backend"
# Stop current backend (Ctrl+C) and restart:
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# If running in Docker
docker-compose restart backend
```

### 4. Verify Setup

Test the GitHub preview system:

```bash
# Test GitHub API access
curl -H "Authorization: token ghp_your_token_here" https://api.github.com/rate_limit

# Expected response should show:
# "rate": { "limit": 5000, "remaining": 4999, "reset": ... }
```

## 🔄 Regenerating Existing Previews

If you've just added a token and want to update existing GitHub entries:

```bash
cd "/Users/pronav/Personal Knowledge Base/PRSNL/backend"
python3 regenerate_github_previews.py
```

This script will:
- Find all existing GitHub entries
- Regenerate previews with README content
- Update database with enhanced preview data
- Show progress and success/failure counts

## 🚨 Troubleshooting

### Issue: "GitHub API rate limit reached"
**Cause**: Token not configured or expired
**Solution**: 
1. Check if `GITHUB_TOKEN` in `.env` is correct
2. Verify token hasn't expired in GitHub settings
3. Restart backend after token changes

### Issue: README tabs not showing
**Cause**: Repository might not have README or token missing
**Solution**:
1. Verify repository actually has a README file
2. Check backend logs for API errors
3. Run regeneration script to update existing entries

### Issue: "Repository not found (404)"
**Cause**: Repository is private or doesn't exist
**Solution**:
1. Verify repository URL is correct and public
2. Private repositories require different token scopes

### Issue: Token validation fails
**Cause**: Invalid token or insufficient permissions
**Solution**:
1. Regenerate token with `public_repo` scope
2. Ensure token is correctly copied (no extra spaces)
3. Check GitHub token hasn't been revoked

## 📊 Monitoring Token Usage

### Check Rate Limit Status
```bash
curl -H "Authorization: token ghp_your_token_here" https://api.github.com/rate_limit
```

### Backend Logs
Monitor backend logs for GitHub API calls:
```bash
# Look for these log messages
tail -f backend.log | grep -i github
```

**Successful calls show:**
```
INFO - Successfully fetched README content (4695 characters)
INFO - 💾 Cached GitHub data for owner/repo
```

**Failed calls show:**
```
WARNING - GitHub API rate limit hit for README.md
ERROR - GitHub API returned status 403 for owner/repo
```

## 🔐 Security Best Practices

1. **Token Storage**: Keep tokens in `.env` files only (never commit to git)
2. **Scope Limitation**: Use minimal scopes needed (`public_repo` only)
3. **Regular Rotation**: Rotate tokens every 90 days
4. **Monitoring**: Watch for unusual API usage in GitHub settings

## 📈 Expected Performance

With proper token setup:
- **New GitHub URLs**: Instant preview generation with README
- **Existing entries**: Regeneration script updates 10-15 entries/minute
- **API calls**: ~3-5 calls per GitHub URL (repo + README + languages + commits)
- **Cache duration**: 1 hour for repository data, 6 hours for previews

## 🎯 Success Indicators

✅ **Working correctly when:**
- New GitHub URLs show both repository cards AND README tabs
- Existing GitHub entries display README content after regeneration
- Backend logs show successful GitHub API calls
- No rate limit error messages in frontend or logs

❌ **Need to troubleshoot when:**
- README tabs missing from GitHub previews
- "Rate limit reached" messages appear
- GitHub entries show only basic metadata
- 403/404 errors in backend logs

## 📞 Quick Recovery Commands

If GitHub previews break, run these commands:

```bash
# 1. Check backend status
curl http://localhost:8000/health

# 2. Verify token in environment
cd "/Users/pronav/Personal Knowledge Base/PRSNL/backend"
grep GITHUB_TOKEN .env

# 3. Test token directly
curl -H "Authorization: token $(grep GITHUB_TOKEN .env | cut -d= -f2)" https://api.github.com/rate_limit

# 4. Regenerate all previews
python3 regenerate_github_previews.py

# 5. Restart backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

*This documentation was created following the successful implementation of GitHub token authentication and preview enhancement on 2025-07-12.*