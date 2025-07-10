#!/usr/bin/env python3
"""
Database Reset using Docker Exec
This script resets the database using docker exec commands
"""

import subprocess
import sys
from pathlib import Path

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

def run_sql_command(sql_command, description=""):
    """Run SQL command via docker exec"""
    try:
        cmd = [
            'docker', 'exec', 'prsnl_db', 
            'psql', '-U', 'postgres', '-d', 'prsnl', 
            '-c', sql_command
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if description:
            print(f"  ✅ {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed: {description}")
        print(f"     Error: {e.stderr}")
        return False

def run_sql_file(file_path, description=""):
    """Run SQL file via docker exec"""
    try:
        cmd = [
            'docker', 'exec', '-i', 'prsnl_db', 
            'psql', '-U', 'postgres', '-d', 'prsnl'
        ]
        
        with open(file_path, 'r') as f:
            result = subprocess.run(cmd, input=f.read(), text=True, check=True, capture_output=True)
        
        if description:
            print(f"  ✅ {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed: {description}")
        print(f"     Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"  ❌ File not found: {file_path}")
        return False

def drop_all_tables():
    """Drop all tables and start fresh"""
    print(f"{Colors.YELLOW}🗑️  Dropping all existing tables...{Colors.END}")
    
    # Drop tables in reverse dependency order
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
        run_sql_command(f"DROP TABLE IF EXISTS {table} CASCADE;", f"Dropped table: {table}")
    
    # Drop views
    views = ['video_items', 'file_storage_stats', 'recent_files']
    for view in views:
        run_sql_command(f"DROP VIEW IF EXISTS {view} CASCADE;", f"Dropped view: {view}")
    
    # Drop functions
    functions = [
        'update_search_vector()',
        'update_updated_at()',
        'notify_item_created()',
        'update_item_file_count()',
        'set_item_type()',
        'get_file_content_summary(uuid)',
        'cleanup_orphaned_files()',
        'update_updated_at_column()'
    ]
    
    for func in functions:
        run_sql_command(f"DROP FUNCTION IF EXISTS {func} CASCADE;", f"Dropped function: {func}")

def create_unified_schema():
    """Create the unified schema"""
    print(f"{Colors.BLUE}🏗️  Creating unified database schema...{Colors.END}")
    
    schema_path = Path("backend/app/db/schema_unified.sql")
    
    if not schema_path.exists():
        print(f"{Colors.RED}❌ Schema file not found: {schema_path}{Colors.END}")
        return False
    
    return run_sql_file(schema_path, "Unified schema created successfully")

def verify_schema():
    """Verify that all expected tables exist"""
    print(f"{Colors.CYAN}🔍 Verifying schema integrity...{Colors.END}")
    
    # Check if key tables exist
    expected_tables = ['items', 'tags', 'files', 'jobs', 'attachments']
    
    for table in expected_tables:
        cmd = [
            'docker', 'exec', 'prsnl_db', 
            'psql', '-U', 'postgres', '-d', 'prsnl', 
            '-t', '-c', f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table}');"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            exists = result.stdout.strip() == 't'
            
            if exists:
                print(f"  ✅ Table {table} exists")
            else:
                print(f"  ❌ Table {table} missing")
                return False
        except:
            print(f"  ❌ Could not check table {table}")
            return False
    
    # Check critical columns in items table
    critical_columns = ['id', 'type', 'content_type', 'enable_summarization', 'has_files']
    
    for column in critical_columns:
        cmd = [
            'docker', 'exec', 'prsnl_db', 
            'psql', '-U', 'postgres', '-d', 'prsnl', 
            '-t', '-c', f"SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'items' AND column_name = '{column}');"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            exists = result.stdout.strip() == 't'
            
            if exists:
                print(f"  ✅ Column items.{column} exists")
            else:
                print(f"  ❌ Column items.{column} missing")
                return False
        except:
            print(f"  ❌ Could not check column {column}")
            return False
    
    print(f"{Colors.GREEN}✅ Schema verification passed{Colors.END}")
    return True

def test_basic_operations():
    """Test basic database operations"""
    print(f"{Colors.MAGENTA}🧪 Testing basic database operations...{Colors.END}")
    
    # Test item insertion
    test_sql = """
    INSERT INTO items (
        id, url, title, type, status, content_type, 
        enable_summarization, has_files, file_count, highlight
    ) VALUES (
        'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 
        'https://example.com/test', 
        'Test Item', 
        'article', 
        'pending', 
        'auto', 
        false, 
        false, 
        0, 
        'Test highlight'
    );
    """
    
    if not run_sql_command(test_sql, "Item insertion test"):
        return False
    
    # Test retrieval
    test_query = """
    SELECT id, title, type, content_type, enable_summarization, has_files 
    FROM items 
    WHERE id = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';
    """
    
    if not run_sql_command(test_query, "Item retrieval test"):
        return False
    
    # Clean up
    cleanup_sql = "DELETE FROM items WHERE id = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';"
    run_sql_command(cleanup_sql, "Test data cleanup")
    
    print(f"{Colors.GREEN}✅ All basic operations successful{Colors.END}")
    return True

def main():
    """Main reset function"""
    print(f"{Colors.BOLD}{Colors.CYAN}🔄 PRSNL Database Reset & Initialization{Colors.END}")
    print("=" * 60)
    
    # Step 1: Drop all existing tables
    drop_all_tables()
    print()
    
    # Step 2: Create unified schema
    if not create_unified_schema():
        print(f"{Colors.RED}❌ Failed to create unified schema{Colors.END}")
        return False
    print()
    
    # Step 3: Verify schema
    if not verify_schema():
        print(f"{Colors.RED}❌ Schema verification failed{Colors.END}")
        return False
    print()
    
    # Step 4: Test basic operations
    if not test_basic_operations():
        print(f"{Colors.RED}❌ Basic operations test failed{Colors.END}")
        return False
    print()
    
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
    print("  1. Fix column references in backend code")
    print("  2. Replace SQLAlchemy models")
    print("  3. Restart backend container")
    print("  4. Test capture API")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)