#!/bin/bash
set -e

echo "Starting Container"

# Check if we should reset/initialize the database
if [ "$RESET_DATABASE" = "true" ]; then
    echo "Resetting database completely..."
    python /app/reset_db.py
    echo "Database reset complete"
elif [ "$INIT_DATABASE" = "true" ]; then
    echo "Initializing database schema..."
    python /app/init_db.py || echo "Warning: Database initialization had issues, but continuing..."
fi

# Verify database connection before starting
echo "Verifying database connection..."
python -c "
from app import app, db
with app.app_context():
    try:
        db.engine.connect()
        print('✓ Database connection successful')
    except Exception as e:
        print(f'✗ Database connection failed: {e}')
        exit(1)
"

echo "Starting Gunicorn server on port ${PORT:-8080}..."
exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 300 --keep-alive 5 --access-logfile - --error-logfile - "wsgi:app"
