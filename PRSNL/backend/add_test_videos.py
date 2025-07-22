import json
import uuid
from datetime import datetime

import psycopg2

# Database connection
conn = psycopg2.connect(
    host='127.0.0.1',
    port=5432,
    database='prsnl',
    user='prsnl',
    password='prsnl123'
)
cur = conn.cursor()

# Test videos data
videos = [
    {
        'title': 'First YouTube Video - Me at the zoo',
        'url': 'https://www.youtube.com/watch?v=jNQXAC9IVRw',
        'platform': 'youtube',
        'duration': 19,
        'thumbnail_url': 'https://img.youtube.com/vi/jNQXAC9IVRw/maxresdefault.jpg'
    },
    {
        'title': 'PSY - GANGNAM STYLE',
        'url': 'https://www.youtube.com/watch?v=9bZkp7q19f0',
        'platform': 'youtube',
        'duration': 252,
        'thumbnail_url': 'https://img.youtube.com/vi/9bZkp7q19f0/maxresdefault.jpg'
    },
    {
        'title': 'Luis Fonsi - Despacito ft. Daddy Yankee',
        'url': 'https://www.youtube.com/watch?v=kJQP7kiw5Fk',
        'platform': 'youtube',
        'duration': 282,
        'thumbnail_url': 'https://img.youtube.com/vi/kJQP7kiw5Fk/maxresdefault.jpg'
    },
    {
        'title': 'Mark Ronson - Uptown Funk ft. Bruno Mars',
        'url': 'https://www.youtube.com/watch?v=OPf0YbXqDm0',
        'platform': 'youtube',
        'duration': 270,
        'thumbnail_url': 'https://img.youtube.com/vi/OPf0YbXqDm0/maxresdefault.jpg'
    },
    {
        'title': 'Ed Sheeran - Shape of You',
        'url': 'https://www.youtube.com/watch?v=JGwWNGJdvx8',
        'platform': 'youtube',
        'duration': 263,
        'thumbnail_url': 'https://img.youtube.com/vi/JGwWNGJdvx8/maxresdefault.jpg'
    },
    {
        'title': 'Wiz Khalifa - See You Again ft. Charlie Puth',
        'url': 'https://www.youtube.com/watch?v=RgKAFK5djSk',
        'platform': 'youtube',
        'duration': 229,
        'thumbnail_url': 'https://img.youtube.com/vi/RgKAFK5djSk/maxresdefault.jpg'
    }
]

# Insert videos
for video in videos:
    video_id = str(uuid.uuid4())
    metadata = {
        'video': {
            'description': f'Popular YouTube video: {video["title"]}',
            'views': 1000000,
            'likes': 50000,
            'channel': 'Test Channel'
        }
    }
    
    cur.execute("""
        INSERT INTO items (
            id, title, url, type, platform, duration, 
            thumbnail_url, status, created_at, metadata
        ) VALUES (
            %s, %s, %s, 'video', %s, %s, 
            %s, 'completed', %s, %s
        )
    """, (
        video_id,
        video['title'],
        video['url'],
        video['platform'],
        video['duration'],
        video['thumbnail_url'],
        datetime.now(),
        json.dumps(metadata)
    ))
    print(f"Added: {video['title']}")

conn.commit()
cur.close()
conn.close()

print("\nDone! Added 6 test videos.")