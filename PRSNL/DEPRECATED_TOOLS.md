# Deprecated Tools and Services

This document tracks all tools and services that have been removed from the PRSNL codebase to prevent accidental re-enablement.

## ⛔ PERMANENTLY REMOVED TOOLS

### 1. Vosk (Removed: Initial Phase 2 months ago, Re-removed: 2025-08-01)
- **What it was**: Offline speech recognition
- **Why removed**: Lower quality than whisper.cpp, "we were never supposed to use vosk"
- **Replacement**: whisper.cpp for offline transcription
- **DO NOT RE-ENABLE**: Even if mentioned in old docs

### 2. Haystack (Removed: Last week, 2025-07-25)
- **What it was**: RAG (Retrieval Augmented Generation) framework
- **Why removed**: Redundant with LangChain, which we already use
- **Replacement**: LangChain for all RAG functionality
- **DO NOT RE-ENABLE**: We use LangChain exclusively

### 3. whisper_only_transcription (Removed: 2025-08-01)
- **What it was**: Direct whisper transcription service
- **Why removed**: Replaced by hybrid transcription architecture
- **Replacement**: hybrid_transcription_service
- **DO NOT RE-ENABLE**: Use hybrid service instead

### 4. RAG API endpoints (Removed: 2025-08-01)
- **What it was**: /api/rag/* endpoints
- **Why removed**: Haystack-specific, not used
- **Replacement**: Use unified AI service endpoints
- **DO NOT RE-ENABLE**: No longer needed

## 🚨 IMPORTANT NOTES

1. **Documentation Cleanup Required**: Many docs still reference these tools
2. **Test Files**: Old test files may still import these services
3. **Requirements Files**: Multiple backup requirement files contain these dependencies
4. **Import Statements**: Check for unused imports in service files

## 📋 CLEANUP CHECKLIST

When removing a deprecated tool:
1. [ ] Remove from requirements.txt and all backup requirement files
2. [ ] Remove service files
3. [ ] Remove API endpoints
4. [ ] Remove from main.py router registrations
5. [ ] Remove from all documentation (README, CLAUDE.md, etc.)
6. [ ] Remove from test files
7. [ ] Remove from docker-compose.yml if applicable
8. [ ] Remove from environment files (.env examples)
9. [ ] Update this file with removal details

## 🔍 HOW TO CHECK FOR REFERENCES

```bash
# Check for Vosk references
grep -r "vosk\|Vosk\|VOSK" . --exclude-dir=.git --exclude="DEPRECATED_TOOLS.md"

# Check for Haystack references  
grep -r "haystack\|Haystack\|HAYSTACK" . --exclude-dir=.git --exclude="DEPRECATED_TOOLS.md"

# Check for whisper_only references
grep -r "whisper_only\|whisper-only" . --exclude-dir=.git --exclude="DEPRECATED_TOOLS.md"
```

## ⚠️ WARNING FOR AI ASSISTANTS

**DO NOT RE-ENABLE ANY OF THESE TOOLS** even if you see them mentioned in:
- Old documentation
- Backup requirement files
- Commented code
- Test files
- Migration scripts

Always check this file first before adding any dependencies or services.