import logging
from typing import List, Dict, Any, Optional
from app.utils.database import chroma_db
from app.services.llm_service import llm_service
from app.utils.document_processor import document_processor
from app.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.chroma_db = chroma_db
        self.llm_service = llm_service
        self.document_processor = document_processor
    
    def query(self, question: str, max_chunks: Optional[int] = None) -> Dict[str, Any]:
        """Process a question using RAG workflow"""
        if not question.strip():
            raise ValueError("Question cannot be empty")
        
        # Use default max_chunks if not specified
        if max_chunks is None:
            max_chunks = settings.max_retrieved_chunks
        
        try:
            # Step 1: Retrieve relevant documents from ChromaDB
            retrieval_results = self.chroma_db.query_documents(
                query=question,
                n_results=max_chunks
            )
            
            if not retrieval_results["documents"]:
                return {
                    "answer": "I couldn't find any relevant information in the knowledge base to answer your question.",
                    "sources": [],
                    "metadata": {
                        "question": question,
                        "chunks_retrieved": 0,
                        "retrieval_successful": False
                    }
                }
            
            # Step 2: Generate answer using LLM
            llm_response = self.llm_service.generate_answer(
                question=question,
                context_chunks=retrieval_results["documents"],
                metadata_list=retrieval_results["metadatas"]
            )
            
            # Step 3: Combine results
            response = {
                "answer": llm_response["answer"],
                "sources": llm_response["sources"],
                "metadata": {
                    "question": question,
                    "chunks_retrieved": len(retrieval_results["documents"]),
                    "retrieval_successful": True,
                    "model": llm_response["model"],
                    "usage": llm_response["usage"],
                    "distances": retrieval_results["distances"]
                }
            }
            
            return response
            
        except Exception as e:
            raise Exception(f"Error in RAG query: {str(e)}")
    
    def ingest_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ingest raw text into the knowledge base"""
        try:
            # Process the text
            chunks = self.document_processor.process_text(text, metadata)
            
            # Extract content and metadata for ChromaDB
            chunk_contents = [chunk["content"] for chunk in chunks]
            chunk_metadatas = [chunk["metadata"] for chunk in chunks]
            
            # Add to ChromaDB
            chunk_ids = self.chroma_db.add_documents(chunk_contents, chunk_metadatas)
            
            return {
                "success": True,
                "message": "Text ingested successfully",
                "chunks_created": len(chunks),
                "chunk_ids": chunk_ids
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error ingesting text: {str(e)}",
                "chunks_created": 0
            }
    
    def ingest_file(self, file_path: str, additional_metadata: Optional[Dict[str, Any]] = None,
                    use_smart_chunking: bool = True) -> Dict[str, Any]:
        """Ingest a file into the knowledge base"""
        logger.info(f"Starting file ingestion: {file_path}")
        try:
            # Process the file
            chunks = self.document_processor.process_file(file_path, additional_metadata, use_smart_chunking)
            
            # Extract content and metadata for ChromaDB
            chunk_contents = [chunk["content"] for chunk in chunks]
            chunk_metadatas = [chunk["metadata"] for chunk in chunks]
            
            # Add to ChromaDB
            logger.info(f"Adding {len(chunks)} chunks to ChromaDB")
            chunk_ids = self.chroma_db.add_documents(chunk_contents, chunk_metadatas)
            
            logger.info(f"Successfully ingested file: {file_path} ({len(chunks)} chunks)")
            return {
                "success": True,
                "message": f"File '{file_path}' ingested successfully",
                "chunks_created": len(chunks),
                "chunk_ids": chunk_ids
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error ingesting file: {str(e)}",
                "chunks_created": 0
            }
    
    def ingest_directory(self, directory_path: str, recursive: bool = True, 
                        additional_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ingest all supported files in a directory"""
        try:
            # Process all files in the directory
            all_chunks = self.document_processor.process_directory(
                directory_path, recursive, additional_metadata
            )
            
            if not all_chunks:
                return {
                    "success": True,
                    "message": "No supported files found in directory",
                    "chunks_created": 0
                }
            
            # Extract content and metadata for ChromaDB
            chunk_contents = [chunk["content"] for chunk in all_chunks]
            chunk_metadatas = [chunk["metadata"] for chunk in all_chunks]
            
            # Add to ChromaDB
            chunk_ids = self.chroma_db.add_documents(chunk_contents, chunk_metadatas)
            
            return {
                "success": True,
                "message": f"Directory '{directory_path}' ingested successfully",
                "chunks_created": len(all_chunks),
                "chunk_ids": chunk_ids
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error ingesting directory: {str(e)}",
                "chunks_created": 0
            }
    
    def get_knowledge_base_info(self) -> Dict[str, Any]:
        """Get information about the knowledge base"""
        try:
            collection_info = self.chroma_db.get_collection_info()
            
            # Get more detailed information about the data
            total_chunks = collection_info.get("count", 0)
            
            # Get sample documents to analyze metadata
            sample_docs = []
            if total_chunks > 0:
                try:
                    # Get a sample of documents to analyze metadata
                    sample_results = self.chroma_db.query_documents(
                        query="",  # Empty query to get random samples
                        n_results=min(100, total_chunks)
                    )
                    sample_docs = sample_results.get("metadatas", [])
                except Exception:
                    sample_docs = []
            
            # Analyze metadata to categorize data
            data_summary = self._analyze_data_summary(sample_docs, total_chunks)
            
            return {
                "status": "healthy",
                "collection_name": collection_info.get("name", "Unknown"),
                "total_chunks": total_chunks,
                "collection_metadata": collection_info.get("metadata", {}),
                "data_summary": data_summary
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _analyze_data_summary(self, sample_metadatas: List[Dict[str, Any]], total_chunks: int) -> Dict[str, Any]:
        """Analyze metadata to provide a summary of ingested data"""
        summary = {
            "total_documents": 0,
            "file_types": {},
            "sources": {},
            "categories": {},
            "recent_ingestions": [],
            "estimated_size_mb": 0
        }
        
        if not sample_metadatas:
            return summary
        
        # Analyze file types and sources
        for metadata in sample_metadatas:
            # Count file types
            file_type = metadata.get("file_type", "unknown")
            summary["file_types"][file_type] = summary["file_types"].get(file_type, 0) + 1
            
            # Count sources
            source = metadata.get("source", "unknown")
            summary["sources"][source] = summary["sources"].get(source, 0) + 1
            
            # Count categories
            category = metadata.get("category", "uncategorized")
            summary["categories"][category] = summary["categories"].get(category, 0) + 1
            
            # Track recent ingestions
            ingestion_time = metadata.get("ingestion_timestamp")
            if ingestion_time:
                summary["recent_ingestions"].append({
                    "source": source,
                    "file_type": file_type,
                    "timestamp": ingestion_time
                })
        
        # Scale up counts based on sample size
        sample_size = len(sample_metadatas)
        if sample_size > 0:
            scale_factor = total_chunks / sample_size
            for file_type in summary["file_types"]:
                summary["file_types"][file_type] = int(summary["file_types"][file_type] * scale_factor)
            for source in summary["sources"]:
                summary["sources"][source] = int(summary["sources"][source] * scale_factor)
            for category in summary["categories"]:
                summary["categories"][category] = int(summary["categories"][category] * scale_factor)
        
        # Estimate total documents (assuming average chunks per document)
        avg_chunks_per_doc = 3  # Rough estimate
        summary["total_documents"] = max(1, total_chunks // avg_chunks_per_doc)
        
        # Estimate size (rough calculation: ~1KB per chunk)
        summary["estimated_size_mb"] = round(total_chunks * 1 / 1024, 2)
        
        # Sort recent ingestions by timestamp
        summary["recent_ingestions"].sort(
            key=lambda x: x.get("timestamp", ""), 
            reverse=True
        )
        summary["recent_ingestions"] = summary["recent_ingestions"][:10]  # Keep only 10 most recent
        
        return summary
    
    def test_system(self) -> Dict[str, Any]:
        """Test all components of the RAG system"""
        results = {
            "chromadb": {"status": "unknown", "error": None},
            "llm": {"status": "unknown", "error": None},
            "overall": {"status": "unknown", "error": None}
        }
        
        # Test ChromaDB
        try:
            info = self.chroma_db.get_collection_info()
            results["chromadb"]["status"] = "healthy"
            results["chromadb"]["info"] = info
        except Exception as e:
            results["chromadb"]["status"] = "error"
            results["chromadb"]["error"] = str(e)
        
        # Test LLM
        try:
            llm_test = self.llm_service.test_connection()
            results["llm"]["status"] = "healthy" if llm_test else "error"
            if not llm_test:
                results["llm"]["error"] = "Connection test failed"
        except Exception as e:
            results["llm"]["status"] = "error"
            results["llm"]["error"] = str(e)
        
        # Overall status
        if results["chromadb"]["status"] == "healthy" and results["llm"]["status"] == "healthy":
            results["overall"]["status"] = "healthy"
        else:
            results["overall"]["status"] = "error"
            results["overall"]["error"] = "One or more components failed"
        
        return results

# Global RAG service instance
rag_service = RAGService() 