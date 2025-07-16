#!/usr/bin/env python3
"""Check email_verifications table schema"""
import asyncio
import os
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def check_schema():
    """Check the schema of email_verifications table"""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5433/prsnl")
    # Fix Railway's postgres:// to postgresql:// for asyncpg
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    print("Checking email_verifications table schema...")
    print("-" * 60)
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # Query table schema
        schema_query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' 
        AND table_name = 'email_verifications'
        ORDER BY ordinal_position;
        """
        
        columns = await conn.fetch(schema_query)
        
        if columns:
            print("email_verifications table columns:")
            print()
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"  - {col['column_name']}: {col['data_type']} {nullable} {default}")
        else:
            print("❌ Table email_verifications not found or has no columns")
        
        # Close connection
        await conn.close()
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_schema())