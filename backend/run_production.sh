#!/bin/bash
# Production server startup script for DC Medical Cannabis Application
# Uses Gunicorn WSGI server for production deployment

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export FLASK_ENV=production
export DISABLE_MODEL_SOURCE_CHECK=True

# Start Gunicorn with production settings
# - 2 workers (adjust based on CPU cores)
# - 120 second timeout (for slow OCR operations)
# - Bind to all interfaces on port 5001
exec gunicorn \
    --bind 0.0.0.0:5001 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    app:app
