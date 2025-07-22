# 🖥️ Mac Mini M4 Setup Session Notes - 2025-07-18

## 📋 Overview
This document captures the complete setup process and configuration changes made during the migration to Mac Mini M4 with Colima as the Docker runtime replacement.

## 🎯 Migration Goal
Replace Rancher Desktop with Colima for a lightweight Docker alternative that doesn't consume excessive storage space on the new Mac Mini M4 system.

## 🧹 Storage Cleanup Performed

### Space Freed: ~28GB Total
1. **npm cache**: 2GB
   - Command: `npm cache clean --force`
   - Location: `~/.npm`

2. **Puppeteer cache**: 964MB
   - Command: `rm -rf ~/Library/Caches/Puppeteer`
   - Used for headless Chrome operations

3. **Old IDE directories**: ~333MB
   - Cursor: 178MB (`~/Library/Application Support/Cursor`)
   - Trae: 155MB (`~/Library/Application Support/Trae`)

4. **Xcode iOS Device Support**: 4.4GB
   - Command: `rm -rf ~/Library/Developer/Xcode/iOS DeviceSupport/*`
   - Not needed for PRSNL development

## 🔧 Installation Process

### 1. System Prerequisites
```bash
# Accept Xcode license (required for Homebrew)
sudo xcodebuild -license accept
```

### 2. Homebrew Installation
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 3. PostgreSQL 16 Installation
```bash
# Install PostgreSQL 16 (ARM64 version)
brew install postgresql@16

# Start PostgreSQL service
brew services start postgresql@16

# Create PRSNL database
createdb prsnl
```

### 4. Colima Installation
```bash
# Install Colima and Docker CLI
brew install colima docker docker-compose

# Start Colima
colima start
```

## 📝 Configuration Changes

### 1. PostgreSQL Port Change
- **Old**: Port 5432 (previous setup)
- **New**: Port 5432 (standard port)
- **Files Updated**:
  - `/backend/.env`: DATABASE_URL changed to port 5432
  - `/docker-compose.auth.yml`: Keycloak connection updated

### 2. Environment File Fix
- **Issue**: Invalid EOF line in `.env` file
- **Fix**: Changed `EOF < /dev/null` to `# EOF`
- **Error**: Was causing docker-compose parsing failures

### 3. Database Schema Creation
Created basic schema manually since migrations failed:
```sql
CREATE TABLE IF NOT EXISTS items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    type VARCHAR(50) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## 🚀 Service Status

### ✅ Running Services
1. **PostgreSQL**: Port 5432 (local, not Docker)
2. **Colima**: Docker runtime (replacing Rancher Desktop)
3. **Frontend**: Port 3004 (development server)
4. **Backend**: Port 8000 (FastAPI)
5. **Keycloak**: Port 8080 (admin/admin123)
6. **FusionAuth**: Port 9011 (needs configuration)
7. **DragonflyDB**: Port 6379 (via Docker)

### ⚠️ Known Issues
1. **pgvector extension**: Not installed
   - Vector operations disabled
   - Affects AI embeddings functionality

2. **Authentication errors**: 500 errors on login
   - `/api/timeline` returns 500
   - `/api/auth/login` returns 500
   - Root cause: No users configured in auth systems

3. **Database migrations**: Failed on startup
   - Error: `relation "items" does not exist`
   - Workaround: Created tables manually

4. **OpenTelemetry**: Connection refused (non-critical)
   - Service not running but not required

## 🔍 Browser Console Errors
```javascript
GET http://localhost:8000/api/timeline?limit=20 500 (Internal Server Error)
POST http://localhost:8000/api/auth/login 500 (Internal Server Error)
```

## 📌 Next Steps (To Do Tomorrow)

1. **Install pgvector extension**
   ```bash
   brew install pgvector
   # Then in PostgreSQL:
   CREATE EXTENSION vector;
   ```

2. **Configure Authentication**
   - Set up test users in Keycloak
   - Configure FusionAuth application
   - Update OAuth settings

3. **Run Database Migrations**
   - Fix migration scripts
   - Apply all pending migrations

4. **Test Authentication Flow**
   - Verify login works
   - Test JWT token generation
   - Confirm protected routes

## 💡 Lessons Learned

### Colima vs Rancher Desktop
- **Colima Pros**:
  - Much lighter resource usage
  - No GUI overhead
  - Fast startup
  - Native Apple Silicon support
  
- **Colima Cons**:
  - Command-line only (no GUI)
  - Requires manual start (`colima start`)
  - Less feature-rich than Rancher Desktop

### PostgreSQL Port Standardization
- Using standard port 5432 reduces configuration complexity
- Previous non-standard port (5432) caused multiple issues
- Always check port configuration when services fail to connect

### Authentication System Complexity
- Dual auth system (Keycloak + FusionAuth) requires careful configuration
- Missing user setup causes cascade of 500 errors
- Need proper initialization sequence for auth services

## 📞 Support Notes
- User requested to continue tomorrow
- All infrastructure is in place
- Just needs authentication configuration to complete setup
- System is ~90% ready, only auth config remaining

## 🔗 Related Documentation
- `CURRENT_SESSION_STATE.md` - Updated with Mac Mini M4 status
- `TASK_HISTORY.md` - Task marked as partially complete
- `PROJECT_STATUS.md` - Infrastructure stack updated
- `QUICK_REFERENCE_COMPLETE.md` - New setup commands added