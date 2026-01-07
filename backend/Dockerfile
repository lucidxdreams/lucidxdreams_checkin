# Dockerfile for Railway deployment
# Includes all system dependencies for barcode scanning

FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PORT=5000

# Install system dependencies for barcode scanning libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libzbar0 \
        gcc \
        g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the application - use shell form to expand $PORT
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
