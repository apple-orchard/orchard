"""
RAG System Commands
"""
from typing import Dict, Any
from ..helpers import api_client, display_helper, validation_helper


def health_check() -> None:
    """Check system health"""
    try:
        response = api_client.get("/health")
        
        status = response.get("status", "unknown")
        if status == "healthy":
            display_helper.print_success("System is healthy")
        else:
            display_helper.print_error(f"System status: {status}")
        
        # Show additional info if available
        if "version" in response:
            print(f"Version: {response['version']}")
        if "uptime" in response:
            print(f"Uptime: {response['uptime']}")
            
    except Exception as e:
        display_helper.print_error(f"Health check failed: {e}")


def system_info() -> None:
    """Get system information"""
    try:
        response = api_client.get("/knowledge-base/info")
        
        display_helper.print_info("System Information")
        print(f"Status: {response.get('status', 'Unknown')}")
        print(f"Collection: {response.get('collection_name', 'Unknown')}")
        print(f"Total Chunks: {response.get('total_chunks', 0):,}")
        
        # Show data summary if available
        data_summary = response.get("data_summary", {})
        if data_summary:
            print(f"Estimated Documents: {data_summary.get('total_documents', 0):,}")
            print(f"Estimated Size: {data_summary.get('estimated_size_mb', 0)} MB")
            
            # Show file types
            file_types = data_summary.get("file_types", {})
            if file_types:
                print("\nFile Types:")
                for file_type, count in file_types.items():
                    print(f"  {file_type}: {count:,} chunks")
            
            # Show sources
            sources = data_summary.get("sources", {})
            if sources:
                print("\nSources:")
                for source, count in sources.items():
                    print(f"  {source}: {count:,} chunks")
        
    except Exception as e:
        display_helper.print_error(f"Failed to get system info: {e}")


def test_system() -> None:
    """Test all system components"""
    try:
        response = api_client.get("/test")
        
        display_helper.print_info("System Test Results")
        
        # Test ChromaDB
        chromadb_status = response.get("chromadb", {})
        if chromadb_status.get("status") == "healthy":
            display_helper.print_success("ChromaDB: Healthy")
        else:
            display_helper.print_error(f"ChromaDB: {chromadb_status.get('error', 'Unknown error')}")
        
        # Test agents
        agents_status = response.get("agents", {})
        if agents_status.get("status") == "healthy":
            display_helper.print_success("Agents: Healthy")
        else:
            display_helper.print_error(f"Agents: {agents_status.get('error', 'Unknown error')}")
        
        # Overall status
        overall_status = response.get("overall", {})
        if overall_status.get("status") == "healthy":
            display_helper.print_success("Overall: All systems healthy")
        else:
            display_helper.print_error(f"Overall: {overall_status.get('error', 'Unknown error')}")
        
    except Exception as e:
        display_helper.print_error(f"System test failed: {e}")


def list_models() -> None:
    """List available Ollama models"""
    try:
        response = api_client.get("/models")
        models = response.get("models", [])
        
        if not models:
            display_helper.print_info("No models found")
            return
        
        headers = ["Name", "Size", "Modified"]
        rows = []
        
        for model in models:
            rows.append([
                model.get("name", "Unknown"),
                model.get("size", "N/A"),
                model.get("modified", "N/A")
            ])
        
        display_helper.print_table(headers, rows, "Available Models")
        
    except Exception as e:
        display_helper.print_error(f"Failed to list models: {e}")


def pull_model(model_name: str) -> None:
    """Pull a model from Ollama"""
    try:
        if not validation_helper.confirm_action(f"Pull model '{model_name}'?"):
            return
        
        response = api_client.post(f"/models/pull?model_name={model_name}")
        
        message = response.get("message", "Model pulled successfully")
        display_helper.print_success(message)
        
    except Exception as e:
        display_helper.print_error(f"Failed to pull model: {e}")


def query_documents(question: str, max_chunks: int = 5) -> None:
    """Query the knowledge base"""
    try:
        if not question:
            question = validation_helper.get_input("Enter your question", required=True)
        
        data = {
            "question": question,
            "max_chunks": max_chunks
        }
        
        response = api_client.post("/query", data)
        
        # Display the answer
        print(f"\n🤖 Answer:")
        print(f"{response.get('answer', 'No answer provided')}")
        
        # Display sources
        sources = response.get("sources", [])
        if sources:
            print(f"\n📚 Sources:")
            for i, source in enumerate(sources, 1):
                filename = source.get("filename", "Unknown")
                chunk_index = source.get("chunk_index")
                if chunk_index is not None:
                    print(f"{i}. {filename} (chunk {chunk_index})")
                else:
                    print(f"{i}. {filename}")
        
        # Display metadata
        metadata = response.get("metadata", {})
        if metadata:
            print(f"\n📊 Metadata:")
            print(f"Chunks retrieved: {metadata.get('chunks_retrieved', 0)}")
            if metadata.get("model"):
                print(f"Model used: {metadata['model']}")
        
    except Exception as e:
        display_helper.print_error(f"Query failed: {e}")


def ingest_text(text: str = None, metadata: Dict[str, Any] = None) -> None:
    """Ingest text content"""
    try:
        if not text:
            text = validation_helper.get_input("Enter text content", required=True)
        
        data = {
            "text_content": text
        }
        
        if metadata:
            data["metadata"] = metadata
        
        response = api_client.post("/ingest/text", data)
        
        if response.get("success"):
            chunks_created = response.get("chunks_created", 0)
            display_helper.print_success(f"Text ingested successfully! {chunks_created} chunks created.")
        else:
            display_helper.print_error(f"Ingestion failed: {response.get('message', 'Unknown error')}")
        
    except Exception as e:
        display_helper.print_error(f"Failed to ingest text: {e}")


def ingest_file(file_path: str, metadata: Dict[str, Any] = None) -> None:
    """Ingest a file"""
    try:
        if not file_path:
            file_path = validation_helper.get_input("Enter file path", required=True)
        
        if not validation_helper.validate_file_path(file_path):
            display_helper.print_error(f"File not found: {file_path}")
            return
        
        data = {
            "file_path": file_path
        }
        
        if metadata:
            data["metadata"] = metadata
        
        response = api_client.post("/ingest/file", data)
        
        if response.get("success"):
            chunks_created = response.get("chunks_created", 0)
            display_helper.print_success(f"File ingested successfully! {chunks_created} chunks created.")
        else:
            display_helper.print_error(f"Ingestion failed: {response.get('message', 'Unknown error')}")
        
    except Exception as e:
        display_helper.print_error(f"Failed to ingest file: {e}") 