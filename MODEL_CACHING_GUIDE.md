# Model Caching Guide

This guide explains how to set up local model caching to avoid downloading models every time Docker containers start.

## 🎯 Why Model Caching?

### Problems Solved:
- ✅ **Slow startup**: No more waiting for model downloads on each container restart
- ✅ **Bandwidth usage**: Download models once, reuse forever
- ✅ **Offline development**: Work without internet once models are cached
- ✅ **Consistent versions**: Same model files across all environments

### Model Sizes:
- `all-mpnet-base-v2`: ~420MB
- `all-MiniLM-L6-v2`: ~80MB
- `all-MiniLM-L12-v2`: ~120MB

## 🚀 Quick Setup

### One-Command Setup:
```bash
./setup_models.sh
```

This will:
1. Download your current embedding model (`all-mpnet-base-v2`)
2. Set up Docker volume mounting
3. Configure environment variables
4. Verify the setup

## 📁 How It Works

### Directory Structure:
```
orchard/
├── model_cache/           # ← Local model storage
│   ├── models--sentence-transformers--all-mpnet-base-v2/
│   └── ...
├── docker-compose.yml     # ← Updated with volume mounts
└── setup_models.sh        # ← Setup script
```

### Docker Mounting:
```yaml
volumes:
  - ./model_cache:/app/model_cache  # Mount local cache into container
```

### Environment Variables:
```yaml
environment:
  - TRANSFORMERS_CACHE=/app/model_cache
  - SENTENCE_TRANSFORMERS_HOME=/app/model_cache
  - HF_HOME=/app/model_cache
```

## 🔧 Manual Setup

### Step 1: Download Models
```bash
# Download default model
uv run python download_models.py

# Download specific model
uv run python download_models.py download --model all-MiniLM-L6-v2

# List available models
uv run python download_models.py list
```

### Step 2: Run Docker
```bash
# Development
docker-compose -f docker-compose.dev.yml up

# Production
docker-compose up
```

## 📊 Model Management

### Check Cache Status:
```bash
# List cached models
./setup_models.sh list

# Check cache size
./setup_models.sh size

# Verify setup
./setup_models.sh verify
```

### Download Additional Models:
```bash
# Download specific model
./setup_models.sh download sentence-transformers/all-MiniLM-L12-v2

# Or use the Python script directly
uv run python download_models.py download --model paraphrase-mpnet-base-v2
```

### Clear Cache:
```bash
./setup_models.sh clear
```

## 🐳 Docker Configuration

### Volume Mounts Added:
Both `docker-compose.yml` and `docker-compose.dev.yml` now include:

```yaml
volumes:
  - ./model_cache:/app/model_cache  # Model cache
  - ./chroma_db:/app/chroma_db      # Database
  - ./documents:/app/documents       # Documents
```

### Environment Variables Added:
```yaml
environment:
  # Model cache configuration
  - TRANSFORMERS_CACHE=/app/model_cache
  - SENTENCE_TRANSFORMERS_HOME=/app/model_cache
  - HF_HOME=/app/model_cache
```

## 📈 Performance Benefits

### Before (No Caching):
```
Container startup: ~2-5 minutes
- Download model: 2-4 minutes
- Load model: 30 seconds
- Start API: 30 seconds
```

### After (With Caching):
```
Container startup: ~30 seconds
- Load cached model: 10 seconds
- Start API: 20 seconds
```

## 🔍 Verification

### Check If Models Are Cached:
1. **Start container**: `docker-compose up`
2. **Look for log**: `"📁 Using cached model from: /app/model_cache"`
3. **No download logs**: Should not see "📥 Downloading model"

### Test Model Loading:
```bash
# Test the cached model
uv run python -c "
from sentence_transformers import SentenceTransformer
import os
os.environ['SENTENCE_TRANSFORMERS_HOME'] = './model_cache'
model = SentenceTransformer('all-mpnet-base-v2', cache_folder='./model_cache')
print('✅ Model loaded successfully!')
print(f'📊 Embedding dimension: {model.get_sentence_embedding_dimension()}')
"
```

## 🛠️ Troubleshooting

### Model Not Found:
```bash
# Re-download the model
./setup_models.sh download all-mpnet-base-v2

# Verify it's cached
./setup_models.sh list
```

### Container Still Downloading:
1. Check volume mount: `docker-compose config`
2. Verify environment variables are set
3. Check model cache directory exists: `ls -la model_cache/`

### Permission Issues:
```bash
# Fix permissions
chmod -R 755 model_cache/

# Or recreate with proper permissions
rm -rf model_cache/
./setup_models.sh setup
```

### Cache Size Too Large:
```bash
# Check what's using space
./setup_models.sh size

# Clear old models
./setup_models.sh clear

# Download only needed model
./setup_models.sh download all-mpnet-base-v2
```

## 🔄 Migration from Old Setup

### If You Have Existing Containers:
```bash
# Stop containers
docker-compose down

# Set up model caching
./setup_models.sh setup

# Clear old embeddings (dimension mismatch fix)
rm -rf chroma_db/

# Restart with cached models
docker-compose up
```

## 📚 Advanced Usage

### Multiple Models:
```bash
# Download multiple models for experimentation
./setup_models.sh download all-mpnet-base-v2
./setup_models.sh download all-MiniLM-L12-v2
./setup_models.sh download paraphrase-mpnet-base-v2

# Switch between models by changing EMBEDDING_MODEL env var
```

### Custom Cache Location:
```bash
# Use custom cache directory
uv run python download_models.py --cache-dir /path/to/custom/cache download --model MODEL_NAME

# Update docker-compose.yml to mount the custom directory
```

### CI/CD Integration:
```bash
# In your CI pipeline
./setup_models.sh setup

# Build Docker image with pre-cached models
docker build -t your-app .
```

## 🎉 Benefits Summary

✅ **Faster Development**: No waiting for model downloads
✅ **Offline Capability**: Work without internet after initial setup
✅ **Bandwidth Savings**: Download once, use everywhere
✅ **Consistent Environment**: Same model versions across team
✅ **Production Ready**: Same setup works for production deployments

---

## Quick Reference

```bash
# Initial setup
./setup_models.sh setup

# Download additional model
./setup_models.sh download MODEL_NAME

# Check status
./setup_models.sh list
./setup_models.sh size

# Start containers (now with cached models)
docker-compose up
```