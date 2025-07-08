# 🔧 PRSNL Fixes Needed

## 1. AI Suggestions Connection Reset Issue

### Problem
The `/api/ai/suggest` endpoint times out because:
- The httpx client in `ai_suggest.py` has a 10-second timeout (line 41)
- The LLM processor has a 60-second timeout
- When the LLM takes longer than 10 seconds, the connection is reset

### Fix
In `backend/app/api/ai_suggest.py`, change line 41:
```python
# OLD:
async with httpx.AsyncClient(timeout=10.0) as client:

# NEW:
async with httpx.AsyncClient(timeout=30.0) as client:
```

## 2. Image Extraction from Articles/Tweets

### Problem
The scraper only extracts text, stripping out all images because:
- Line 57 in `scraper.py` uses `get_text()` which removes all HTML tags
- No image URLs are extracted or stored
- The database has an `attachments` table ready but unused for article images

### Fix
Add image extraction to the scraper:

**Step 1: Update `backend/app/services/scraper.py`**

Add after line 57:
```python
# Extract image URLs before stripping HTML
images = []
for img in article_soup.find_all('img'):
    img_url = img.get('src') or img.get('data-src')
    if img_url:
        # Make absolute URL if relative
        if not img_url.startswith(('http://', 'https://')):
            from urllib.parse import urljoin
            img_url = urljoin(url, img_url)
        images.append({
            'url': img_url,
            'alt': img.get('alt', ''),
            'title': img.get('title', '')
        })
```

**Step 2: Update ScrapedData model** in `backend/app/services/scraper.py`:
```python
@dataclass
class ScrapedData:
    url: str
    title: Optional[str]
    content: Optional[str]
    html: Optional[str]
    author: Optional[str]
    published_date: Optional[datetime]
    scraped_at: datetime
    images: List[Dict[str, str]] = field(default_factory=list)  # Add this
```

**Step 3: Update the return statement** (around line 65):
```python
return ScrapedData(
    url=url,
    title=title,
    content=content,
    html=html,
    author=author,
    published_date=published_date,
    scraped_at=datetime.now(),
    images=images  # Add this
)
```

**Step 4: Update capture engine** to save images in the database:

In `backend/app/core/capture_engine.py`, after creating the item, add:
```python
# Save images as attachments
if scraped_data.images:
    for idx, img in enumerate(scraped_data.images[:5]):  # Limit to 5 images
        await db_connection.execute("""
            INSERT INTO attachments (item_id, file_type, file_path, mime_type, metadata)
            VALUES ($1, $2, $3, $4, $5)
        """, 
            item_id,
            'image',
            img['url'],  # Store URL as file_path
            'image/jpeg',  # Default, could be improved
            json.dumps({
                'alt': img['alt'],
                'title': img['title'],
                'is_remote': True,
                'index': idx
            })
        )
```

**Step 5: Update frontend** to display images:

In `frontend/src/lib/types/api.ts`, add to Item interface:
```typescript
interface Attachment {
  id: string;
  fileType: 'image' | 'video';
  filePath: string;
  mimeType: string;
  metadata?: {
    alt?: string;
    title?: string;
    isRemote?: boolean;
    index?: number;
  };
}

interface Item {
  // ... existing fields
  attachments?: Attachment[];
}
```

Then update the API to include attachments when fetching items.

### Alternative Quick Fix (Text-Only)
If you just want to include image descriptions in the content without storing URLs:

In `scraper.py`, replace line 57:
```python
# OLD:
content = article_soup.get_text(separator='\n', strip=True)

# NEW:
# Include image alt text in content
content_parts = []
for element in article_soup.descendants:
    if element.name == 'img':
        alt_text = element.get('alt', '')
        if alt_text:
            content_parts.append(f"[Image: {alt_text}]")
    elif element.string:
        content_parts.append(element.string.strip())
content = '\n'.join(filter(None, content_parts))
```

This would at least preserve image context in the text content.