# 🤖 CLAUDE - Orchestration & Integration Tasks

## 📚 REQUIRED READING BEFORE ANY TASK
Always review these files before starting work:

### Documentation to Read First:
1. `/PRSNL/PROJECT_STATUS.md` - Current project state and context
2. `/PRSNL/MODEL_COORDINATION_RULES.md` - Coordination protocols
3. `/PRSNL/CONSOLIDATED_TASK_TRACKER.md` - Task history
4. `/PRSNL/API_DOCUMENTATION.md` - API contracts

### Files to Update After Each Task:
1. `/PRSNL/CONSOLIDATED_TASK_TRACKER.md` - Mark task complete
2. `/PRSNL/MODEL_ACTIVITY_LOG.md` - Log your changes
3. `/PRSNL/PROJECT_STATUS.md` - Update progress section

---

## 🆕 ACTIVE TASKS - 2025-07-07

### ✅ COMPLETED - iOS Share Extension Implementation
**Completed**: 2025-07-07
**Status**: DONE

Implemented full Share Extension functionality for PRSNL iOS app:
- ✅ URL sharing from Safari with JavaScript preprocessing
- ✅ Text selection sharing
- ✅ Image sharing support (new)
- ✅ Online/offline capture with fallback
- ✅ Tag management with recent tags
- ✅ App group configuration verified
- ✅ Created test plan documentation

Files modified:
- `PRSNLShareExtension/ShareViewModel.swift` - Added image handling
- `PRSNLShareExtension/ShareView.swift` - Added image preview
- `PRSNLShareExtension/Info.plist` - Added image support
- Created `SHARE_EXTENSION_TEST_PLAN.md`

### ✅ COMPLETED - iOS WebSocket Integration & Compliance Fixes
**Completed**: 2025-07-07
**Status**: DONE

Implemented WebSocket real-time features and fixed critical iOS compliance issues:
- ✅ WebSocketManager with auto-reconnect, message queuing, exponential backoff
- ✅ LiveTagService for real-time AI tag suggestions
- ✅ RealtimeUpdateService for cross-device sync
- ✅ Created Info.plist and PrivacyInfo.xcprivacy for App Store compliance
- ✅ Fixed memory leaks, race conditions, force unwrapping
- ✅ Added background URLSession configuration
- ✅ Created comprehensive compliance documentation

Files created/modified:
- `PRSNL/Core/Services/WebSocketManager.swift` - Complete implementation with fixes
- `PRSNL/Core/Services/LiveTagService.swift` - Tag suggestions service
- `PRSNL/Core/Services/RealtimeUpdateService.swift` - Real-time sync
- `PRSNL/Info.plist` - Main app configuration
- `PRSNL/PrivacyInfo.xcprivacy` - Privacy manifest
- `IOS_COMPLIANCE_ISSUES.md` - Detailed compliance report
- `WEBSOCKET_CODE_REVIEW.md` - Code review findings

### 🔧 KILOCODE TASKS - iOS Compliance Fixes
**Assigned**: 2025-07-07
**Priority**: CRITICAL

Tasks delegated to Kilocode for iOS compliance:

1. **Fix App Group Identifiers** (BLOCKER)
   - Standardize all to `group.ai.prsnl.shared`
   - Files: All `.entitlements` files
   - Widget uses wrong identifier: `group.com.prsnl.app`

2. **Fix Keychain Access Group** (BLOCKER)
   - Replace `$(AppIdentifierPrefix)` with actual Team ID
   - File: `PRSNL/Core/Services/KeychainService.swift:8`
   - Current: `"$(AppIdentifierPrefix)com.prsnl.shared"`
   - Need: `"TEAMID.com.prsnl.shared"`

3. **Core Data Threading Fixes**
   - Ensure all operations on proper contexts
   - Fix `localizedStandardContains` thread safety issue
   - File: `CoreDataManager.swift:371`

4. **Widget Battery Monitoring**
   - Replace UIDevice battery monitoring
   - File: `WidgetDataProvider.swift:636-806`
   - Won't work correctly in widget extension

5. **Create Xcode Project**
   - Set up proper project structure
   - Configure all build settings
   - Add all entitlements
   - Test on real device

## 🎯 Your Priority Tasks

### Task CLAUDE-001: End-to-End AI Integration Testing
**Priority**: CRITICAL
**Status**: TODO
**Estimated Time**: 2-3 hours

**Objective**: Verify all AI features work seamlessly together

**Test Scenarios**:
1. **Semantic Search Flow**
   - Add a new item via capture page
   - Wait for embedding generation
   - Search using semantic mode
   - Verify "Find Similar" functionality
   - Check relevance scores

