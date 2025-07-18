import app.core.logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from app.utils.database import chroma_db
from app.utils.document_processor import document_processor
from app.utils.document_processor import serialize_metadata
from app.core.config import settings
from app.agents.query_agent import QueryAgentFactory, RAGQueryAgentInputSchema
from app.agents.qa_agent import QAAgentFactory, RAGQuestionAnsweringAgentInputSchema
from app.core.context_providers import RAGContextProvider, ChunkItem
from atomic_agents.agents.base_agent import BaseAgent
from app.agents.query_agent import QueryAgent
from app.agents.qa_agent import QAAgent
from openai.types.chat.chat_completion_user_message_param import ChatCompletionUserMessageParam

logger = app.core.logging.logger.getChild('services.rag_service')

class RAGService:
    def __init__(self):
        self.chroma_db = chroma_db
        self.document_processor = document_processor
    
    async def query(
        self,
        question: str,
        query_agent: QueryAgent,
        qa_agent: QAAgent,
        max_chunks: Optional[int] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a question using RAG workflow"""

        # Register context providers for agents
        rag_context = RAGContextProvider(title="RAG Context")
        qa_agent.register_context_provider("rag_context", rag_context)
        query_agent.register_context_provider("rag_context", rag_context)

        if not question.strip():
            raise ValueError("Question cannot be empty")

        query_output = query_agent.run(RAGQueryAgentInputSchema(user_message=question))

        # Use default max_chunks if not specified
        if max_chunks is None:
            max_chunks = settings.max_retrieved_chunks
        
        # Step 1: Retrieve relevant documents from ChromaDB
        search_results = self.chroma_db.query_documents(
            query=query_output.model_dump()["query"],
            n_results=max_chunks
        )

        # Update context with retrieved chunks
        rag_context.chunks = [
            ChunkItem(content=doc, metadata={"chunk_id": id, "distance": dist})
            for doc, id, dist in zip(search_results["documents"], search_results["ids"], search_results["distances"])
        ]
        
        # Step 2: Generate answer using QA agent
        user_input = RAGQuestionAnsweringAgentInputSchema(question=question)

        # Run QA agent
        qa_output = qa_agent.run_async(user_input)

        try:
            # qa_agent.run_async() actually returns an async generator
            current_answer = ""
            async for partial_response in qa_output:
                response_json: Dict[str, Any] = partial_response.model_dump() if partial_response is not None else {}
                if response_json["answer"] is not None:
                    if response_json["answer"] != current_answer:
                        current_answer = response_json["answer"]
                        yield {
                            "answer": current_answer,
                            "sources": response_json["sources"] or [],
                            "metadata": {
                                "question": question,
                                "chunks_retrieved": len(search_results["documents"]),
                                "distances": search_results["distances"]
                            }
                        }
        except Exception as e:
            logger.error(f"Error in query: {e}")
            yield {
                "answer": "I'm sorry, I'm having trouble answering your question. Please try again.",
                "sources": [],
                "metadata": {
                    "question": question,
                    "chunks_retrieved": len(search_results["documents"]),
                    "distances": search_results["distances"]
                }
            }
    
    def ingest_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ingest raw text into the knowledge base"""
        try:
            # Process the text
            chunks = self.document_processor.process_text(text, metadata)
            
            # Extract content and metadata for ChromaDB
            chunk_contents = [chunk["content"] for chunk in chunks]
            chunk_metadatas = [serialize_metadata(chunk["metadata"]) for chunk in chunks]
            
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
    
    def ingest_file(self, file_path: str, additional_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ingest a file into the knowledge base"""
        try:
            # Process the file
            chunks = self.document_processor.process_file(file_path, additional_metadata)
            
            # Extract content and metadata for ChromaDB
            chunk_contents = [chunk["content"] for chunk in chunks]
            chunk_metadatas = [serialize_metadata(chunk["metadata"]) for chunk in chunks]
            
            # Add to ChromaDB
            chunk_ids = self.chroma_db.add_documents(chunk_contents, chunk_metadatas)
            
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
            chunk_metadatas = [serialize_metadata(chunk["metadata"]) for chunk in all_chunks]
            
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

    def _test_agent(self, agent: BaseAgent) -> bool:
        try:
            # Test with a simple ping-like request
            response = agent.client.chat.completions.create(
                messages=[
                    ChatCompletionUserMessageParam(
                        role="user",
                        content="Hello, this is a test message. Please respond with just 'OK'.",
                    )
                ],
                response_model=None,
            )
            return True
        except Exception as e:
            print(f"Ollama connection test failed: {e}")
            return False
    
    def test_system(self) -> Dict[str, Any]:
        """Test all components of the RAG system"""
        results = {
            "chromadb": {"status": "unknown", "error": None},
            "agents": {"status": "unknown", "error": None},
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
        
        # Test agents
        try:
            query_agent_test = self._test_agent(QueryAgentFactory.build())
            qa_agent_test = self._test_agent(QAAgentFactory.build(is_async=False))
            results["agents"]["status"] = "healthy" if query_agent_test and qa_agent_test else "error"
            if not query_agent_test:
                results["agents"]["error"] = "Query agent connection test failed"
            if not qa_agent_test:
                results["agents"]["error"] = "QA agent connection test failed"
        except Exception as e:
            results["agents"]["status"] = "error"
            results["agents"]["error"] = str(e)
        
        # Overall status
        if results["chromadb"]["status"] == "healthy" and results["agents"]["status"] == "healthy":
            results["overall"]["status"] = "healthy"
        else:
            results["overall"]["status"] = "error"
            results["overall"]["error"] = "One or more components failed"
        
        return results

# Global RAG service instance
rag_service = RAGService() 