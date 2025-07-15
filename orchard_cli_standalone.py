#!/usr/bin/env python3
"""
Orchard RAG CLI - Standalone Version
This version has minimal dependencies and can run without the full environment.
"""
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
import argparse
from typing import Dict, Any, Optional, List


class SimpleAPIClient:
    """Simple API client using urllib instead of requests"""
    
    def __init__(self, base_url: str = "http://localhost:8011"):
        self.base_url = base_url.rstrip('/')
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an HTTP request to the API"""
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Orchard-CLI/1.0.0'
        }
        
        request_data = None
        if data:
            request_data = json.dumps(data).encode('utf-8')
        
        req = urllib.request.Request(url, data=request_data, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_msg = f"HTTP {e.code}: {e.reason}"
            try:
                error_data = json.loads(e.read().decode('utf-8'))
                if 'detail' in error_data:
                    error_msg = error_data['detail']
            except:
                pass
            raise Exception(f"API request failed: {error_msg}")
        except urllib.error.URLError as e:
            raise Exception(f"Connection failed: {e.reason}")
    
    def get(self, endpoint: str) -> Dict[str, Any]:
        """Make a GET request"""
        return self._make_request('GET', endpoint)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a POST request"""
        return self._make_request('POST', endpoint, data)


def print_table(headers: List[str], rows: List[List[str]], title: Optional[str] = None) -> None:
    """Print a formatted table"""
    if title:
        print(f"\n{title}")
        print("=" * len(title))
    
    if not rows:
        print("No data to display")
        return
    
    # Calculate column widths
    col_widths = []
    for i, header in enumerate(headers):
        max_width = len(header)
        for row in rows:
            if i < len(row):
                max_width = max(max_width, len(str(row[i])))
        col_widths.append(max_width)
    
    # Print header
    header_row = " | ".join(header.ljust(width) for header, width in zip(headers, col_widths))
    print(header_row)
    print("-" * len(header_row))
    
    # Print rows
    for row in rows:
        formatted_row = " | ".join(str(cell).ljust(width) for cell, width in zip(row, col_widths))
        print(formatted_row)


# Initialize API client
api_client = SimpleAPIClient()


# Command functions
def health_check():
    """Check system health"""
    try:
        response = api_client.get("/health")
        status = response.get("status", "unknown")
        if status == "healthy":
            print("✅ System is healthy")
        else:
            print(f"❌ System status: {status}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")


def list_plugins():
    """List all available plugins"""
    try:
        response = api_client.get("/api/plugins")
        plugins = response.get("plugins", [])
        
        if not plugins:
            print("ℹ️  No plugins found")
            return
        
        headers = ["Name", "Display Name", "Status", "Sources", "Description"]
        rows = []
        
        for plugin in plugins:
            status = "✅ Enabled" if plugin.get("enabled") else "❌ Disabled"
            if not plugin.get("initialized"):
                status = "⚠️  Not Initialized"
            
            description = plugin.get("description", "No description")
            if len(description) > 50:
                description = description[:50] + "..."
            
            rows.append([
                plugin.get("name", "Unknown"),
                plugin.get("display_name", "N/A"),
                status,
                str(plugin.get("total_sources", 0)),
                description
            ])
        
        print_table(headers, rows, "Available Plugins")
        
    except Exception as e:
        print(f"❌ Failed to list plugins: {e}")


