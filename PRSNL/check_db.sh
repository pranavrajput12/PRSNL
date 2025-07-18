#!/bin/bash

echo "=== Checking Database Status ==="
echo ""

# Check if PostgreSQL is running
echo "1. PostgreSQL Status:"
ps aux | grep postgres | grep -v grep | head -3

echo ""
echo "2. Database Tables:"
psql -U pronav -d prsnl -p 5432 << EOF
\dt
EOF

echo ""
echo "3. User Table Sample (if exists):"
psql -U pronav -d prsnl -p 5432 << EOF
SELECT COUNT(*) as user_count FROM users;
EOF

echo ""
echo "4. Items Table Sample (if exists):"
psql -U pronav -d prsnl -p 5432 << EOF
SELECT COUNT(*) as item_count FROM items;
EOF

echo ""
echo "5. pgvector Extension:"
psql -U pronav -d prsnl -p 5432 << EOF
\dx vector
EOF