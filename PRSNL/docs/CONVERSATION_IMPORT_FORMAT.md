# AI Conversation Import Format Documentation

## Overview
This document defines the exact format for importing AI chat conversations from platforms like ChatGPT, Claude, Perplexity, and Bard into PRSNL's Neural Echo system.

## Import Endpoint
```
POST /api/conversations/import
Content-Type: application/json
```

## Request Format

### Root Object
```json
{
  "id": "unique-conversation-id",
  "title": "Conversation Title",
  "platform": "chatgpt",
  "source_url": "https://chat.openai.com/c/...",
  "timestamp": "2025-01-13T10:30:00Z",
  "tags": ["optional", "user", "tags"],
  "messages": [...]
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier from the extension (prevents duplicates) |
| `title` | string | Yes | Sanitized conversation title |
| `platform` | string | Yes | One of: `chatgpt`, `claude`, `perplexity`, `bard`, `gemini`, `other` |
| `source_url` | string | Yes | Original URL of the conversation |
| `timestamp` | string (ISO 8601) | Yes | When the conversation occurred |
| `tags` | string[] | No | Optional user-provided tags |
| `messages` | Message[] | Yes | Array of conversation messages (min 1) |

### Message Object
```json
{
  "id": "msg-001",
  "role": "user",
  "timestamp": "2025-01-13T10:30:00Z",
  "content": {
    "text": "Plain text content",
    "html": "<p>HTML content</p>",
    "markdown": "**Markdown** content"
  },
  "metadata": {}
}
```

### Message Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique message identifier |
| `role` | string | Yes | One of: `user`, `assistant`, `system` |
| `timestamp` | string (ISO 8601) | Yes | When the message was sent |
| `content` | Content | Yes | Message content in multiple formats |
| `metadata` | object | No | Platform-specific metadata |

### Content Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Plain text version (sanitized) |
| `html` | string | No | HTML version (sanitized with DOMPurify) |
| `markdown` | string | No | Markdown version (converted via Turndown) |

## Processing Pipeline

1. **Chrome Extension** extracts conversation from AI platform
2. **Content Script** uses platform-specific adapters to parse DOM
3. **ConversationProcessor** sanitizes and formats data
4. **Background Script** sends to PRSNL backend
5. **Backend** validates, stores, and triggers AI analysis

## Response Format

### Success Response
```json
{
  "id": "uuid",
  "platform": "chatgpt",
  "title": "Conversation Title",
  "slug": "conversation-title-202501",
  "permalink": "/conversations/chatgpt/conversation-title-202501",
  "message_count": 10,
  "neural_category": "learning",
  "neural_subcategory": "tutorial",
  "imported_at": "2025-01-13T12:00:00Z",
  "source_url": "https://chat.openai.com/c/..."
}
```

### Error Response
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## Validation Rules

1. **Conversation Level**
   - Must have at least 1 message
   - Maximum 1000 messages per conversation
   - Title must be 1-500 characters
   - Platform must be valid

2. **Message Level**
   - Role must be valid
   - Content must have text (can be empty string)
   - Timestamp must be valid ISO 8601

3. **Duplicate Prevention**
   - Combination of `platform` + `id` must be unique
   - Backend checks `extension_id` field to prevent re-imports

## AI Processing

After import, PRSNL's AI agent will analyze the conversation to extract:

1. **Summary** - Comprehensive summary of the entire conversation
2. **Key Topics** - Main subjects discussed
3. **Learning Points** - What the user learned
4. **User Journey** - How understanding evolved
5. **Knowledge Gaps** - Areas needing more exploration
6. **Neural Category** - Automatic categorization

## Example Request

```json
{
  "id": "chatgpt-12345",
  "title": "Learning React Hooks and State Management",
  "platform": "chatgpt",
  "source_url": "https://chat.openai.com/c/12345",
  "timestamp": "2025-01-13T10:30:00Z",
  "tags": ["react", "javascript", "frontend"],
  "messages": [
    {
      "id": "msg-001",
      "role": "user",
      "timestamp": "2025-01-13T10:30:00Z",
      "content": {
        "text": "Can you explain React hooks and how useState works?",
        "markdown": "Can you explain React hooks and how useState works?"
      }
    },
    {
      "id": "msg-002", 
      "role": "assistant",
      "timestamp": "2025-01-13T10:30:30Z",
      "content": {
        "text": "React Hooks are functions that let you use state...",
        "html": "<p>React Hooks are functions that let you use state...</p>",
        "markdown": "React Hooks are functions that let you use state..."
      }
    }
  ]
}
```

## Security Considerations

1. All content is sanitized using DOMPurify
2. HTML is converted to safe Markdown
3. XSS prevention at multiple levels
4. Size limits enforced
5. Rate limiting on import endpoint