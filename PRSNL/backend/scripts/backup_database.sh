#!/bin/bash

# Load environment variables from .env file if it exists
if [ -f .env ]; then
  export $(cat .env | grep -v '^'#' | xargs)
fi

# Database connection details
DB_HOST=${POSTGRES_HOST:-localhost}
DB_PORT=${POSTGRES_PORT:-5432}
DB_NAME=${POSTGRES_DB:-prsnl_db}
DB_USER=${POSTGRES_USER:-prsnl_user}
DB_PASSWORD=${POSTGRES_PASSWORD:-prsnl_password}

# Backup directory (relative to script location)
BACKUP_DIR="./backups"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Timestamp for the backup file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/$DB_NAME_backup_$TIMESTAMP.sql.gz"

# Export PGPASSWORD for pg_dump
export PGPASSWORD=$DB_PASSWORD

echo "Starting PostgreSQL database backup for $DB_NAME on $DB_HOST:$DB_PORT..."

# Perform the backup using pg_dump and gzip
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME | gzip > "$BACKUP_FILE"

# Check if the backup was successful
if [ $? -eq 0 ]; then
  echo "Database backup successful: $BACKUP_FILE"
else
  echo "Database backup failed!"
  exit 1
fi

# Unset PGPASSWORD for security
unset PGPASSWORD

echo "Backup process completed."
