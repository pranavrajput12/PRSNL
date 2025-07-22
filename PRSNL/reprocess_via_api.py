#!/usr/bin/env python3
"""
Reprocess bookmarks by calling the actual backend API
"""
import requests
import time

def reprocess_bookmarks():
    """Trigger reprocessing via the backend API"""
    
    # First get all bookmarks
    response = requests.get("http://localhost:8000/api/timeline?limit=50")
    if response.status_code != 200:
        print(f"Failed to get timeline: {response.status_code}")
        return
    
    items = response.json().get('items', [])
    bookmarks = [item for item in items if item.get('type') == 'bookmark']
    
    print(f"Found {len(bookmarks)} bookmarks")
    
    # For each bookmark, trigger capture if it has no real content
    success = 0
    failed = 0
    
    for bookmark in bookmarks:
        # Check if it has real content (not just placeholder)
        if bookmark.get('summary', '').startswith('Saved bookmark for'):
            print(f"\nReprocessing: {bookmark['title'][:60]}...")
            
            # Call the capture endpoint
            try:
                capture_response = requests.post(
                    "http://localhost:8000/api/capture",
                    json={
                        "url": bookmark['url'],
                        "enable_summarization": True,
                        "content_type": "link"
                    }
                )
                
                if capture_response.status_code == 200:
                    result = capture_response.json()
                    print(f"  ✓ Capture initiated: {result.get('item_id')}")
                    success += 1
                    
                    # Wait a bit before checking status
                    time.sleep(5)
                    
                    # Check if processing completed
                    item_response = requests.get(f"http://localhost:8000/api/items/{result['item_id']}")
                    if item_response.status_code == 200:
                        item_data = item_response.json()
                        print(f"  Status: {item_data.get('status')}")
                        if item_data.get('summary') and not item_data['summary'].startswith('Saved bookmark'):
                            print(f"  Summary: {item_data['summary'][:100]}...")
                else:
                    print(f"  ✗ Capture failed: {capture_response.status_code}")
                    failed += 1
                    
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                failed += 1
            
            # Rate limit
            time.sleep(2)
    
    print(f"\n=== Reprocessing Complete ===")
    print(f"Success: {success}")
    print(f"Failed: {failed}")
    print(f"Total bookmarks: {len(bookmarks)}")


if __name__ == "__main__":
    reprocess_bookmarks()