# 🔧 FusionAuth API Key Permission Fix

## The Issue
Your API key was created but doesn't have the necessary permissions. The "Super User" option wasn't visible in the UI.

## Solution Options

### Option 1: Edit the Existing API Key
1. Go to: http://localhost:9011/admin/api-key/
2. Find your "PRSNL Backend Integration" key
3. Click the **Edit** button (pencil icon)
4. Look for the **Endpoints** section
5. You should see:
   - A list of all API endpoints
   - Checkboxes for GET, POST, PUT, PATCH, DELETE methods
6. **Either**:
   - Check ALL boxes for full access
   - OR find a "Select All" option
   - OR look for any permission settings

### Option 2: Create a New API Key with Full Permissions
1. Go to: http://localhost:9011/admin/api-key/
2. Delete the existing key (optional)
3. Click **Add** (green + button)
4. Name: "PRSNL Full Access"
5. In the **Endpoints** section:
   - Look for a **"No endpoint restrictions"** option
   - OR manually select all endpoints
   - Make sure ALL HTTP methods are selected (GET, POST, PUT, PATCH, DELETE)
6. Save and copy the new key

### Option 3: Use the Default Kickstart Key (Temporary)
If there's a default API key that was created during setup, you might be able to use that temporarily.

## What to Look For in the UI

### Permissions Section
- **Endpoints**: Should list all available API endpoints
- **HTTP Methods**: GET, POST, PUT, PATCH, DELETE checkboxes
- **Tenant**: "All tenants" or specific tenant selection
- **Key Manager**: Toggle for key management permissions

### Common UI Patterns
- Some versions show a **"Super User"** checkbox
- Others show **"No restrictions"** option
- Some require manual selection of all endpoints

## Quick Test After Updating

Once you've updated permissions, test with:

```bash
curl -X GET "http://localhost:9011/api/user" \
  -H "Authorization: YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json"
```

A successful response will return JSON data instead of 401.

## If Still Having Issues

1. **Check FusionAuth Version**:
   - Different versions have different UI layouts
   - Go to System → About to see version

2. **Try the Master API Key**:
   - During initial setup, FusionAuth might have created a master key
   - Check Settings → System → API Keys

3. **Database Workaround** (Advanced):
   ```sql
   -- View existing keys
   SELECT key_value, permissions, meta_data 
   FROM authentication_keys 
   WHERE meta_data LIKE '%PRSNL%';
   ```

Let me know what you see in the Endpoints section!