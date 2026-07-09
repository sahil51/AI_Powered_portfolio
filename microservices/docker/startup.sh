#!/bin/sh
set -e

echo "=== Starting AI Assistant Startup Check ==="

# Wait for Postgres connection using python socket check
echo "Waiting for database..."
until python -c "import socket; s = socket.socket(); s.connect(('postgres', 5432))" 2>/dev/null; do
  echo "Database is not ready yet. Sleeping for 2 seconds..."
  sleep 2
done
echo "Database is ready!"

# Run alembic migrations
echo "Running database migrations..."
if [ -f "alembic.ini" ]; then
  alembic upgrade head || echo "Database migrations deferred or failed"
else
  echo "alembic.ini not found. Skipping migrations."
fi

# Execute Uvicorn server as pid 1 to handle container signals correctly
echo "Launching FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
