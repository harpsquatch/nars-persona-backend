#!/bin/bash
set -e

# Check if we should reset the database
if [ "$RESET_DATABASE" = "true" ]; then
    echo "Resetting database completely..."
    python /app/reset_db.py
    
    # Mark all migrations as complete without running them
    echo "Marking all migrations as complete..."
    flask db stamp head || echo "Warning: Could not stamp migrations"
    
    echo "Database reset complete"
else
    echo "Running database migrations..."
    
    # Try to run migrations, but handle errors gracefully
    flask db upgrade || {
        echo "Migration failed. Attempting recovery..."
        
        # Try to stamp the current head without running migrations
        echo "Stamping current migration head..."
        flask db stamp head || echo "Warning: Could not stamp migrations"
        
        # Try to run migrations again
        echo "Retrying migrations..."
        flask db upgrade || echo "Warning: Migration still failed, but continuing startup"
    }
fi

echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 300 --keep-alive 5 "wsgi:app"
