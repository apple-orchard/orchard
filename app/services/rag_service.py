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
from openai.types.chat.chat_completion_user_message_param import ChatCompletionUserMessageParam
from app.services.ingestion_jobs import job_manager, JobType, IngestionJob

logger = app.core.logging.logger.getChild('services.rag_service')

class RAGService:
    def __init__(self):
        self.chroma_db = chroma_db
        self.document_processor = document_processor

    async def query(self, question: str, max_chunks: Optional[int] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a question using RAG workflow"""
        rag_context = RAGContextProvider(title="RAG Context")
        query_agent = QueryAgentFactory.build(rag_context)
        qa_agent = QAAgentFactory.build(rag_context)

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

        if not search_results["documents"]:
            yield {
                "answer": "I couldn't find any relevant information in the knowledge base to answer your question.",
                "sources": [],
                "metadata": {
                    "question": question,
                    "chunks_retrieved": 0,
                    "retrieval_successful": False
                }
            }
            return

        # Update context with retrieved chunks
        rag_context.chunks = [
            ChunkItem(content=doc, metadata={"chunk_id": id, "distance": dist})
            for doc, id, dist in zip(search_results["documents"], search_results["ids"], search_results["distances"])
        ]

        # Step 2: Generate answer using QA agent
        qa_output = qa_agent.run_async(RAGQuestionAnsweringAgentInputSchema(question=question))

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

    def ingest_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ingest raw text into the knowledge base"""
        try:
            self.logger.info(f"Starting text ingestion - {len(text)} characters")

            # Process the text
            self.logger.info("Processing text into chunks...")
            chunks = self.document_processor.process_text(text, metadata)
            self.logger.info(f"Created {len(chunks)} chunks from text")

            # Extract content and metadata for ChromaDB
            self.logger.info("Preparing chunks for vector database...")
            chunk_contents = [chunk["content"] for chunk in chunks]
            chunk_metadatas = [serialize_metadata(chunk["metadata"]) for chunk in chunks]

            # Add to ChromaDB
            self.logger.info("Adding chunks to vector database...")
            chunk_ids = self.chroma_db.add_documents(chunk_contents, chunk_metadatas)

            self.logger.info(f"✅ Text ingestion completed successfully - {len(chunks)} chunks stored")
            return {
                "success": True,
                "message": "Text ingested successfully",
                "chunks_created": len(chunks),
                "chunk_ids": chunk_ids
            }

        except Exception as e:
            self.logger.error(f"❌ Text ingestion failed: {str(e)}")
            return {
                "success": False,
                "message": f"Error ingesting text: {str(e)}",
                "chunks_created": 0
            }

    def ingest_file(self, file_path: str, additional_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ingest a file into the knowledge base"""
        try:
            self.logger.info(f"Starting file ingestion: {file_path}")

            # Process the file
            self.logger.info(f"Extracting text and processing file: {file_path}")
            chunks = self.document_processor.process_file(file_path, additional_metadata)
            self.logger.info(f"Created {len(chunks)} chunks from file")

            # Extract content and metadata for ChromaDB
            self.logger.info("Preparing chunks for vector database...")
            chunk_contents = [chunk["content"] for chunk in chunks]
            chunk_metadatas = [serialize_metadata(chunk["metadata"]) for chunk in chunks]

            # Add to ChromaDB
            self.logger.info("Adding chunks to vector database...")
            chunk_ids = self.chroma_db.add_documents(chunk_contents, chunk_metadatas)

            self.logger.info(f"✅ File ingestion completed successfully: {file_path} - {len(chunks)} chunks stored")
            return {
                "success": True,
                "message": f"File '{file_path}' ingested successfully",
                "chunks_created": len(chunks),
                "chunk_ids": chunk_ids
            }

        except Exception as e:
            self.logger.error(f"❌ File ingestion failed for {file_path}: {str(e)}")
            return {
                "success": False,
                "message": f"Error ingesting file: {str(e)}",
                "chunks_created": 0
            }

    def ingest_directory(self, directory_path: str, recursive: bool = True,
                        additional_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ingest all supported files in a directory"""
        try:
            mode = "recursive" if recursive else "non-recursive"
            self.logger.info(f"Starting directory ingestion ({mode}): {directory_path}")

            # Process all files in the directory
            self.logger.info(f"Scanning directory for supported files: {directory_path}")
            all_chunks = self.document_processor.process_directory(
                directory_path, recursive, additional_metadata
            )

            if not all_chunks:
                self.logger.warning(f"No supported files found in directory: {directory_path}")
                return {
                    "success": True,
                    "message": "No supported files found in directory",
                    "chunks_created": 0
                }

            self.logger.info(f"Processed directory - total chunks created: {len(all_chunks)}")

            # Extract content and metadata for ChromaDB
            self.logger.info("Preparing chunks for vector database...")
            chunk_contents = [chunk["content"] for chunk in all_chunks]
            chunk_metadatas = [serialize_metadata(chunk["metadata"]) for chunk in all_chunks]

            # Add to ChromaDB
            self.logger.info("Adding chunks to vector database...")
            chunk_ids = self.chroma_db.add_documents(chunk_contents, chunk_metadatas)

            self.logger.info(f"✅ Directory ingestion completed successfully: {directory_path} - {len(all_chunks)} chunks stored")
            return {
                "success": True,
                "message": f"Directory '{directory_path}' ingested successfully",
                "chunks_created": len(all_chunks),
                "chunk_ids": chunk_ids
            }

        except Exception as e:
            self.logger.error(f"❌ Directory ingestion failed for {directory_path}: {str(e)}")
            return {
                "success": False,
                "message": f"Error ingesting directory: {str(e)}",
                "chunks_created": 0
            }

    # Async ingestion methods using job system

    def ingest_text_async(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start async text ingestion job."""
        job_metadata = {
            "text_length": len(text),
            "user_metadata": metadata or {}
        }

        job_id = job_manager.create_job(JobType.TEXT_INGESTION, job_metadata)

        def text_task(job: IngestionJob, text: str, metadata: Optional[Dict[str, Any]]):
            job.update_progress(0, 1, f"Starting text ingestion - {len(text):,} characters")

            try:
                # Use the existing synchronous method
                result = self.ingest_text(text, metadata)

                job.update_progress(1, 1, f"Text ingested successfully - {result.get('chunks_created', 0)} chunks created")
                return result
            except Exception as e:
                raise Exception(f"Text ingestion failed: {str(e)}")

        job_manager.submit_job(job_id, text_task, text, metadata)
        return job_id

    def ingest_file_async(self, file_path: str, additional_metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start async file ingestion job."""
        job_metadata = {
            "file_path": file_path,
            "user_metadata": additional_metadata or {}
        }

        job_id = job_manager.create_job(JobType.FILE_INGESTION, job_metadata)

        def file_task(job: IngestionJob, file_path: str, metadata: Optional[Dict[str, Any]]):
            import os
            import logging
            logger = logging.getLogger(__name__)

            # Get file info for progress tracking
            try:
                file_size = os.path.getsize(file_path)
                file_size_mb = file_size / (1024 * 1024)
                job.update_progress(0, 1, f"Starting file ingestion: {os.path.basename(file_path)} ({file_size_mb:.2f} MB)")
            except:
                job.update_progress(0, 1, f"Starting file ingestion: {os.path.basename(file_path)}")

            try:
                # Use the existing synchronous method (which now has detailed logging)
                result = self.ingest_file(file_path, metadata)

                chunks_created = result.get('chunks_created', 0)
                job.update_progress(1, 1, f"File ingested successfully: {os.path.basename(file_path)} - {chunks_created} chunks created")
                return result
            finally:
                # Clean up temporary files (those with temp names)
                if "tmp" in file_path and os.path.exists(file_path):
                    try:
                        os.unlink(file_path)
                        logger.info(f"Cleaned up temporary file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up temp file {file_path}: {e}")

        job_manager.submit_job(job_id, file_task, file_path, additional_metadata)
        return job_id

    def ingest_directory_async(self, directory_path: str, recursive: bool = True,
                              additional_metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start async directory ingestion job."""
        import os

        # Count files to estimate progress
        file_count = 0
        supported_extensions = {'.pdf', '.docx', '.doc', '.txt'}
        if os.path.exists(directory_path):
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in supported_extensions):
                        file_count += 1
                if not recursive:
                    break

        job_metadata = {
            "directory_path": directory_path,
            "recursive": recursive,
            "estimated_files": file_count,
            "user_metadata": additional_metadata or {}
        }

        job_id = job_manager.create_job(JobType.DIRECTORY_INGESTION, job_metadata)

        def directory_task(job: IngestionJob, dir_path: str, recursive: bool, metadata: Optional[Dict[str, Any]]):
            mode = "recursively" if recursive else "non-recursively"
            job.update_progress(0, file_count, f"Starting directory ingestion ({mode}): {os.path.basename(dir_path)} - {file_count} files found")

            # Use the existing synchronous method (which now has detailed progress logging)
            result = self.ingest_directory(dir_path, recursive, metadata)

            chunks_created = result.get('chunks_created', 0)
            success_msg = f"Directory ingested successfully: {os.path.basename(dir_path)} - {chunks_created} chunks from {file_count} files"
            job.update_progress(file_count, file_count, success_msg)
            return result

        job_manager.submit_job(job_id, directory_task, directory_path, recursive, additional_metadata)
        return job_id

    def ingest_batch_async(self, messages: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start async batch ingestion job."""
        job_metadata = {
            "message_count": len(messages),
            "user_metadata": metadata or {}
        }

        job_id = job_manager.create_job(JobType.BATCH_INGESTION, job_metadata)

        def batch_task(job: IngestionJob, messages: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]]):
            total_messages = len(messages)
            job.update_progress(0, total_messages, f"Starting batch ingestion - {total_messages} messages to process")

            total_chunks = 0
            errors = []
            successful_messages = 0

            for idx, msg in enumerate(messages):
                if job.status.value == "cancelled":  # Check if job was cancelled
                    break

                text = msg.get("text", "")
                if not text:
                    errors.append(f"Message at index {idx} missing 'text' field.")
                    continue

                # Merge message metadata and request metadata
                combined_metadata = dict(metadata) if metadata else {}
                if msg.get("metadata"):
                    combined_metadata.update(msg["metadata"])

                try:
                    result = self.ingest_text(text, combined_metadata)
                    if result.get("success"):
                        chunks_created = result.get("chunks_created", 0)
                        total_chunks += chunks_created
                        successful_messages += 1
                    else:
                        errors.append(f"Error ingesting message at index {idx}: {result.get('message')}")
                except Exception as e:
                    errors.append(f"Error ingesting message at index {idx}: {str(e)}")

                # Update progress with more detail
                progress_msg = f"Processed {idx + 1}/{total_messages} messages - {successful_messages} successful, {total_chunks} chunks created"
                if errors:
                    progress_msg += f", {len(errors)} errors"
                job.update_progress(idx + 1, total_messages, progress_msg)

            success = len(errors) == 0
            if success:
                final_message = f"Batch ingestion completed successfully - {successful_messages} messages, {total_chunks} chunks created"
            else:
                final_message = f"Batch ingestion completed with {len(errors)} errors - {successful_messages} successful messages, {total_chunks} chunks created"

            return {
                "success": success,
                "message": final_message,
                "chunks_created": total_chunks,
                "successful_messages": successful_messages,
                "total_messages": total_messages,
                "errors": errors
            }

        job_manager.submit_job(job_id, batch_task, messages, metadata)
        return job_id

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
            query_agent_test = self._test_agent(QueryAgentFactory.build(RAGContextProvider(title="RAG Context")))
            qa_agent_test = self._test_agent(QAAgentFactory.build(RAGContextProvider(title="RAG Context"), is_async=False))
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