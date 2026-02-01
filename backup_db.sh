#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"
BACKUP_FILE="narsbeauty_backup_${TIMESTAMP}.sql"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create the backup
docker exec nars-persona-be-db-1 mysqldump -u root -pmysql narsbeauty > "$BACKUP_DIR/$BACKUP_FILE"

# Keep only last 5 backups
ls -t $BACKUP_DIR/narsbeauty_backup_* | tail -n +6 | xargs -r rm

echo "Backup created: $BACKUP_FILE" 