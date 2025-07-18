#!/usr/bin/env python3
"""
Model Download and Cache Manager
Downloads and caches embedding models locally for Docker container mounting.
"""

import os
import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer
import shutil

# Model cache configuration
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "huggingface" / "transformers"
LOCAL_MODEL_CACHE = Path("./model_cache")

class ModelManager:
    def __init__(self, cache_dir: Path = LOCAL_MODEL_CACHE):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def download_model(self, model_name: str, force_download: bool = False) -> Path:
        """Download a model and return its cache path."""
        print(f"📥 Downloading model: {model_name}")

        # Set cache directory for this download
        os.environ['TRANSFORMERS_CACHE'] = str(self.cache_dir)
        os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(self.cache_dir)

        try:
            # Download the model (this caches it locally)
            model = SentenceTransformer(model_name, cache_folder=str(self.cache_dir))

            model_path = self.cache_dir / model_name.replace('/', '--')
            print(f"✅ Model downloaded to: {model_path}")

            # Test the model to ensure it works
            print("🧪 Testing model...")
            test_embeddings = model.encode(["test sentence"])
            print(f"✅ Model test successful - embedding dimension: {len(test_embeddings[0])}")

            return model_path

        except Exception as e:
            print(f"❌ Error downloading model {model_name}: {e}")
            raise

    def list_cached_models(self) -> list:
        """List all cached models."""
        if not self.cache_dir.exists():
            return []

        models = []
        for item in self.cache_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                models.append(item.name.replace('--', '/'))

        return models

    def get_cache_size(self) -> int:
        """Get total cache size in bytes."""
        total_size = 0
        if self.cache_dir.exists():
            for dirpath, dirnames, filenames in os.walk(self.cache_dir):
                for filename in filenames:
                    filepath = Path(dirpath) / filename
                    total_size += filepath.stat().st_size
        return total_size

    def format_size(self, size_bytes: int) -> str:
        """Format bytes as human readable."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def clear_cache(self):
        """Clear all cached models."""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            print("🗑️  Cache cleared")


def main():
    """Main function for model management."""
    import argparse

    parser = argparse.ArgumentParser(description="Manage model cache for Docker containers")
    parser.add_argument("action", choices=["download", "list", "size", "clear"],
                       help="Action to perform")
    parser.add_argument("--model", help="Model name to download")
    parser.add_argument("--cache-dir", default=LOCAL_MODEL_CACHE,
                       help=f"Cache directory (default: {LOCAL_MODEL_CACHE})")
    parser.add_argument("--force", action="store_true",
                       help="Force re-download even if model exists")

    args = parser.parse_args()

    manager = ModelManager(Path(args.cache_dir))

    if args.action == "download":
        if not args.model:
            print("❌ --model required for download action")
            sys.exit(1)

        print(f"🚀 Downloading model: {args.model}")
        print(f"📁 Cache directory: {manager.cache_dir}")

        try:
            model_path = manager.download_model(args.model, args.force)
            print(f"\n✅ Success! Model cached at: {model_path}")
            print(f"💾 Total cache size: {manager.format_size(manager.get_cache_size())}")
        except Exception as e:
            print(f"❌ Download failed: {e}")
            sys.exit(1)

    elif args.action == "list":
        models = manager.list_cached_models()
        cache_size = manager.get_cache_size()

        print(f"📚 Cached Models ({manager.format_size(cache_size)}):")
        print(f"📁 Cache directory: {manager.cache_dir}")

        if models:
            for i, model in enumerate(models, 1):
                print(f"  {i}. {model}")
        else:
            print("  No models cached")

    elif args.action == "size":
        cache_size = manager.get_cache_size()
        print(f"💾 Cache size: {manager.format_size(cache_size)}")
        print(f"📁 Cache directory: {manager.cache_dir}")

    elif args.action == "clear":
        response = input("⚠️  Clear all cached models? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            manager.clear_cache()
            print("✅ Cache cleared")
        else:
            print("❌ Operation cancelled")


if __name__ == "__main__":
    # If run without arguments, download the default model
    if len(sys.argv) == 1:
        print("🚀 Downloading default embedding model...")
        manager = ModelManager()

        # Download the current embedding model
        from app.core.config import settings
        model_name = settings.embedding_model

        print(f"📥 Downloading: {model_name}")
        manager.download_model(model_name)

        print(f"\n🎉 Setup complete!")
        print(f"📁 Models cached in: {manager.cache_dir}")
        print(f"🐳 Ready for Docker mounting!")
    else:
        main()