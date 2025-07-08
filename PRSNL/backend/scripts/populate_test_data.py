import asyncio
import random
from datetime import datetime, timedelta
from faker import Faker
from app.db.database import get_db_pool
from app.services.embedding_service import EmbeddingService
from app.services.unified_ai_service import UnifiedAIService
import json

fake = Faker()
embedding_service = EmbeddingService()
ai_service = UnifiedAIService()

async def create_item(pool, item_type, title, content, url, tags, summary, category, created_at):
    """Inserts a single item into the database."""
    async with pool.acquire() as conn:
        # Generate embedding for the content
        embedding = await embedding_service.get_embedding(content)
        
        # Convert tags list to a comma-separated string
        tags_str = ",".join(tags)

        # Prepare metadata
        metadata = {
            "type": item_type,
            "tags": tags_str,
            "category": category,
            "source": url.split('/')[2] if url else "manual",
            "summary": summary
        }
        
        # Add type-specific metadata
        if item_type == "video":
            metadata["duration"] = str(random.randint(60, 3600)) # seconds
            metadata["platform"] = "youtube" if "youtube.com" in url else "other"
            metadata["thumbnail_url"] = fake.image_url()
        elif item_type == "article":
            metadata["author"] = fake.name()
            metadata["read_time"] = f"{random.randint(2, 20)} min"
        elif item_type == "tweet":
            metadata["author"] = fake.user_name()
            metadata["likes"] = random.randint(10, 1000)
            metadata["retweets"] = random.randint(5, 500)
        elif item_type == "github_repo":
            metadata["owner"] = fake.user_name()
            metadata["stars"] = random.randint(100, 10000)
            metadata["language"] = random.choice(["Python", "JavaScript", "TypeScript", "Go", "Rust"])
        elif item_type == "pdf":
            metadata["pages"] = random.randint(5, 100)
            metadata["file_size"] = f"{random.randint(1, 50)}MB"

        await conn.execute(
            """
            INSERT INTO items (title, raw_content, processed_content, url, embedding, metadata, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            title,
            content,
            content, # For simplicity, processed_content is same as raw_content
            url,
            embedding,
            json.dumps(metadata),
            created_at
        )
    print(f"Added {item_type}: {title}")

async def populate_test_data(num_items=50):
    """Populates the database with diverse test data."""
    pool = await get_db_pool()
    
    item_types = ["article", "video", "tweet", "github_repo", "pdf"]
    
    for i in range(num_items):
        item_type = random.choice(item_types)
        title = fake.sentence(nb_words=random.randint(3, 8)).replace('.', '')
        content = fake.paragraph(nb_sentences=random.randint(5, 15))
        url = fake.url()
        tags = random.sample(fake.words(nb=5), random.randint(1, 3))
        summary = fake.sentence(nb_words=random.randint(10, 20))
        category = random.choice(["Technology", "Science", "News", "Programming", "Education", "Entertainment"])
        created_at = datetime.now() - timedelta(days=random.randint(0, 365))

        await create_item(pool, item_type, title, content, url, tags, summary, category, created_at)
    
    print(f"Successfully populated {num_items} test items.")

if __name__ == "__main__":
    asyncio.run(populate_test_data(num_items=50))
