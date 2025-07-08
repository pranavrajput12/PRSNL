# Entity Analysis - PRSNL Project

*Generated: 2025-01-08*

## 📊 Overview

This document maps all entities (nouns), roles, and relationships in the PRSNL codebase to identify gaps and opportunities for improvement.

## 🏗️ Core Entities

### 1. Item (Primary Entity)
**Database Table**: `items`
**Purpose**: Central content storage entity

**Attributes**:
- `id` (UUID) - Primary identifier
- `url` (TEXT) - Source URL (nullable for content-only items)
- `title` (TEXT) - Item title
- `summary` (TEXT) - AI-generated summary
- `raw_content` (TEXT) - Original content
- `processed_content` (TEXT) - Processed/cleaned content
- `status` (VARCHAR) - Processing status (pending/completed/failed/bookmark)
- `search_vector` (tsvector) - Full-text search index
- `metadata` (JSONB) - Flexible metadata storage
- `created_at` (TIMESTAMPTZ) - Creation timestamp
- `updated_at` (TIMESTAMPTZ) - Last update timestamp
- `accessed_at` (TIMESTAMPTZ) - Last access timestamp
- `access_count` (INTEGER) - Access frequency
- `embedding` (vector) - 1536-dimensional embedding
- `item_type` (VARCHAR) - Type of content (note/article/video/image)
- `platform` (VARCHAR) - Source platform
- `duration` (INTEGER) - Media duration in seconds
- `file_path` (TEXT) - Local file storage path
- `thumbnail_url` (TEXT) - Thumbnail image URL

**Relationships**:
- Has many Tags (through item_tags)
- May have Attachments
- May have Transcripts

### 2. Tag
**Database Table**: `tags`
**Purpose**: Content categorization

**Attributes**:
- `id` (UUID) - Primary identifier
- `name` (TEXT) - Tag name (unique)
- `created_at` (TIMESTAMPTZ) - Creation timestamp

**Relationships**:
- Belongs to many Items (through item_tags)

### 3. ItemTag (Junction Entity)
**Database Table**: `item_tags`
**Purpose**: Many-to-many relationship between Items and Tags

**Attributes**:
- `item_id` (UUID) - Foreign key to items
- `tag_id` (UUID) - Foreign key to tags
- `confidence` (FLOAT) - AI confidence score for auto-generated tags

## 🚸 User-Related Entities (MISSING)

### ❌ User Entity
**Status**: NOT IMPLEMENTED
**Impact**: No multi-user support, no personalization

**Proposed Attributes**:
- `id` (UUID)
- `email` (TEXT)
- `username` (TEXT)
- `password_hash` (TEXT)
- `created_at` (TIMESTAMPTZ)
- `last_login` (TIMESTAMPTZ)
- `preferences` (JSONB)
- `subscription_tier` (VARCHAR)

### ❌ Session Entity
**Status**: NOT IMPLEMENTED
**Impact**: No session management, no authentication

### ❌ Permission/Role Entity
**Status**: NOT IMPLEMENTED
**Impact**: No access control, no admin features

## 📎 Content-Related Entities (PARTIALLY MISSING)

### ❌ Attachment Entity
**Status**: REFERENCED BUT NOT IMPLEMENTED
**Database Table**: `attachments` (missing)
**Impact**: Cannot store multiple files per item

**Proposed Attributes**:
- `id` (UUID)
- `item_id` (UUID) - Foreign key to items
- `file_path` (TEXT)
- `file_type` (VARCHAR)
- `file_size` (INTEGER)
- `created_at` (TIMESTAMPTZ)

### ❌ Transcript Entity
**Status**: PARTIALLY IMPLEMENTED (stored in metadata)
**Impact**: No structured transcript storage

**Proposed Attributes**:
- `id` (UUID)
- `item_id` (UUID) - Foreign key to items
- `content` (TEXT)
- `language` (VARCHAR)
- `confidence` (FLOAT)
- `created_at` (TIMESTAMPTZ)

### ❌ Collection/Folder Entity
**Status**: NOT IMPLEMENTED
**Impact**: No way to organize items into groups

**Proposed Attributes**:
- `id` (UUID)
- `name` (TEXT)
- `description` (TEXT)
- `user_id` (UUID)
- `parent_id` (UUID) - For nested collections
- `created_at` (TIMESTAMPTZ)

## 🤖 AI/Processing Entities (PARTIALLY MISSING)

### ❌ Job/Task Entity
**Status**: REFERENCED BUT NOT IMPLEMENTED
**Impact**: No background job tracking

