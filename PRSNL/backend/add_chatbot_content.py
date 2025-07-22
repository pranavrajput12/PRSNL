#!/usr/bin/env python3
"""
Add real chatbot development content to the system
"""
import asyncio
import asyncpg
import os
from datetime import datetime
from uuid import uuid4
import json

from dotenv import load_dotenv

load_dotenv()

async def add_chatbot_content():
    """Add real content about chatbot development with AI IDEs"""
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Test user ID (from security bypass)
        user_id = "e03c9686-09b0-4a06-b236-d0839ac7f5df"
        
        print("=== Adding Real Chatbot Development Content ===\n")
        
        # 1. Website Links
        website_links = [
            {
                "url": "https://expertbeacon.com/how-to-create-chatbots-with-claude-ai-api/",
                "title": "How To Create Chatbots With Claude AI API: The 2024 Guide",
                "content_type": "tutorial",
                "summary": "Comprehensive guide on building chatbots with Claude AI API in 2024",
                "tags": ["claude", "chatbot", "api", "tutorial", "2024"]
            },
            {
                "url": "https://thehandydevelopersguide.com/2024/11/18/devtools-startup-ideas-build-an-ai-powered-chatbot-using-claude-and-react/",
                "title": "Build an AI-Powered Chatbot Using Claude And React",
                "content_type": "tutorial",
                "summary": "Step-by-step guide to building AI chatbots with Claude API and React framework",
                "tags": ["claude", "react", "chatbot", "javascript", "ai-ide"]
            },
            {
                "url": "https://medium.com/@lad.jai/windsurf-vs-cursor-the-battle-of-ai-powered-ides-in-2025-57d78729900c",
                "title": "Windsurf vs. Cursor: The Battle of AI-Powered IDEs in 2025",
                "content_type": "article",
                "summary": "Detailed comparison of Windsurf and Cursor IDEs for AI-powered development",
                "tags": ["windsurf", "cursor", "ai-ide", "comparison", "2025"]
            },
            {
                "url": "https://kingy.ai/blog/ai-coding-agents-in-2025-cursor-vs-windsurf-vs-copilot-vs-claude-vs-vs-code-ai/",
                "title": "AI Coding Agents in 2025: Cursor vs. Windsurf vs. Copilot vs. Claude",
                "content_type": "article",
                "summary": "Comprehensive comparison of AI coding assistants and IDEs for 2025",
                "tags": ["ai-ide", "cursor", "windsurf", "copilot", "claude", "comparison"]
            },
            {
                "url": "https://www.datacamp.com/tutorial/claude-sonnet-api-anthropic",
                "title": "Claude Sonnet 3.5 API Tutorial: Getting Started With Anthropic's API",
                "content_type": "tutorial",
                "summary": "Official tutorial for getting started with Claude Sonnet 3.5 API for building AI applications",
                "tags": ["claude", "api", "tutorial", "anthropic", "chatbot"]
            }
        ]
        
        # 2. YouTube Videos
        youtube_videos = [
            {
                "url": "https://www.youtube.com/watch?v=C_D8V9odBQ8",
                "title": "Windsurf IDE: NEW AI Editor - Cursor Alternative That's FREE & LOCAL!",
                "content_type": "video",
                "summary": "Video tutorial showcasing Windsurf IDE as a free alternative to Cursor for AI development",
                "tags": ["windsurf", "ai-ide", "tutorial", "video", "cursor-alternative"],
                "metadata": {
                    "platform": "youtube",
                    "video_id": "C_D8V9odBQ8",
                    "duration": "PT15M30S"
                }
            },
            {
                "url": "https://www.youtube.com/watch?v=WDJoiG-apkY",
                "title": "Windsurf IDE UPDATE: AI Editor with Autonomous Web Commands",
                "content_type": "video",
                "summary": "Updated tutorial on Windsurf IDE's autonomous features and web command capabilities",
                "tags": ["windsurf", "ai-ide", "autonomous", "tutorial", "video"],
                "metadata": {
                    "platform": "youtube",
                    "video_id": "WDJoiG-apkY",
                    "duration": "PT18M45S"
                }
            }
        ]
        
        # 3. Document/Guide
        document = {
            "url": "https://docs.anthropic.com/en/docs/build-with-claude",
            "title": "Build with Claude - Official Anthropic Documentation",
            "content_type": "document",
            "summary": "Official comprehensive guide from Anthropic on building applications with Claude, including chatbots",
            "tags": ["claude", "documentation", "official", "chatbot", "guide"],
            "raw_content": """# Building with Claude

## Getting Started
Claude is a powerful AI assistant that can help you build sophisticated applications, including chatbots. This guide covers everything you need to know.

## Key Concepts
- Messages API for conversational interfaces
- System prompts for behavior control
- Multi-turn conversation handling
- Context window management (200k tokens)

## Building a Chatbot
1. Set up your API key
2. Install the SDK (Python, JavaScript, or TypeScript)
3. Create a conversation loop
4. Handle user inputs and model responses
5. Implement error handling and rate limiting

## Best Practices
- Start development in the Workbench
- Use environment variables for API keys
- Implement proper error handling
- Monitor token usage
- Test with different prompts and edge cases"""
        }
        
        # 4. PDF reference (as a link since we can't create actual PDFs here)
        pdf_resource = {
            "url": "https://www.anthropic.com/claude-3-family.pdf",
            "title": "Claude 3 Model Family - Technical Overview",
            "content_type": "document",
            "summary": "Technical PDF detailing Claude 3 models (Haiku, Sonnet, Opus) capabilities for AI development",
            "tags": ["claude", "pdf", "technical", "model-family", "ai-development"],
            "metadata": {
                "file_type": "pdf",
                "document_type": "technical-paper"
            }
        }
        
        # Add all content to database
        all_content = website_links + youtube_videos + [document, pdf_resource]
        
        for idx, content in enumerate(all_content, 1):
            print(f"{idx}. Adding: {content['title'][:60]}...")
            
            # Prepare metadata
            metadata = content.get('metadata', {})
            metadata['tags'] = content.get('tags', [])
            metadata['source'] = 'manual_import'
            metadata['import_date'] = datetime.now().isoformat()
            
            # Determine type based on content_type
            item_type = content['content_type']
            if item_type == 'tutorial':
                item_type = 'article'
            elif item_type == 'document':
                item_type = 'document'
                
            # Insert item
            item_id = await conn.fetchval("""
                INSERT INTO items (
                    id, user_id, type, url, title, summary,
                    raw_content, status, content_type, metadata, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW()
                ) RETURNING id
            """, 
                uuid4(),
                user_id,
                item_type,
                content['url'],
                content['title'],
                content.get('summary'),
                content.get('raw_content'),
                'pending',  # Will be processed by capture engine
                content['content_type'],
                json.dumps(metadata)
            )
            
            print(f"   ✓ Added with ID: {item_id}")
            
        print(f"\n✓ Successfully added {len(all_content)} items!")
        print("\nThese items are now in 'pending' status.")
        print("The capture engine will process them to:")
        print("  - Fetch full content from URLs")
        print("  - Generate embeddings automatically")
        print("  - Enable knowledge base search")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_chatbot_content())