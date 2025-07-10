#!/usr/bin/env python3
"""
Database Reset and Initialization Script
This script completely resets the database using the unified schema
"""

import asyncio
import asyncpg
import sys
import os
from pathlib import Path

# Database connection config
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/prsnl"

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

async def drop_all_tables(conn):
    """Drop all tables and start fresh"""
    print(f"{Colors.YELLOW}🗑️  Dropping all existing tables...{Colors.END}")
    
    # Drop tables in reverse dependency order to avoid foreign key issues
    tables_to_drop = [
        'file_processing_log',
        'audit_logs',
        'api_keys', 
        'user_sessions',
        'jobs',
        'attachments',
        'files',
        'item_tags',
        'tags',
        'items'
    ]
    
    for table in tables_to_drop:
        try:
            await conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            print(f"  ✓ Dropped table: {table}")
        except Exception as e:
            print(f"  ⚠️  Could not drop {table}: {e}")
    
    # Drop views
    views_to_drop = ['video_items', 'file_storage_stats', 'recent_files']
    for view in views_to_drop:
        try:
            await conn.execute(f"DROP VIEW IF EXISTS {view} CASCADE")
            print(f"  ✓ Dropped view: {view}")
        except Exception as e:
            print(f"  ⚠️  Could not drop view {view}: {e}")
    
    # Drop functions
    functions_to_drop = [
        'update_search_vector()',
        'update_updated_at()',
        'notify_item_created()',
        'update_item_file_count()',
        'set_item_type()',
        'get_file_content_summary(uuid)',
        'cleanup_orphaned_files()',
        'update_updated_at_column()'
    ]
    
    for func in functions_to_drop:
        try:
            await conn.execute(f"DROP FUNCTION IF EXISTS {func} CASCADE")
            print(f"  ✓ Dropped function: {func}")
        except Exception as e:
            print(f"  ⚠️  Could not drop function {func}: {e}")

async def create_unified_schema(conn):
    """Create the unified schema"""
    print(f"{Colors.BLUE}🏗️  Creating unified database schema...{Colors.END}")
    
    # Read the unified schema file
    schema_path = Path(__file__).parent / "backend" / "app" / "db" / "schema_unified.sql"
    
    if not schema_path.exists():
        print(f"{Colors.RED}❌ Schema file not found: {schema_path}{Colors.END}")
        return False
    
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    try:
        await conn.execute(schema_sql)
        print(f"{Colors.GREEN}✅ Unified schema created successfully{Colors.END}")
        return True
    except Exception as e:
        print(f"{Colors.RED}❌ Failed to create schema: {e}{Colors.END}")
        return False

async def verify_schema(conn):
    """Verify that all expected tables and columns exist"""
    print(f"{Colors.CYAN}🔍 Verifying schema integrity...{Colors.END}")
    
    # Expected tables
    expected_tables = [
        'items', 'tags', 'item_tags', 'files', 'attachments', 
        'file_processing_log', 'jobs', 'user_sessions', 'api_keys', 'audit_logs'
    ]
    
    # Check tables exist
    for table in expected_tables:
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = $1 AND table_schema = 'public'
            )
        """, table)
        
        if exists:
            print(f"  ✅ Table {table} exists")
        else:
            print(f"  ❌ Table {table} missing")
            return False
    
    # Check critical columns in items table
    critical_columns = [
        'id', 'url', 'title', 'type', 'status', 'content_type', 
        'enable_summarization', 'has_files', 'file_count', 'highlight'
    ]
    
    for column in critical_columns:
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'items' AND column_name = $1
            )
        """, column)
        
        if exists:
            print(f"  ✅ Column items.{column} exists")
        else:
            print(f"  ❌ Column items.{column} missing")
            return False
    
    print(f"{Colors.GREEN}✅ Schema verification passed{Colors.END}")
    return True

async def test_basic_operations(conn):
    """Test basic database operations"""
    print(f"{Colors.MAGENTA}🧪 Testing basic database operations...{Colors.END}")
    
    try:
        # Test item insertion with all key fields
        test_id = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
        await conn.execute("""
            INSERT INTO items (
                id, url, title, type, status, content_type, 
                enable_summarization, has_files, file_count, highlight
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, test_id, 'https://example.com/test', 'Test Item', 'article', 'pending', 
             'auto', False, False, 0, 'Test highlight')
        
        print("  ✅ Item insertion successful")
        
        # Test tag creation and linking
        tag_id = 'bbbbbbbb-cccc-dddd-eeee-ffffffffffff'
        await conn.execute("""
            INSERT INTO tags (id, name) VALUES ($1, $2)
        """, tag_id, 'test-tag')
        
        await conn.execute("""
            INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)
        """, test_id, tag_id)
        
        print("  ✅ Tag creation and linking successful")
        
        # Test retrieval
        item = await conn.fetchrow("""
            SELECT id, title, type, content_type, enable_summarization, has_files 
            FROM items WHERE id = $1
        """, test_id)
        
        if item:
            print(f"  ✅ Item retrieval successful: {item['title']}")
        else:
            print("  ❌ Item retrieval failed")
            return False
        
        # Clean up test data
        await conn.execute("DELETE FROM items WHERE id = $1", test_id)
        await conn.execute("DELETE FROM tags WHERE id = $1", tag_id)
        
        print(f"{Colors.GREEN}✅ All basic operations successful{Colors.END}")
        return True
        
    except Exception as e:
        print(f"{Colors.RED}❌ Basic operations test failed: {e}{Colors.END}")
        return False

async def main():
    """Main reset function"""
    print(f"{Colors.BOLD}{Colors.CYAN}🔄 PRSNL Database Reset & Initialization{Colors.END}")
    print("=" * 60)
    
    try:
        # Connect to database
        print(f"{Colors.BLUE}📡 Connecting to database...{Colors.END}")
        conn = await asyncpg.connect(DATABASE_URL)
        print(f"{Colors.GREEN}✅ Connected to database{Colors.END}\n")
        
        # Step 1: Drop all existing tables
        await drop_all_tables(conn)
        print()
        
        # Step 2: Create unified schema
        if not await create_unified_schema(conn):
            return False
        print()
        
        # Step 3: Verify schema
        if not await verify_schema(conn):
            return False
        print()
        
        # Step 4: Test basic operations
        if not await test_basic_operations(conn):
            return False
        print()
        
        await conn.close()
        
        print(f"{Colors.BOLD}{Colors.GREEN}🎉 Database reset completed successfully!{Colors.END}")
        print(f"{Colors.CYAN}📋 Summary:{Colors.END}")
        print("  ✅ All old tables and data removed")
        print("  ✅ Unified schema created with all required tables")
        print("  ✅ All column name conflicts resolved") 
        print("  ✅ File support tables added")
        print("  ✅ Schema integrity verified")
        print("  ✅ Basic operations tested")
        print()
        print(f"{Colors.YELLOW}🔧 Next steps:{Colors.END}")
        print("  1. Restart the backend container")
        print("  2. Test the capture API with all 16 scenarios")
        print("  3. Verify enable_summarization works correctly")
        
        return True
        
    except Exception as e:
        print(f"{Colors.RED}❌ Database reset failed: {e}{Colors.END}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)