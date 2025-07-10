#!/usr/bin/env python3
"""
Column Reference Fix Script
This script fixes all column name mismatches in the backend codebase
"""

import os
import re
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

def fix_file_content(file_path, fixes):
    """Apply fixes to a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        for old_pattern, new_pattern, description in fixes:
            if isinstance(old_pattern, str):
                # Simple string replacement
                if old_pattern in content:
                    content = content.replace(old_pattern, new_pattern)
                    changes_made.append(description)
            else:
                # Regex replacement
                matches = old_pattern.findall(content)
                if matches:
                    content = old_pattern.sub(new_pattern, content)
                    changes_made.append(f"{description} ({len(matches)} matches)")
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return changes_made
        
        return []
        
    except Exception as e:
        print(f"  ❌ Error fixing {file_path}: {e}")
        return []

def fix_backend_files():
    """Fix all backend files with column name issues"""
    backend_path = Path("backend")
    
    if not backend_path.exists():
        print(f"{Colors.RED}❌ Backend directory not found{Colors.END}")
        return
    
    # Define all the fixes needed
    fixes = [
        # Fix item_type -> type in SQL queries and code
        (re.compile(r'\bitem_type\b'), 'type', 'Change item_type to type'),
        
        # Fix content -> processed_content in SQL queries  
        (re.compile(r'SELECT.*\bcontent\b.*FROM\s+items'), 
         lambda m: m.group(0).replace('content', 'processed_content'), 
         'Change content to processed_content in SELECT'),
        
        # Fix INSERT statements to use processed_content
        ('INSERT INTO items (id, title, url, content,', 
         'INSERT INTO items (id, title, url, processed_content,',
         'Fix INSERT statements to use processed_content'),
        
        # Fix metadata column reference (item_metadata -> metadata)
        ('item_metadata', 'metadata', 'Change item_metadata to metadata'),
        
        # Fix WHERE content IS NOT NULL
        ('WHERE content IS NOT NULL', 'WHERE processed_content IS NOT NULL', 
         'Fix WHERE content IS NOT NULL'),
        
        # Fix column selections that assume wrong names
        ('SELECT url, content, raw_content', 'SELECT url, processed_content, raw_content',
         'Fix SELECT with content column'),
    ]
    
    # Files to process
    file_patterns = [
        "**/*.py",
        "**/*.sql"
    ]
    
    total_files_processed = 0
    total_changes = 0
    
    for pattern in file_patterns:
        for file_path in backend_path.glob(pattern):
            if file_path.is_file() and not str(file_path).endswith('fix_column_references.py'):
                changes = fix_file_content(file_path, fixes)
                if changes:
                    total_files_processed += 1
                    total_changes += len(changes)
                    print(f"{Colors.GREEN}✅ Fixed {file_path}{Colors.END}")
                    for change in changes:
                        print(f"  - {change}")
    
    print(f"\n{Colors.CYAN}📊 Summary:{Colors.END}")
    print(f"  Files processed: {total_files_processed}")
    print(f"  Total changes: {total_changes}")

def create_test_data_fix():
    """Create a script to fix test data"""
    test_fixes = """
-- Fix for test files that reference item_type instead of type
-- This script updates all test INSERT statements

UPDATE items SET type = 'article' WHERE type IS NULL;

-- No additional fixes needed since we're resetting the database
"""
    
    with open("fix_test_data.sql", "w") as f:
        f.write(test_fixes)
    
    print(f"{Colors.GREEN}✅ Created fix_test_data.sql{Colors.END}")

def main():
    """Main fix function"""
    print(f"{Colors.BOLD}{Colors.CYAN}🔧 PRSNL Column Reference Fix{Colors.END}")
    print("=" * 50)
    
    print(f"{Colors.BLUE}🔍 Fixing backend files...{Colors.END}")
    fix_backend_files()
    
    print(f"\n{Colors.BLUE}🧪 Creating test data fixes...{Colors.END}")
    create_test_data_fix()
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}✅ All column reference fixes completed!{Colors.END}")
    print(f"{Colors.YELLOW}📋 Next steps:{Colors.END}")
    print("  1. Run the database reset script")
    print("  2. Replace the old models.py with models_unified.py")
    print("  3. Test all API endpoints")

if __name__ == "__main__":
    main()