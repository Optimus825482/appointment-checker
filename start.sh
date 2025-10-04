#!/bin/bash
set -e

# Port kontrolü
if [ -z "$PORT" ]; then
  export PORT=5000
fi

echo "🚀 Starting application on port $PORT"

# Gunicorn başlat
exec gunicorn src.app:app \
  --bind 0.0.0.0:$PORT \
  --timeout 120 \
  --workers 1 \
  --log-level info \
  --access-logfile - \
  --error-logfile -