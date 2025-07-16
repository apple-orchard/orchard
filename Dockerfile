FROM python:3.13-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin/:$PATH"

# Copy requirements first (for better layer caching)
COPY pyproject.toml .

# Install Python dependencies
RUN uv sync

# Copy startup script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

# Development stage
FROM base AS development

# Copy application code
COPY . .

# Create directory for ChromaDB data
RUN mkdir -p /app/chroma_db

# Expose port for application and debugger
EXPOSE 8011
EXPOSE 5678

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROMA_DB_PATH=/app/chroma_db

# Production stage
FROM base AS production

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
