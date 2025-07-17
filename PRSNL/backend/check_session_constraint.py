#!/usr/bin/env python3
"""
Check user_sessions table constraints
"""

import asyncio
import asyncpg
from app.config import settings

async def check_constraints():
    """Check constraints on user_sessions table"""
    
    db = await asyncpg.connect(settings.DATABASE_URL)
    
    # Get table constraints
    constraints = await db.fetch("""
        SELECT 
            conname as constraint_name,
            contype as constraint_type,
            pg_get_constraintdef(oid) as definition
        FROM pg_constraint 
        WHERE conrelid = 'user_sessions'::regclass
    """)
    
    print("User Sessions Table Constraints:")
    print("=" * 80)
    
    for constraint in constraints:
        print(f"\nConstraint: {constraint['constraint_name']}")
        print(f"Type: {constraint['constraint_type']}")
        print(f"Definition: {constraint['definition']}")
    
    # Check if session_token has unique constraint
    unique_check = await db.fetch("""
        SELECT 
            a.attname as column_name,
            i.indisunique as is_unique
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
        WHERE i.indrelid = 'user_sessions'::regclass
        AND a.attname = 'session_token'
    """)
    
    print("\n\nSession Token Index Info:")
    for idx in unique_check:
        print(f"Column: {idx['column_name']}, Is Unique: {idx['is_unique']}")
    
    await db.close()

if __name__ == "__main__":
    asyncio.run(check_constraints())