def trigger_ingestion(plugin_name: str, source_id: Optional[str] = None, full_sync: bool = True):
    """Trigger ingestion for a plugin"""
    try:
        # If no source_id provided, list available sources
        if not source_id:
            response = api_client.get(f"/api/plugins/{plugin_name}/sources")
            sources = response.get("sources", [])
            
            if not sources:
                print(f"❌ No sources found for plugin '{plugin_name}'")
                return
            
            print(f"\nAvailable sources for {plugin_name}:")
            for i, source in enumerate(sources, 1):
                print(f"{i}. {source.get('name', 'Unknown')} ({source.get('id', 'Unknown')})")
            
            try:
                choice = int(input("Select source number: "))
                if 1 <= choice <= len(sources):
                    source_id = sources[choice - 1]["id"]
                else:
                    print("❌ Invalid selection")
                    return
            except ValueError:
                print("❌ Invalid input")
                return
        
        # Confirm the action
        sync_type = "full" if full_sync else "incremental"
        confirm = input(f"Trigger {sync_type} sync for {plugin_name} source '{source_id}'? (y/N): ")
        if confirm.lower() != 'y':
            return
        
        # Trigger ingestion
        data = {
            "source_id": source_id,
            "full_sync": full_sync
        }
        
        response = api_client.post(f"/api/plugins/{plugin_name}/ingest", data)
        
        job_id = response.get("job_id")
        print(f"✅ Ingestion started! Job ID: {job_id}")
        print(f"Plugin: {response.get('plugin_name')}")
        print(f"Source: {response.get('source_id')}")
        print(f"Sync Type: {response.get('sync_type')}")
        
    except Exception as e:
        print(f"❌ Failed to trigger ingestion: {e}")


def system_info():
    """Get system information"""
    try:
        response = api_client.get("/knowledge-base/info")
        
        print("ℹ️  System Information")
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
        print(f"❌ Failed to get system info: {e}")


def query_documents(question: str, max_chunks: int = 5):
    """Query the knowledge base"""
    try:
        if not question:
            question = input("Enter your question: ").strip()
            if not question:
                print("❌ Question cannot be empty")
                return
        
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
        
    except Exception as e:
        print(f"❌ Query failed: {e}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="orchard",
        description="Orchard RAG System CLI - Standalone Version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  orchard health                    # Check system health
  orchard plugins list              # List all plugins
  orchard plugins ingest github     # Trigger GitHub ingestion
  orchard rag query "What is RAG?"  # Query the knowledge base
  orchard rag info                  # Show system information
        """
    )
    
    # Global options
    parser.add_argument(
        "--api-url",
        default="http://localhost:8011",
        help="API base URL (default: http://localhost:8011)"
    )
    
    # Create subparsers
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Health command
    subparsers.add_parser("health", help="Check system health")
    
    # RAG commands
    rag_parser = subparsers.add_parser("rag", help="RAG system commands")
    rag_subparsers = rag_parser.add_subparsers(dest="rag_command")
    
    rag_subparsers.add_parser("info", help="Show system information")
    
    query_parser = rag_subparsers.add_parser("query", help="Query the knowledge base")
    query_parser.add_argument("question", nargs="?", help="Question to ask")
    query_parser.add_argument("--max-chunks", type=int, default=5, help="Maximum chunks to retrieve")
    
    # Plugin commands
    plugin_parser = subparsers.add_parser("plugins", help="Plugin management commands")
    plugin_subparsers = plugin_parser.add_subparsers(dest="plugin_command")
    
    plugin_subparsers.add_parser("list", help="List all plugins")
    
    ingest_parser = plugin_subparsers.add_parser("ingest", help="Trigger plugin ingestion")
    ingest_parser.add_argument("plugin_name", help="Name of the plugin")
    ingest_parser.add_argument("--source-id", help="Source ID to ingest (optional)")
    ingest_parser.add_argument("--incremental", action="store_true", help="Perform incremental sync")
    
    args = parser.parse_args()
    
    # Update API client URL if specified
    if args.api_url:
        api_client.base_url = args.api_url.rstrip('/')
    
    # Handle commands
    try:
        if args.command == "health":
            health_check()
        elif args.command == "rag":
            if args.rag_command == "info":
                system_info()
            elif args.rag_command == "query":
                query_documents(args.question, args.max_chunks)
            else:
                parser.print_help()
        elif args.command == "plugins":
            if args.plugin_command == "list":
                list_plugins()
            elif args.plugin_command == "ingest":
                full_sync = not args.incremental
                trigger_ingestion(args.plugin_name, args.source_id, full_sync)
            else:
                parser.print_help()
        else:
            parser.print_help()
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 