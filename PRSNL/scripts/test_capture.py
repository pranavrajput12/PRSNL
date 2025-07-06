import asyncio
import asyncpg
import json
import os

async def send_notification(item_data: dict):
    db_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/prsnl")
    conn = None
    try:
        conn = await asyncpg.connect(db_url)
        # In a real scenario, this would be an INSERT that triggers the NOTIFY
        # For testing the worker, we directly send a NOTIFY
        await conn.execute(f"NOTIFY item_created, '{json.dumps(item_data)}';")
        print(f"Sent notification for item ID: {item_data.get('id')}")
    except Exception as e:
        print(f"Error sending notification: {e}")
    finally:
        if conn:
            await conn.close()

async def main():
    test_item = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "url": "http://example.com/test",
        "title": "Test Item from Script",
        "content": "This is some test content for the worker to process."
    }
    await send_notification(test_item)
    print("Test notification sent. Check worker logs for processing.")

if __name__ == "__main__":
    asyncio.run(main())
