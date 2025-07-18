#!/usr/bin/env python3
"""
Add more missing columns to the database
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def add_columns():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        # Check and add platform column
        platform_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'items'
                AND column_name = 'platform'
            )
        """)
        
        if not platform_exists:
            print('Adding platform column to items table...')
            await conn.execute("""
                ALTER TABLE items ADD COLUMN platform VARCHAR(255)
            """)
            print('✅ platform column added successfully')
        else:
            print('✅ platform column already exists')
            
        # Check and add raw_content column
        raw_content_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'items'
                AND column_name = 'raw_content'
            )
        """)
        
        if not raw_content_exists:
            print('Adding raw_content column to items table...')
            await conn.execute("""
                ALTER TABLE items ADD COLUMN raw_content TEXT
            """)
            print('✅ raw_content column added successfully')
        else:
            print('✅ raw_content column already exists')
            
        # Check and add processed_content column
        processed_content_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'items'
                AND column_name = 'processed_content'
            )
        """)
        
        if not processed_content_exists:
            print('Adding processed_content column to items table...')
            await conn.execute("""
                ALTER TABLE items ADD COLUMN processed_content TEXT
            """)
            print('✅ processed_content column added successfully')
        else:
            print('✅ processed_content column already exists')
            
        # Check and add search_vector column
        search_vector_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'items'
                AND column_name = 'search_vector'
            )
        """)
        
        if not search_vector_exists:
            print('Adding search_vector column to items table...')
            await conn.execute("""
                ALTER TABLE items ADD COLUMN search_vector tsvector
            """)
            print('✅ search_vector column added successfully')
            
            # Create index for search_vector
            print('Creating index on search_vector...')
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_items_search_vector 
                ON items USING GIN (search_vector)
            """)
            print('✅ search_vector index created successfully')
        else:
            print('✅ search_vector column already exists')
            
        # Check and add embedding column
        embedding_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'items'
                AND column_name = 'embedding'
            )
        """)
        
        if not embedding_exists:
            print('Adding embedding column to items table...')
            await conn.execute("""
                ALTER TABLE items ADD COLUMN embedding vector(1536)
            """)
            print('✅ embedding column added successfully')
        else:
            print('✅ embedding column already exists')
            
    except Exception as e:
        print(f'❌ Error: {e}')
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_columns())