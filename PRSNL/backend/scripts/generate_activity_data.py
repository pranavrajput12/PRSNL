import asyncio
import random
from datetime import datetime, timedelta
from faker import Faker
from app.db.database import get_db_pool
import json

fake = Faker()

async def create_user(pool, username, email, created_at):
    """Inserts a single user into the database."""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (username, email, created_at)
            VALUES ($1, $2, $3)
            """,
            username,
            email,
            created_at
        )
    print(f"Added user: {username}")

async def create_activity(pool, user_id, item_id, activity_type, timestamp):
    """Inserts a single activity record into the database."""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO activities (user_id, item_id, activity_type, timestamp)
            VALUES ($1, $2, $3, $4)
            """,
            user_id,
            item_id,
            activity_type,
            timestamp
        )
    # print(f"Added activity: {activity_type} for user {user_id} on item {item_id}")

async def generate_activity_data(num_users=5, num_activities_per_user=100):
    """Generates realistic user and activity data."""
    pool = await get_db_pool()

    # Create users
    user_ids = []
    for _ in range(num_users):
        username = fake.user_name()
        email = fake.email()
        created_at = datetime.now() - timedelta(days=random.randint(0, 365))
        await create_user(pool, username, email, created_at)
        async with pool.acquire() as conn:
            user_record = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
            user_ids.append(user_record['id'])

    # Get existing item IDs
    async with pool.acquire() as conn:
        item_records = await conn.fetch("SELECT id FROM items")
        item_ids = [record['id'] for record in item_records]

    if not item_ids:
        print("No items found in the database. Please run populate_test_data.py first.")
        return

    activity_types = ["view", "like", "share", "comment", "capture"]

    # Generate activities
    for user_id in user_ids:
        for _ in range(num_activities_per_user):
            item_id = random.choice(item_ids)
            activity_type = random.choice(activity_types)
            timestamp = datetime.now() - timedelta(days=random.randint(0, 365), hours=random.randint(0, 23), minutes=random.randint(0, 59))
            await create_activity(pool, user_id, item_id, activity_type, timestamp)

    print(f"Successfully generated {num_users} users and {num_users * num_activities_per_user} activities.")

if __name__ == "__main__":
    asyncio.run(generate_activity_data(num_users=5, num_activities_per_user=100))