**Proposed Attributes**:
- `id` (UUID)
- `type` (VARCHAR) - Job type (transcription/summarization/etc)
- `status` (VARCHAR) - pending/processing/completed/failed
- `item_id` (UUID) - Related item
- `started_at` (TIMESTAMPTZ)
- `completed_at` (TIMESTAMPTZ)
- `error_message` (TEXT)
- `retry_count` (INTEGER)

### ❌ AIModel Entity
**Status**: NOT IMPLEMENTED
**Impact**: No tracking of which AI model was used

**Proposed Attributes**:
- `id` (UUID)
- `name` (VARCHAR)
- `provider` (VARCHAR) - Azure/OpenAI/etc
- `version` (VARCHAR)
- `capabilities` (JSONB)

### ❌ AIInteraction Entity
**Status**: NOT IMPLEMENTED
**Impact**: No audit trail of AI usage

**Proposed Attributes**:
- `id` (UUID)
- `item_id` (UUID)
- `model_id` (UUID)
- `interaction_type` (VARCHAR)
- `tokens_used` (INTEGER)
- `cost` (DECIMAL)
- `created_at` (TIMESTAMPTZ)

## 📊 Analytics Entities (MISSING)

### ❌ SearchQuery Entity
**Status**: NOT IMPLEMENTED
**Impact**: No search analytics

**Proposed Attributes**:
- `id` (UUID)
- `user_id` (UUID)
- `query` (TEXT)
- `results_count` (INTEGER)
- `clicked_item_id` (UUID)
- `created_at` (TIMESTAMPTZ)

### ❌ ItemView Entity
**Status**: NOT IMPLEMENTED
**Impact**: Limited analytics (only access_count)

**Proposed Attributes**:
- `id` (UUID)
- `item_id` (UUID)
- `user_id` (UUID)
- `duration` (INTEGER) - Time spent
- `viewed_at` (TIMESTAMPTZ)

## 🔔 Communication Entities (MISSING)

### ❌ Notification Entity
**Status**: NOT IMPLEMENTED
**Impact**: No notification system

### ❌ Webhook Entity
**Status**: NOT IMPLEMENTED
**Impact**: No external integrations

## 💼 Business Logic Entities (MISSING)

### ❌ Subscription Entity
**Status**: NOT IMPLEMENTED
**Impact**: No premium features management

### ❌ Invoice/Payment Entity
**Status**: NOT IMPLEMENTED
**Impact**: No billing support

## 🔐 Security Entities (MISSING)

### ❌ APIKey Entity
**Status**: NOT IMPLEMENTED
**Impact**: No API access management

### ❌ AuditLog Entity
**Status**: NOT IMPLEMENTED
**Impact**: No security audit trail

## 📋 Summary of Gaps

### Critical Missing Entities:
1. **User Management**: No User, Session, or Role entities
2. **File Management**: Attachment table referenced but not created
3. **Job Management**: Background job tracking not implemented
4. **Analytics**: No detailed usage tracking
5. **Security**: No audit logging or API key management

### Partial Implementations:
1. **Transcripts**: Stored in metadata instead of dedicated table
2. **AI Interactions**: No tracking of AI usage/costs
3. **Search Analytics**: Basic search but no analytics

### Design Limitations:
1. **Single-tenant**: No multi-user support
2. **Flat Structure**: No collections/folders for organization
3. **Limited Relationships**: Only Items-Tags relationship exists
4. **No Versioning**: No content version history

## 🎯 Recommendations

### Phase 1 - Critical (Immediate):
1. Create `attachments` table (already referenced in code)
2. Implement basic User entity for future multi-user support
3. Add Job/Task tracking for background processing

### Phase 2 - Important (Short-term):
1. Add Collections/Folders for organization
2. Implement proper Transcript entity
3. Add basic analytics entities

### Phase 3 - Enhancement (Long-term):
1. Full user management with roles/permissions
2. AI usage tracking and cost management
3. Audit logging and security features
4. Subscription/billing support

## 🔄 Entity Relationships Diagram

```
Items (1) ----< (N) ItemTags (N) >---- (1) Tags
  |
  |--< Attachments (planned)
  |--< Transcripts (planned)
  |--< ItemViews (planned)
  |
Users (planned) --< Collections (planned) --< CollectionItems (planned)
  |
  |--< Sessions (planned)
  |--< SearchQueries (planned)
  |--< APIKeys (planned)
```

## 📝 Notes

1. The current schema is optimized for single-user personal knowledge management
2. PostgreSQL extensions (vector, uuid-ossp) are properly utilized
3. Full-text search is well-implemented with tsvector
4. JSONB metadata provides flexibility but lacks structure
5. The codebase references several entities that don't exist in the database