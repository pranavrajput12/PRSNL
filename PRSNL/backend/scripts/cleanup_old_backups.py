import datetime
import os
import re

# Configuration
BACKUP_DIR = "./backups"  # Relative to the script's execution location
DAYS_TO_KEEP = 7

def cleanup_old_backups(backup_dir=BACKUP_DIR, days_to_keep=DAYS_TO_KEEP):
    """Deletes backup files older than a specified number of days."""
    print(f"Cleaning up old backups in {os.path.abspath(backup_dir)}...")
    
    if not os.path.exists(backup_dir):
        print(f"Backup directory {backup_dir} does not exist. Exiting.")
        return

    now = datetime.datetime.now()
    deleted_count = 0

    for filename in os.listdir(backup_dir):
        filepath = os.path.join(backup_dir, filename)
        
        # Ensure it's a file and matches the backup naming convention
        if os.path.isfile(filepath) and re.match(r".*_backup_\d{8}_\d{6}\.sql\.gz", filename):
            try:
                # Extract timestamp from filename (e.g., prsnl_db_backup_20231027_123456.sql.gz)
                match = re.search(r'_backup_(\d{8}_\d{6})\.sql\.gz', filename)
                if match:
                    date_str = match.group(1)
                    file_date = datetime.datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                    
                    if (now - file_date).days > days_to_keep:
                        os.remove(filepath)
                        print(f"Deleted old backup: {filename}")
                        deleted_count += 1
                else:
                    print(f"Skipping non-conforming file: {filename}")
            except Exception as e:
                print(f"Error processing file {filename}: {e}")
    
    print(f"Cleanup complete. Deleted {deleted_count} old backup files.")

if __name__ == "__main__":
    # This script is expected to be run from the PRSNL/backend directory
    # So, the BACKUP_DIR should be relative to that.
    # For example, if backups are in PRSNL/backend/backups, then BACKUP_DIR = "./backups"
    
    # Change to the directory where the script is located to ensure relative paths work
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    cleanup_old_backups()
