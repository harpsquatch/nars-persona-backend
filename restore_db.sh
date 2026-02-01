#!/bin/bash
if [ -z "$1" ]
then
    echo "Please provide backup file name"
    echo "Available backups:"
    ls -l /opt/backups/narsbeauty_backup_*
    exit 1
fi

echo "Restoring from backup: $1"
docker exec -i nars-persona-be-db-1 mysql -u root -pmysql -e "CREATE DATABASE IF NOT EXISTS narsbeauty;"
docker exec -i nars-persona-be-db-1 mysql -u root -pmysql narsbeauty < "/opt/backups/$1" 