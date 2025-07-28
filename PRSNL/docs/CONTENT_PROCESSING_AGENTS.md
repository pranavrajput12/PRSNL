# PRSNL Content Processing Agents

This document describes the CrewAI agents designed for enhanced content processing in PRSNL, focusing on extracting actionable knowledge and cleaning scraped content.

## Overview

PRSNL uses two specialized CrewAI agents to enhance content processing:

1. **Actionable Insights Agent** - Extracts practical, actionable knowledge from content
2. **Content Cleaner Agent** - Cleans and structures scraped web content

## Actionable Insights Extraction Agent

### Purpose
The Actionable Insights Agent specializes in identifying and extracting actionable information from content, making it easy for chatbots and voice assistants to provide practical guidance to users.

### Location
`/backend/app/agents/content/actionable_insights_agent.py`

### Features
- Extracts step-by-step instructions
- Identifies practical tips and tricks
- Finds methods and techniques
- Highlights key takeaways
- Categorizes insights by importance (high/medium/low)
- Provides context for each insight
- Generates voice-friendly summaries

### Insight Categories

#### 1. Tips
- Practical advice and best practices
- Quick wins and time-savers
- Warnings about common mistakes
- Pro tips and expert advice

#### 2. Steps
- Sequential instructions or procedures
- How-to guides
- Setup instructions
- Process workflows

#### 3. Methods
- Techniques, approaches, or strategies
- Problem-solving techniques
- Methodologies and frameworks
- Alternative approaches

#### 4. Takeaways
- Key learnings and important points
- Core concepts to remember
- Important facts or findings
- Summary points

### Usage Example

```python
from app.agents.content.actionable_insights_agent import ActionableInsightsAgent

# Create agent instance
insights_agent = ActionableInsightsAgent()

# Extract insights from content
insights = await insights_agent.extract_insights(
    content="Your content here...",
    content_type="tutorial",
    url="https://example.com/tutorial",
    title="Python Best Practices",
    focus_areas=["performance", "security"]
)

# Access categorized insights
tips = insights.tips  # List of ActionableInsight objects
steps = insights.steps
methods = insights.methods
takeaways = insights.takeaways

# Generate voice-friendly summary
voice_summary = await insights_agent.generate_voice_friendly_summary(
    insights=insights,
    max_length=300
)
```

### Output Format

```json
{
  "tips": [
    {
      "type": "tip",
      "content": "Use list comprehensions for better performance",
      "context": "When working with large datasets",
      "importance": "high"
    }
  ],
  "steps": [
    {
      "type": "step", 
      "content": "Install required dependencies using pip",
      "context": "Initial setup",
      "importance": "high"
    }
  ],
  "methods": [
    {
      "type": "method",
      "content": "Apply the decorator pattern for extending functionality",
      "context": "Design patterns",
      "importance": "medium"
    }
  ],
  "takeaways": [
    {
      "type": "takeaway",
      "content": "Always validate user input to prevent security vulnerabilities",
      "context": "Security best practices",
      "importance": "high"
    }
  ],
  "summary": "Comprehensive summary of the most actionable insights",
  "total_insights": 15
}
```

## Content Cleaner Agent

### Purpose
The Content Cleaner Agent removes redundant elements from scraped web content while preserving semantic meaning and improving readability.

### Location
`/backend/app/agents/content/content_cleaner_agent.py`

### Features
- Removes advertisements and navigation elements
- Eliminates newsletter signup prompts
- Strips social media sharing buttons
- Preserves code blocks and important tables
- Maintains document structure with headings
- Improves spacing and formatting
- Provides cleaning statistics

### Cleaning Process

1. **HTML Analysis** - Detects and parses HTML content
2. **Element Removal** - Removes unwanted elements by class/id patterns
3. **Content Preservation** - Protects code blocks, tables, and quotes
4. **Structure Extraction** - Maintains heading hierarchy
5. **Text Cleaning** - Removes boilerplate patterns
6. **AI Enhancement** - Optional intelligent cleaning for complex content
7. **Formatting** - Applies consistent spacing and structure

