FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

ENV PATH="/root/.local/bin/:$PATH"

# Copy requirements first (for better layer caching)
COPY pyproject.toml uv.lock .

# Install Python dependencies
RUN uv venv .venv
RUN uv sync --locked --no-dev

# Copy startup script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

# Development stage
FROM base AS development

# Copy application code
COPY . .

# Create directory for ChromaDB data and models
RUN mkdir -p /app/data/chroma_db /app/data/model_cache

# Expose ports for application and debugger
EXPOSE 8011 5678

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROMA_DB_PATH=/app/data/chroma_db

# Production stage
FROM base AS production

# Copy application code (excluding heavy directories via .dockerignore)
COPY . .

# Create directories for ChromaDB data and models
RUN mkdir -p /app/data/chroma_db /app/data/model_cache

# Clean up unnecessary files to reduce image size
RUN find . -type f -name "*.pyc" -delete && \
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find . -type f -name "*.pyo" -delete && \
    rm -rf .git .pytest_cache .coverage htmlcov && \
    rm -rf /root/.cache/pip /root/.cache/uv

# Expose port for application
EXPOSE 8011

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROMA_DB_PATH=/app/data/chroma_db

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8011/health || exit 1

# Run the application
ENV PATH="/app/.venv/bin:$PATH"