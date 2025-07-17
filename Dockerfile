FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS base

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
COPY pyproject.toml uv.lock .

# Install Python dependencies
RUN uv venv .venv
RUN uv sync --locked

# Development stage
FROM base AS development

# Copy application code
COPY . .

# Set up all plugin virtual environments
RUN python plugins/plugin_setup.py build

# Create directory for ChromaDB data
RUN mkdir -p /app/chroma_db

# Expose port
EXPOSE 8011

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROMA_DB_PATH=/app/chroma_db

# Run with hot reload for development
CMD ["uv", "run", "uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8011", "--reload"]

# Production stage
FROM base AS production

# Copy application code
COPY . .

# Set up all plugin virtual environments
RUN python plugins/plugin_setup.py build

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
ENV PATH="/app/.venv/bin:$PATH"
CMD ["/app/entrypoint.sh"]