### Usage Example

```python
from app.agents.content.content_cleaner_agent import ContentCleanerAgent

# Create agent instance
cleaner_agent = ContentCleanerAgent()

# Clean content
cleaned = await cleaner_agent.clean_content(
    content=raw_html_content,
    content_type="article",
    preserve_structure=True,
    aggressive_cleaning=False
)

# Access cleaned content and metadata
clean_content = cleaned.content
sections = cleaned.sections  # Extracted sections with headings
stats = cleaned.cleaning_stats  # Cleaning statistics
```

### Output Format

```json
{
  "content": "Cleaned and formatted content...",
  "title": "Extracted title if available",
  "sections": [
    {
      "level": 2,
      "title": "Introduction",
      "content": "Section content...",
      "line_start": 0
    }
  ],
  "metadata": {
    "content_type": "article",
    "is_html": true,
    "preserve_structure": true,
    "aggressive_cleaning": false
  },
  "cleaning_stats": {
    "original_length": 15000,
    "final_length": 8000,
    "reduction_percent": 46.67,
    "removed_elements": 25,
    "preserved_blocks": 5,
    "sections_created": 8
  }
}
```

### Cleaning Options

- **preserve_structure**: Maintains heading hierarchy and document structure
- **aggressive_cleaning**: Removes more elements that might be content
- **content_type**: Optimizes cleaning for specific content types (article, documentation, tutorial)

## Integration with PRSNL

### Content Processing Pipeline

1. **Scraping** - SmartScraper fetches raw content
2. **Cleaning** - Content Cleaner Agent removes redundant elements
3. **Analysis** - LLM processes cleaned content
4. **Insights Extraction** - Actionable Insights Agent extracts practical knowledge
5. **Storage** - Clean content and insights stored in database

### Unified AI Service Integration

The agents are integrated into the UnifiedAIService with these methods:

```python
# Extract actionable insights
insights = await unified_ai_service.extract_actionable_insights(
    content=content,
    content_type="tutorial",
    url=url,
    title=title,
    focus_areas=["setup", "configuration"]
)

# Clean content
cleaned = await unified_ai_service.clean_content(
    content=raw_content,
    content_type="article",
    preserve_structure=True,
    aggressive_cleaning=False
)

# Generate actionable summary
summary = await unified_ai_service.generate_actionable_summary(
    content=content,
    content_type="article",
    max_length=300
)
```

### Frontend Display

Actionable insights are displayed in dedicated sections:

1. **Article Template** (`/article/[id]`) - Full insights display with categories
2. **Bookmark Template** (`/bookmark/[id]`) - Compact insights in content view
3. **Timeline View** - Actionable summaries in item cards

## Benefits

### For Users
- **Practical Knowledge** - Focus on what can be applied immediately
- **Clear Structure** - Organized by actionability type
- **Quick Reference** - Easy to scan and find specific information
- **Voice Ready** - Optimized for conversational interfaces

### For System
- **Consistent Processing** - Standardized content handling
- **Better Quality** - Cleaner content for all features
- **Reduced Storage** - Smaller, cleaner content
- **Enhanced Search** - Better structured data for searching

## Configuration

### Environment Variables
No additional environment variables required. Uses existing Azure OpenAI configuration.

### Agent Parameters

#### Actionable Insights Agent
- `max_iter`: 5 (default) - Maximum iterations for processing
- `temperature`: 0.2 - Low temperature for consistent extraction
- `verbose`: True - Detailed logging

#### Content Cleaner Agent
- `removal_patterns`: Customizable patterns for element removal
- `preserve_patterns`: Patterns for content to always keep
- `batch_size`: 10 - For bulk processing

## Future Enhancements

1. **Domain-Specific Insights** - Specialized extraction for technical domains
2. **Multi-Language Support** - Extract insights in multiple languages
3. **Custom Insight Types** - User-defined insight categories
4. **Learning from Feedback** - Improve extraction based on user interactions
5. **Real-time Processing** - Stream insights as content is processed
6. **Integration with Voice** - Direct voice synthesis of insights