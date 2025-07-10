#!/usr/bin/env python3
"""
Database Schema Validation Script
Automatically checks if all required tables and columns exist for the PRSNL application.
"""

import asyncpg
import asyncio
import sys
import json
from typing import Dict, List, Set
import os
from pathlib import Path

# Database connection config
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/prsnl"

# Required schema based on the application code
REQUIRED_SCHEMA = {
    "items": {
        "columns": [
            "id", "url", "title", "summary", "raw_content", "processed_content",
            "status", "search_vector", "metadata", "created_at", "updated_at",
            "accessed_at", "access_count", "embedding", "transcription"
        ],
        "optional_columns": [
            "content_type", "enable_summarization", "video_url", "platform",
            "duration", "file_path", "thumbnail_url", "highlight"
        ]
    },
    "tags": {
        "columns": ["id", "name", "color", "created_at", "updated_at"],
        "optional_columns": ["description", "parent_id"]
    },
    "item_tags": {
        "columns": ["item_id", "tag_id", "created_at"],
        "optional_columns": []
    },
    "attachments": {
        "columns": ["id", "item_id", "filename", "file_path", "file_size", "mime_type", "created_at"],
        "optional_columns": ["thumbnail_path", "metadata"]
    },
    "api_keys": {
        "columns": ["id", "key_hash", "name", "created_at", "last_used_at", "is_active"],
        "optional_columns": ["expires_at", "permissions"]
    },
    "user_sessions": {
        "columns": ["id", "session_token", "created_at", "expires_at", "last_activity"],
        "optional_columns": ["user_data", "ip_address"]
    },
    "audit_logs": {
        "columns": ["id", "action", "resource_type", "resource_id", "created_at"],
        "optional_columns": ["user_id", "ip_address", "metadata"]
    },
    "jobs": {
        "columns": ["id", "type", "status", "payload", "created_at", "updated_at"],
        "optional_columns": ["started_at", "completed_at", "error_message", "retry_count"]
    }
}

# API endpoints and their table dependencies
API_DEPENDENCIES = {
    "/api/tags": ["tags", "item_tags"],
    "/api/suggest": ["items"],
    "/api/capture": ["items", "tags", "item_tags", "attachments"],
    "/api/timeline": ["items", "tags", "item_tags"],
    "/api/search": ["items", "tags", "item_tags"],
    "/api/items": ["items", "tags", "item_tags", "attachments"],
    "/api/insights": ["items", "tags", "item_tags"],
    "/api/videos": ["items", "tags", "item_tags"],
    "/api/import": ["items", "tags", "item_tags", "attachments", "jobs"]
}

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

async def get_database_schema(conn) -> Dict[str, Set[str]]:
    """Get actual database schema"""
    schema = {}
    
    # Get all tables
    tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    """
    tables = await conn.fetch(tables_query)
    
    for table_row in tables:
        table_name = table_row['table_name']
        
        # Get columns for each table
        columns_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = $1
        """
        columns = await conn.fetch(columns_query, table_name)
        schema[table_name] = {col['column_name'] for col in columns}
    
    return schema

def validate_schema(actual_schema: Dict[str, Set[str]]) -> Dict[str, List[str]]:
    """Validate actual schema against required schema"""
    issues = {
        "missing_tables": [],
        "missing_columns": [],
        "missing_optional_columns": [],
        "extra_tables": [],
        "api_issues": []
    }
    
    # Check for missing tables
    required_tables = set(REQUIRED_SCHEMA.keys())
    actual_tables = set(actual_schema.keys())
    
    missing_tables = required_tables - actual_tables
    extra_tables = actual_tables - required_tables
    
    issues["missing_tables"] = list(missing_tables)
    issues["extra_tables"] = list(extra_tables)
    
    # Check columns for existing tables
    for table_name, table_spec in REQUIRED_SCHEMA.items():
        if table_name not in actual_schema:
            continue
            
        actual_columns = actual_schema[table_name]
        required_columns = set(table_spec["columns"])
        optional_columns = set(table_spec.get("optional_columns", []))
        
        missing_required = required_columns - actual_columns
        missing_optional = optional_columns - actual_columns
        
        for col in missing_required:
            issues["missing_columns"].append(f"{table_name}.{col}")
            
        for col in missing_optional:
            issues["missing_optional_columns"].append(f"{table_name}.{col}")
    
    # Check API dependencies
    for api_endpoint, required_tables in API_DEPENDENCIES.items():
        missing_deps = []
        for table in required_tables:
            if table not in actual_schema:
                missing_deps.append(table)
        
        if missing_deps:
            issues["api_issues"].append({
                "endpoint": api_endpoint,
                "missing_tables": missing_deps
            })
    
    return issues

