import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import uuid
import os
from sentence_transformers import SentenceTransformer
from app.core.config import settings

class ChromaDBManager:
    def __init__(self):
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.initialize_db()

    def initialize_db(self):
        """Initialize ChromaDB client and collection"""
        try:
            self.client = chromadb.PersistentClient(
                path=settings.chroma_db_path,
            )

            # Initialize embedding model
            self.embedding_model = SentenceTransformer(settings.embedding_model)

            # Get or create collection
            try:
                self.collection = self.client.get_collection(name="documents")
            except:
                self.collection = self.client.create_collection(
                    name="documents",
                    metadata={"hnsw:space": "cosine"}
                )

            print(f"ChromaDB initialized successfully at {settings.chroma_db_path}")

        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")
            raise

    def add_documents(self, chunks: List[str], metadatas: List[Dict[str, Any]]) -> List[str]:
        """Add document chunks to ChromaDB with embeddings"""
        try:
            # Generate embeddings for chunks
            embeddings = self.embedding_model.encode(chunks).tolist()

            # Generate unique IDs for each chunk
            ids = [str(uuid.uuid4()) for _ in chunks]

            # Add to collection
            self.collection.add(
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )

            return ids

        except Exception as e:
            print(f"Error adding documents to ChromaDB: {e}")
            raise

    def query_documents(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """Query documents from ChromaDB"""
        try:
            # Generate embedding for query
            query_embedding = self.embedding_model.encode([query]).tolist()

            # Query collection
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )

            return {
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else []
            }

        except Exception as e:
            print(f"Error querying ChromaDB: {e}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            count = self.collection.count()
            return {
                "name": self.collection.name,
                "count": count,
                "metadata": self.collection.metadata
            }
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return {"error": str(e)}

    def delete_collection(self):
        """Delete the collection (for testing/cleanup)"""
        try:
            self.client.delete_collection(name="documents")
            print("Collection deleted successfully")
        except Exception as e:
            print(f"Error deleting collection: {e}")

# Global database manager instance
chroma_db = ChromaDBManager()