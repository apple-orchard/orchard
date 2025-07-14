FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base as development

# Copy application code
COPY . .

# Create directory for ChromaDB data
RUN mkdir -p /app/chroma_db

# Expose port
EXPOSE 8011

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROMA_DB_PATH=/app/chroma_db

# Run with hot reload for development
CMD ["python", "-m", "uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8011", "--reload"]

# Production stage
FROM base as production

# Copy application code
COPY . .

# Create directory for ChromaDB data
RUN mkdir -p /app/chroma_db

# Expose port
EXPOSE 8011

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROMA_DB_PATH=/app/chroma_db

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8011/health || exit 1

# Run the application
CMD ["python", "main.py"] 