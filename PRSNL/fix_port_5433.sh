#!/bin/bash

# Fix all instances of port 5432 to 5432
echo "Fixing all instances of port 5432 to 5432..."

# Find and replace in all files
find . -type f \( -name "*.py" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" -o -name "*.env" -o -name "*.sh" -o -name "*.json" \) \
    -not -path "*/node_modules/*" \
    -not -path "*/.git/*" \
    -not -path "*/venv/*" \
    -not -path "*/__pycache__/*" \
    -exec grep -l "5432" {} \; | while read file; do
    echo "Fixing: $file"
    sed -i '' 's/5432/5432/g' "$file"
done

echo "All instances of port 5432 have been replaced with 5432"
echo "Please restart any services that were using the old port."