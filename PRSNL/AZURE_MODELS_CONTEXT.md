# Azure OpenAI Models Context - PRSNL Project
*Created: 2025-01-08 by Claude*

## Current Situation
The user will provide Azure OpenAI model deployments to fix video processing and enable advanced features.

## Models Available
1. **gpt-4.1** - Main LLM with vision support ✅ (CONFIRMED WORKING)
   - Supports text generation
   - Supports vision/image analysis
   - Can extract text (OCR)
   - Can describe images
   - Can detect objects and generate tags

## Models Still Needed
1. **text-embedding-ada-002** - For semantic search and embeddings (CRITICAL)
2. **whisper** - For video transcription (IMPORTANT)

## Current Issues Due to Missing Models
1. Videos are failing to process (status: failed)
2. Semantic search not working
3. "Find Similar" feature disabled
4. Video transcription failing

## What's Been Fixed So Far
1. ✅ Made embeddings optional (won't fail video processing)
2. ✅ Fixed attachments table schema
3. ✅ Updated video library to use regular timeline API
4. ✅ Added mini-course messaging (needs 5+ videos)
5. ✅ Disabled problematic API routes temporarily

## Current State
- **Frontend**: Running on http://localhost:3002
- **Backend**: Running with core features only
- **Videos**: 6 videos manually marked as completed for testing
- **Video Library**: Now shows videos correctly
- **Mini-Courses**: UI ready, waiting for more videos

## Next Steps After Models Are Added
1. Test video capture with working embeddings
2. Re-enable video_streaming API routes
3. Test semantic search functionality
4. Test video transcription
5. Implement mini-course creation
6. Re-enable all advanced AI features

## Important Files
- `/backend/app/config.py` - Azure OpenAI configuration
- `/backend/.env` - Environment variables for API keys
- `/backend/app/services/embedding_service.py` - Embedding generation
- `/backend/app/services/transcription_service.py` - Video transcription

## Test Videos Added
Successfully added 5 YouTube videos through API for testing:
- Me at the zoo (First YouTube video)
- Uptown Funk - Mark Ronson
- Despacito - Luis Fonsi
- Sorry - Justin Bieber
- Shape of You - Ed Sheeran

## Agent Coordination
Working with:
- **Windsurf**: Frontend specialist (port 3002)
- **Gemini**: Backend specialist (port 8000)
- Coordination rules in MODEL_COORDINATION_RULES.md