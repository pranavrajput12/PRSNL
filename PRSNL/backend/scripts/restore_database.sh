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

# Check if a backup file is provided as an argument
if [ -z "$1" ]; then
  echo "Usage: $0 <backup_file.sql.gz>"
  echo "Available backups in $BACKUP_DIR:"
  ls -lh "$BACKUP_DIR"/*.sql.gz 2>/dev/null || echo "No backup files found."
  exit 1
fi

BACKUP_FILE="$1"

# Check if the backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
  echo "Error: Backup file '$BACKUP_FILE' not found!"
  exit 1
}

# Export PGPASSWORD for pg_restore
export PGPASSWORD=$DB_PASSWORD

echo "Starting PostgreSQL database restore for $DB_NAME on $DB_HOST:$DB_PORT from $BACKUP_FILE..."

# Warning before proceeding
read -p "WARNING: This will overwrite the current database '$DB_NAME'. Are you sure? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Restore cancelled."
    exit 0
fi

# Drop existing database and create a new one
# This ensures a clean restore without conflicts
PG_CONN_STRING="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/postgres"

echo "Dropping existing database '$DB_NAME'..."
psql $PG_CONN_STRING -c "DROP DATABASE IF EXISTS \"$DB_NAME\";"
if [ $? -ne 0 ]; then
  echo "Error: Failed to drop database '$DB_NAME'."
  unset PGPASSWORD
  exit 1
fi

echo "Creating new database '$DB_NAME'..."
psql $PG_CONN_STRING -c "CREATE DATABASE \"$DB_NAME\" OWNER \"$DB_USER\";"
if [ $? -ne 0 ]; then
  echo "Error: Failed to create database '$DB_NAME'."
  unset PGPASSWORD
  exit 1
fi

# Perform the restore using pg_restore (or gunzip and psql for plain SQL dumps)
gunzip -c "$BACKUP_FILE" | psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME

# Check if the restore was successful
if [ $? -eq 0 ]; then
  echo "Database restore successful from $BACKUP_FILE"
else
  echo "Database restore failed!"
  exit 1
fi

# Unset PGPASSWORD for security
unset PGPASSWORD

echo "Restore process completed."
