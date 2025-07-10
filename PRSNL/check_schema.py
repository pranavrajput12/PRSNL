#!/usr/bin/env python3
"""
Simple Database Schema Check
Uses docker exec to check the schema
"""

import subprocess
import json
import sys

def run_sql(query):
    """Run SQL query via docker exec"""
    cmd = [
        'docker', 'exec', 'prsnl_db', 
        'psql', '-U', 'postgres', '-d', 'prsnl', 
        '-t', '-c', query
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running SQL: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return None

def check_table_columns(table_name):
    """Get columns for a table"""
    query = f"""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'public' AND table_name = '{table_name}'
    ORDER BY ordinal_position;
    """
    
    result = run_sql(query)
    if result:
        return [col.strip() for col in result.split('\n') if col.strip()]
    return []

def main():
    print("🔍 Database Schema Check")
    print("=" * 50)
    
    # Required columns for items table based on API usage
    required_items_columns = [
        "id", "url", "title", "summary", "raw_content", "processed_content",
        "status", "search_vector", "metadata", "created_at", "updated_at",
        "accessed_at", "access_count", "embedding", "transcription"
    ]
    
    optional_items_columns = [
        "content_type", "enable_summarization", "video_url", "platform",
        "duration", "file_path", "thumbnail_url", "highlight"
    ]
    
    # Check items table
    print("\n📊 Checking 'items' table...")
    actual_columns = check_table_columns('items')
    
    if not actual_columns:
        print("❌ Could not retrieve items table columns")
        return
        
    print(f"✅ Found {len(actual_columns)} columns in 'items' table")
    
    # Check required columns
    missing_required = []
    for col in required_items_columns:
        if col not in actual_columns:
            missing_required.append(col)
    
    # Check optional columns
    missing_optional = []
    for col in optional_items_columns:
        if col not in actual_columns:
            missing_optional.append(col)
    
    # Report results
    print("\n🔍 ANALYSIS RESULTS:")
    print("-" * 30)
    
    if missing_required:
        print(f"🚨 CRITICAL: Missing {len(missing_required)} required columns:")
        for col in missing_required:
            print(f"   ❌ items.{col}")
    else:
        print("✅ All required columns present")
        
    if missing_optional:
        print(f"\n⚠️  Missing {len(missing_optional)} optional columns:")
        for col in missing_optional:
            print(f"   🟡 items.{col}")
    else:
        print("\n✅ All optional columns present")
        
    print(f"\n📋 Current columns in 'items' table:")
    for col in actual_columns:
        status = "✅" if col in required_items_columns + optional_items_columns else "➕"
        print(f"   {status} {col}")
    
    # Generate SQL for missing columns
    if missing_optional:
        print(f"\n🛠️  SQL to add missing optional columns:")
        print("-" * 40)
        
        sql_commands = {
            "content_type": "ALTER TABLE items ADD COLUMN content_type VARCHAR(50) DEFAULT 'auto';",
            "enable_summarization": "ALTER TABLE items ADD COLUMN enable_summarization BOOLEAN DEFAULT false;", 
            "video_url": "ALTER TABLE items ADD COLUMN video_url TEXT;",
            "platform": "ALTER TABLE items ADD COLUMN platform VARCHAR(50);",
            "duration": "ALTER TABLE items ADD COLUMN duration INTEGER;",
            "file_path": "ALTER TABLE items ADD COLUMN file_path TEXT;",
            "thumbnail_url": "ALTER TABLE items ADD COLUMN thumbnail_url TEXT;",
            "highlight": "ALTER TABLE items ADD COLUMN highlight TEXT;"
        }
        
        for col in missing_optional:
            if col in sql_commands:
                print(f"-- Add {col}")
                print(sql_commands[col])
                print()
    
    # Exit with error if critical issues
    if missing_required:
        print("❌ Critical schema issues found!")
        sys.exit(1)
    elif missing_optional:
        print("⚠️  Optional columns missing - APIs may have limited functionality")
        sys.exit(0)
    else:
        print("✅ Database schema is complete!")
        sys.exit(0)

if __name__ == "__main__":
    main()