2. **AI Suggestions Flow**
   - Navigate to capture page
   - Enter a URL (test with: https://x.com/cline/status/1939716967012946141)
   - Verify AI suggestions appear
   - Test Azure OpenAI integration

3. **Vision AI Processing**
   - Upload a screenshot/image
   - Verify OCR extraction
   - Check AI analysis results
   - Test metadata generation

4. **WebSocket Streaming**
   - Test live tag suggestions
   - Verify connection stability
   - Check reconnection logic
   - Test with multiple clients

5. **AI Insights Dashboard**
   - Load insights page
   - Verify analytics data loads
   - Test export functionality (PDF, CSV, JSON)
   - Check all visualizations render

**Files to Test**:
```
backend/
├── app/api/ai_suggest.py
├── app/api/vision.py
├── app/api/ws.py
├── app/services/ai_router.py
├── app/services/embedding_service.py
└── app/services/vision_processor.py

frontend/
├── src/routes/search/+page.svelte
├── src/routes/insights/+page.svelte
└── src/routes/capture/+page.svelte
```

### Task CLAUDE-002: Performance & Error Handling Audit
**Priority**: HIGH
**Status**: TODO

**Objectives**:
1. **Error Handling**
   - Verify graceful degradation when AI services fail
   - Test fallback mechanisms
   - Check error messages are user-friendly

2. **Performance Testing**
   - Measure embedding generation time
   - Check search response times
   - Monitor WebSocket latency
   - Verify batch processing efficiency

3. **Edge Cases**
   - Test with empty inputs
   - Very long text processing
   - Network interruptions
   - Service unavailability

### Task CLAUDE-003: Documentation Update
**Priority**: MEDIUM
**Status**: TODO

**Tasks**:
1. Update API_DOCUMENTATION.md with new endpoints
2. Create AI_FEATURES_GUIDE.md for users
3. Update deployment guide with AI service requirements
4. Document environment variables needed

### Task CLAUDE-004: Integration Verification
**Priority**: HIGH
**Status**: TODO

**Verify**:
1. All TypeScript types match backend responses
2. API error codes are properly handled
3. WebSocket reconnection works reliably
4. Caching strategies are effective

## 📝 Testing Checklist

### Before Starting Tests:
```bash
# Ensure all services are running
cd PRSNL/backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# In another terminal
cd PRSNL/frontend
npm run dev -- --port 3002


# Check PostgreSQL with pgvector
docker-compose up -d postgres
```

### Test Data Preparation:
1. Create test items with various content types
2. Generate embeddings for test data
3. Prepare test images for vision AI
4. Set up test URLs for capture

### Expected Outcomes:
- [ ] All AI features work without errors
- [ ] Fallback mechanisms activate when needed
- [ ] Performance meets acceptable thresholds
- [ ] Error messages are clear and helpful
- [ ] All integrations are stable

## 🔧 Tools & Commands

### Monitoring Commands:
```bash
# Check API health
curl http://localhost:8000/health

# Monitor WebSocket connections
curl http://localhost:8000/ws/status

# Check embedding service
curl -X POST http://localhost:8000/api/embeddings/test

# Verify AI router
curl http://localhost:8000/api/ai/status
```

### Debug Commands:
```bash
# View backend logs
tail -f PRSNL/backend/logs/app.log

# Check PostgreSQL embeddings
psql -U prsnl -d prsnl -c "SELECT COUNT(*) FROM items WHERE embedding IS NOT NULL;"

```

## 📋 Progress Tracking

Update this section as you complete tasks:

- [ ] CLAUDE-001: E2E Testing
  - [ ] Semantic search flow
  - [ ] AI suggestions flow
  - [ ] Vision AI processing
  - [ ] WebSocket streaming
  - [ ] AI insights dashboard

- [ ] CLAUDE-002: Performance Audit
  - [ ] Error handling verification
  - [ ] Performance benchmarks
  - [ ] Edge case testing

- [ ] CLAUDE-003: Documentation
  - [ ] API documentation
  - [ ] User guide
  - [ ] Deployment guide

- [ ] CLAUDE-004: Integration Verification
  - [ ] Type checking
  - [ ] Error handling
  - [ ] WebSocket stability
  - [ ] Caching verification

## 🚨 Issues to Report

Document any issues found:
1. Issue description
2. Steps to reproduce
3. Expected vs actual behavior
4. Suggested fix

## 🎯 Success Criteria

The testing phase is complete when:
1. All test scenarios pass without errors
2. Performance metrics are documented
3. Documentation is updated
4. No critical issues remain
5. Integration is stable across all services

Remember: Your thorough testing ensures PRSNL's AI features work flawlessly for users!