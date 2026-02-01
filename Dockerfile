# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory to /app (backend code will be copied directly into /app)
WORKDIR /app

# Flask CLI + Python env vars
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    FLASK_ENV=production \
    FLASK_APP=wsgi.py \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything from backend directory into container's /app
COPY . /app/

# Expose port (Railway default)
EXPOSE 8080

# Healthcheck for container management
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Copy reset_db.py instead of creating it
COPY reset_db.py /app/reset_db.py
RUN chmod +x /app/reset_db.py

# Copy start script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Start container using the script
CMD ["/app/start.sh"]
