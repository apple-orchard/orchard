#!/usr/bin/env python3
"""
Embedding Model Migration Script

This script helps migrate from one embedding model to another by:
1. Backing up the current ChromaDB data
2. Clearing the old embeddings
3. Re-embedding all documents with the new model

Use this when changing the EMBEDDING_MODEL configuration.
"""

import os
import shutil
import sys
from pathlib import Path
from datetime import datetime
import json

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings
from app.utils.database import chroma_db


def backup_chroma_data():
    """Create a backup of the current ChromaDB data."""
    if not Path(settings.chroma_db_path).exists():
        print("No existing ChromaDB data found. No backup needed.")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{settings.chroma_db_path}_backup_{timestamp}"

    print(f"Creating backup at: {backup_path}")
    shutil.copytree(settings.chroma_db_path, backup_path)
    print(f"✅ Backup created successfully")

    return backup_path


def export_documents():
    """Export all documents and metadata before migration."""
    try:
        # Get collection info
        info = chroma_db.get_collection_info()
        print(f"Found {info.get('count', 0)} documents in collection")

        if info.get('count', 0) == 0:
            print("No documents to export.")
            return []

        # Get all documents (ChromaDB doesn't have a direct "get all" method)
        # We'll use a very broad query to get everything
        results = chroma_db.collection.get(
            include=["documents", "metadatas", "ids"]
        )

        documents = []
        for i, doc in enumerate(results["documents"]):
            documents.append({
                "id": results["ids"][i],
                "content": doc,
                "metadata": results["metadatas"][i]
            })

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = f"documents_export_{timestamp}.json"

        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)

        print(f"✅ Exported {len(documents)} documents to: {export_file}")
        return documents

    except Exception as e:
        print(f"❌ Error exporting documents: {e}")
        return []


def clear_embeddings():
    """Clear all embeddings from ChromaDB."""
    try:
        print("Clearing old embeddings...")
        chroma_db.delete_collection()
        print("✅ Old embeddings cleared")
    except Exception as e:
        print(f"❌ Error clearing embeddings: {e}")
        raise


def re_embed_documents(documents):
    """Re-embed all documents with the new model."""
    if not documents:
        print("No documents to re-embed.")
        return

    print(f"Re-embedding {len(documents)} documents with new model: {settings.embedding_model}")

    # Reinitialize the database (this will create a new collection with the new model)
    chroma_db.initialize_db()

    # Process documents in batches
    batch_size = 50
    total_batches = (len(documents) + batch_size - 1) // batch_size

    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        batch_number = (i // batch_size) + 1

        print(f"Processing batch {batch_number}/{total_batches}...")

        try:
            # Extract content and metadata
            contents = [doc["content"] for doc in batch]
            metadatas = [doc["metadata"] for doc in batch]

            # Add to ChromaDB (this will generate new embeddings)
            chroma_db.add_documents(contents, metadatas)

            print(f"  ✅ Batch {batch_number} completed")

        except Exception as e:
            print(f"  ❌ Error processing batch {batch_number}: {e}")
            # Continue with next batch
            continue

    print("✅ Re-embedding completed!")


def verify_migration():
    """Verify the migration was successful."""
    try:
        info = chroma_db.get_collection_info()
        count = info.get('count', 0)
        print(f"✅ Migration verification: {count} documents in new embedding space")

        # Test a query to make sure everything works
        if count > 0:
            test_results = chroma_db.query_documents("test query", n_results=1)
            if test_results["documents"]:
                print("✅ Query test successful - embeddings are working correctly")
            else:
                print("⚠️  Query test returned no results - this might be normal if documents don't match 'test query'")

    except Exception as e:
        print(f"❌ Error during verification: {e}")


def main():
    """Main migration process."""
    print("=" * 60)
    print("🔄 ChromaDB Embedding Model Migration")
    print("=" * 60)
    print(f"New embedding model: {settings.embedding_model}")
    print(f"ChromaDB path: {settings.chroma_db_path}")
    print()

    # Confirm with user
    response = input("This will replace all existing embeddings. Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Migration cancelled.")
        return

    try:
        # Step 1: Export current documents
        print("\n📤 Step 1: Exporting current documents...")
        documents = export_documents()

        # Step 2: Create backup
        print("\n💾 Step 2: Creating backup...")
        backup_path = backup_chroma_data()

        # Step 3: Clear old embeddings
        print("\n🗑️  Step 3: Clearing old embeddings...")
        clear_embeddings()

        # Step 4: Re-embed with new model
        print("\n🔄 Step 4: Re-embedding with new model...")
        re_embed_documents(documents)

        # Step 5: Verify migration
        print("\n✅ Step 5: Verifying migration...")
        verify_migration()

        print("\n" + "=" * 60)
        print("🎉 Migration completed successfully!")
        print("=" * 60)

        if backup_path:
            print(f"💾 Backup available at: {backup_path}")
        print(f"📊 Documents exported to: documents_export_*.json")
        print("\n⚠️  Remember to restart your application to use the new embeddings!")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\n🔄 Restore from backup if needed:")
        if 'backup_path' in locals() and backup_path:
            print(f"   rm -rf {settings.chroma_db_path}")
            print(f"   mv {backup_path} {settings.chroma_db_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()