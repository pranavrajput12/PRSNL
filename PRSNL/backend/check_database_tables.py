#!/usr/bin/env python3
"""Check what tables exist in the PRSNL database"""
import asyncio
import os
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def check_tables():
    """List all tables in the database"""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5433/prsnl")
    # Fix Railway's postgres:// to postgresql:// for asyncpg
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    print("Connecting to database...")
    print("-" * 60)
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # Query all tables
        tables_query = """
        SELECT 
            schemaname,
            tablename
        FROM pg_tables 
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schemaname, tablename;
        """
        
        tables = await conn.fetch(tables_query)
        
        print(f"Found {len(tables)} tables:")
        print()
        
        for table in tables:
            print(f"  {table['schemaname']}.{table['tablename']}")
        
        print()
        print("Checking for authentication-related tables...")
        auth_tables = ['users', 'user_sessions', 'verification_tokens']
        
        for table_name in auth_tables:
            exists_query = """
            SELECT EXISTS (
                SELECT FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename = $1
            );
            """
            exists = await conn.fetchval(exists_query, table_name)
            status = "✅" if exists else "❌"
            print(f"  {status} {table_name}")
        
        # Close connection
        await conn.close()
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_tables())