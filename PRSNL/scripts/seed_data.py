import asyncio
import asyncpg
import uuid
import random

async def seed_data():
    db_url = "postgresql://postgres:postgres@localhost:5432/prsnl"
    conn = None
    try:
        conn = await asyncpg.connect(db_url)
        print("Connected to database for seeding.")

        # Clear existing data (optional, for fresh seeding)
        await conn.execute("TRUNCATE TABLE item_tags, items, tags RESTART IDENTITY CASCADE;")
        print("Cleared existing data.")

        # Sample Tags
        tags_to_add = ["programming", "ai", "productivity", "reading", "news", "research", "webdev"]
        tag_ids = {}
        for tag_name in tags_to_add:
            tag_id = uuid.uuid4()
            await conn.execute("INSERT INTO tags (id, name) VALUES ($1, $2)", tag_id, tag_name)
            tag_ids[tag_name] = tag_id
        print(f"Added {len(tags_to_add)} sample tags.")

        # Sample Items
        sample_items = [
            {
                "url": "https://example.com/article1",
                "title": "The Future of AI in Personal Knowledge Management",
                "content": "Artificial intelligence is set to revolutionize how we manage and retrieve personal information. From intelligent tagging to predictive search, the possibilities are endless.",
                "tags": ["ai", "productivity", "research"]
            },
            {
                "url": "https://dev.to/python/fastapi-best-practices",
                "title": "FastAPI Best Practices for Scalable APIs",
                "content": "Building robust and scalable APIs with FastAPI requires adherence to certain best practices, including proper dependency injection and asynchronous programming.",
                "tags": ["programming", "webdev"]
            },
            {
                "url": "https://www.nytimes.com/2025/07/01/tech/new-tech-breakthrough.html",
                "title": "Breakthrough in Quantum Computing",
                "content": "Scientists have announced a significant leap forward in quantum computing, promising unprecedented processing power for complex problems.",
                "tags": ["news", "research"]
            },
            {
                "url": "https://medium.com/reading-list/speed-reading-techniques",
                "title": "Mastering Speed Reading Techniques",
                "content": "Improve your reading speed and comprehension with these proven techniques. Focus on chunking, pacing, and active recall.",
                "tags": ["reading", "productivity"]
            },
            {
                "url": "https://github.com/openai/gpt-3",
                "title": "OpenAI GPT-3 GitHub Repository",
                "content": "The official repository for OpenAI's GPT-3, showcasing its capabilities and providing resources for developers.",
                "tags": ["ai", "programming"]
            },
            {
                "url": "https://www.freecodecamp.org/news/learn-javascript-full-course/",
                "title": "Learn JavaScript - Full Course for Beginners",
                "content": "A comprehensive guide to learning JavaScript from scratch, covering everything from variables to advanced concepts like asynchronous programming.",
                "tags": ["programming", "webdev"]
            },
            {
                "url": "https://www.nature.com/articles/s41586-025-00001-x",
                "title": "New Discoveries in Neuroscience",
                "content": "Recent studies shed light on the intricate workings of the human brain, offering new insights into memory formation and cognitive processes.",
                "tags": ["research", "news"]
            },
            {
                "url": "https://www.producthunt.com/posts/new-productivity-app",
                "title": "Top 5 Productivity Apps of 2025",
                "content": "Discover the latest and most effective productivity applications designed to streamline your workflow and boost efficiency.",
                "tags": ["productivity"]
            },
            {
                "url": "https://www.smashingmagazine.com/2025/06/css-grid-layout-mastery/",
                "title": "CSS Grid Layout Mastery",
                "content": "A deep dive into CSS Grid Layout, exploring its powerful features for creating responsive and complex web designs.",
                "tags": ["webdev", "programming"]
            },
            {
                "url": "https://www.ted.com/talks/ai_and_humanity",
                "title": "AI and Humanity: A Symbiotic Future",
                "content": "A thought-provoking talk on the potential for artificial intelligence to complement human capabilities and foster a more collaborative future.",
                "tags": ["ai"]
            },
            {
                "url": "https://www.nasa.gov/mission/mars-rover-update/",
                "title": "Mars Rover Update: New Discoveries on the Red Planet",
                "content": "The latest updates from the Mars Rover mission, including stunning images and groundbreaking geological findings.",
                "tags": ["news", "research"]
            },
            {
                "url": "https://www.goodreads.com/book/show/12345.fiction",
                "title": "Fiction Novel: The Silent Echo",
                "content": "A captivating mystery novel that keeps you on the edge of your seat from beginning to end.",
                "tags": ["reading"]
            },
            {
                "url": "https://www.docker.com/blog/docker-compose-best-practices/",
                "title": "Docker Compose Best Practices",
                "content": "Optimize your Docker Compose configurations for development and production environments with these essential tips.",
                "tags": ["programming"]
            },
            {
                "url": "https://www.wired.com/story/future-of-work-ai/",
                "title": "How AI is Reshaping the Future of Work",
                "content": "Artificial intelligence is transforming industries and creating new job opportunities, requiring a shift in skills and education.",
                "tags": ["ai", "productivity"]
            },
            {
                "url": "https://www.investopedia.com/terms/b/blockchain.asp",
                "title": "Blockchain Explained: A Beginner's Guide",
                "content": "Understand the fundamentals of blockchain technology, its applications, and its potential impact on various sectors.",
                "tags": ["research"]
            },
            {
                "url": "https://www.epicurious.com/recipes/main/views/quick-dinner-ideas",
                "title": "Quick and Easy Dinner Ideas",
                "content": "Delicious and simple recipes for busy weeknights, perfect for a quick and satisfying meal.",
                "tags": []
            },
            {
                "url": "https://www.nationalgeographic.com/animals/article/endangered-species-conservation",
                "title": "Efforts to Save Endangered Species",
                "content": "Conservationists are working tirelessly to protect and restore populations of endangered animals around the world.",
                "tags": ["news"]
            },
            {
                "url": "https://www.w3schools.com/html/html_forms.asp",
                "title": "HTML Forms Tutorial",
                "content": "A comprehensive tutorial on creating and styling HTML forms, covering input types, attributes, and validation.",
                "tags": ["webdev"]
            },
            {
                "url": "https://www.psychologytoday.com/us/blog/the-power-of-mind/202506/mindfulness-for-stress-reduction",
                "title": "Mindfulness for Stress Reduction",
                "content": "Practice mindfulness techniques to alleviate stress and improve mental well-being in your daily life.",
                "tags": ["productivity"]
            },
            {
                "url": "https://www.artstation.com/artwork/digital-painting-tutorial",
                "title": "Digital Painting Tutorial for Beginners",
                "content": "Learn the basics of digital painting, from brush techniques to color theory, with this step-by-step guide.",
                "tags": []
            }
        ]

        for item_data in sample_items:
            item_id = uuid.uuid4()
            await conn.execute(
                "INSERT INTO items (id, url, title, raw_content, processed_content) VALUES ($1, $2, $3, $4, $5)",
                item_id, item_data["url"], item_data["title"], item_data["content"], item_data["content"]
            )
            for tag_name in item_data.get("tags", []):
                tag_id = tag_ids.get(tag_name)
                if tag_id:
                    await conn.execute(
                        "INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)",
                        item_id, tag_id
                    )
            print(f"Inserted item: {item_data['title']}")
        print(f"Added {len(sample_items)} sample items.")

    except Exception as e:
        print(f"Error during seeding: {e}")
    finally:
        if conn:
            await conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    asyncio.run(seed_data())