def print_report(issues: Dict[str, List[str]], actual_schema: Dict[str, Set[str]]):
    """Print validation report"""
    print(f"{Colors.BOLD}{Colors.CYAN}=== PRSNL Database Schema Validation Report ==={Colors.END}\n")
    
    # Summary
    total_issues = (
        len(issues["missing_tables"]) + 
        len(issues["missing_columns"]) + 
        len(issues["api_issues"])
    )
    
    if total_issues == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ Database schema is valid! All required tables and columns exist.{Colors.END}\n")
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ Found {total_issues} critical issues that need to be fixed.{Colors.END}\n")
    
    # Existing tables
    print(f"{Colors.BOLD}📊 Current Database Tables:{Colors.END}")
    for table_name, columns in sorted(actual_schema.items()):
        print(f"  {Colors.GREEN}✓{Colors.END} {table_name} ({len(columns)} columns)")
    print()
    
    # Critical issues
    if issues["missing_tables"]:
        print(f"{Colors.RED}{Colors.BOLD}🚨 CRITICAL: Missing Required Tables:{Colors.END}")
        for table in issues["missing_tables"]:
            print(f"  {Colors.RED}✗{Colors.END} {table}")
        print()
    
    if issues["missing_columns"]:
        print(f"{Colors.RED}{Colors.BOLD}🚨 CRITICAL: Missing Required Columns:{Colors.END}")
        for column in issues["missing_columns"]:
            print(f"  {Colors.RED}✗{Colors.END} {column}")
        print()
    
    # API impact analysis
    if issues["api_issues"]:
        print(f"{Colors.RED}{Colors.BOLD}🔥 API Endpoints That Will Fail:{Colors.END}")
        for api_issue in issues["api_issues"]:
            endpoint = api_issue["endpoint"]
            missing = ", ".join(api_issue["missing_tables"])
            print(f"  {Colors.RED}✗{Colors.END} {endpoint} (missing: {missing})")
        print()
    
    # Optional missing columns (warnings)
    if issues["missing_optional_columns"]:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  Missing Optional Columns (may cause feature limitations):{Colors.END}")
        for column in issues["missing_optional_columns"]:
            print(f"  {Colors.YELLOW}!{Colors.END} {column}")
        print()
    
    # Extra tables (info only)
    if issues["extra_tables"]:
        print(f"{Colors.CYAN}{Colors.BOLD}ℹ️  Extra Tables (not required by app):{Colors.END}")
        for table in issues["extra_tables"]:
            print(f"  {Colors.CYAN}+{Colors.END} {table}")
        print()

def generate_migration_sql(issues: Dict[str, List[str]]) -> str:
    """Generate SQL to fix missing tables/columns"""
    sql_commands = []
    
    # Add missing tables
    for table_name in issues["missing_tables"]:
        if table_name in REQUIRED_SCHEMA:
            table_spec = REQUIRED_SCHEMA[table_name]
            sql_commands.append(f"-- Create missing table: {table_name}")
            sql_commands.append(f"-- TODO: Define CREATE TABLE statement for {table_name}")
            sql_commands.append("")
    
    # Add missing columns
    for column_path in issues["missing_columns"]:
        table_name, column_name = column_path.split(".", 1)
        sql_commands.append(f"-- Add missing column: {column_path}")
        sql_commands.append(f"-- ALTER TABLE {table_name} ADD COLUMN {column_name} <TYPE>;")
        sql_commands.append("")
    
    return "\n".join(sql_commands)

async def main():
    """Main validation function"""
    print(f"{Colors.BOLD}{Colors.MAGENTA}🔍 Connecting to database...{Colors.END}")
    
    try:
        # First try to install asyncpg if it's not available
        try:
            import asyncpg
        except ImportError:
            print(f"{Colors.YELLOW}Installing asyncpg...{Colors.END}")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "asyncpg"])
            import asyncpg
            
        conn = await asyncpg.connect(DATABASE_URL)
        print(f"{Colors.GREEN}✅ Connected to database{Colors.END}\n")
        
        # Get actual schema
        actual_schema = await get_database_schema(conn)
        
        # Validate
        issues = validate_schema(actual_schema)
        
        # Print report
        print_report(issues, actual_schema)
        
        # Generate migration if needed
        if issues["missing_tables"] or issues["missing_columns"]:
            print(f"{Colors.BOLD}🛠️  Migration SQL:{Colors.END}")
            migration_sql = generate_migration_sql(issues)
            print(migration_sql)
        
        await conn.close()
        
        # Exit with error code if critical issues found
        critical_issues = len(issues["missing_tables"]) + len(issues["missing_columns"])
        if critical_issues > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"{Colors.RED}❌ Database connection failed: {e}{Colors.END}")
        print(f"{Colors.YELLOW}💡 Make sure PostgreSQL is running and accessible at: {DATABASE_URL}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())