"""
Orchard RAG CLI - Main Entry Point
"""
import argparse
import sys
import logging
from typing import List, Optional

from .helpers import display_helper, api_client
from .commands import plugins, rag

# Import and setup logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.logging_config import setup_logging


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser"""
    parser = argparse.ArgumentParser(
        prog="orchard",
        description="Orchard RAG System CLI - Manage your RAG system from the command line",
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
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    # Create subparsers for different command groups
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands"
    )
    
    # Health command
    health_parser = subparsers.add_parser(
        "health",
        help="Check system health"
    )
    
    # RAG commands
    rag_parser = subparsers.add_parser(
        "rag",
        help="RAG system commands"
    )
    rag_subparsers = rag_parser.add_subparsers(dest="rag_command")
    
    # RAG info
    rag_subparsers.add_parser(
        "info",
        help="Show system information"
    )
    
    # RAG test
    rag_subparsers.add_parser(
        "test",
        help="Test all system components"
    )
    
    # RAG query
    query_parser = rag_subparsers.add_parser(
        "query",
        help="Query the knowledge base"
    )
    query_parser.add_argument(
        "question",
        nargs="?",
        help="Question to ask"
    )
    query_parser.add_argument(
        "--max-chunks",
        type=int,
        default=5,
        help="Maximum chunks to retrieve (default: 5)"
    )
    
    # RAG ingest text
    ingest_text_parser = rag_subparsers.add_parser(
        "ingest-text",
        help="Ingest text content"
    )
    ingest_text_parser.add_argument(
        "text",
        nargs="?",
        help="Text content to ingest"
    )
    
    # RAG ingest file
    ingest_file_parser = rag_subparsers.add_parser(
        "ingest-file",
        help="Ingest a file"
    )
    ingest_file_parser.add_argument(
        "file_path",
        nargs="?",
        help="Path to file to ingest"
    )
    ingest_file_parser.add_argument(
        "--no-smart-chunking",
        action="store_true",
        help="Disable smart chunking for PDFs"
    )
    
    # Models commands
    models_parser = rag_subparsers.add_parser(
        "models",
        help="List available models"
    )
    
    # Pull model
    pull_parser = rag_subparsers.add_parser(
        "pull-model",
        help="Pull a model from Ollama"
    )
    pull_parser.add_argument(
        "model_name",
        help="Name of model to pull"
    )
    
    # Plugin commands
    plugin_parser = subparsers.add_parser(
        "plugins",
        help="Plugin management commands"
    )
    plugin_subparsers = plugin_parser.add_subparsers(dest="plugin_command")
    
    # List plugins
    plugin_subparsers.add_parser(
        "list",
        help="List all plugins"
    )
    
    # Show plugin info
    info_parser = plugin_subparsers.add_parser(
        "info",
        help="Show plugin information"
    )
    info_parser.add_argument(
        "plugin_name",
        help="Name of the plugin"
    )
    
    # List plugin sources
    sources_parser = plugin_subparsers.add_parser(
        "sources",
        help="List plugin sources"
    )
    sources_parser.add_argument(
        "plugin_name",
        help="Name of the plugin"
    )
    
    # Trigger ingestion
    ingest_parser = plugin_subparsers.add_parser(
        "ingest",
        help="Trigger plugin ingestion"
    )
    ingest_parser.add_argument(
        "plugin_name",
        help="Name of the plugin"
    )
    ingest_parser.add_argument(
        "--source-id",
        help="Source ID to ingest (optional)"
    )
    ingest_parser.add_argument(
        "--incremental",
        action="store_true",
        help="Perform incremental sync instead of full sync"
    )
    
    # Monitor job
    monitor_parser = plugin_subparsers.add_parser(
        "monitor",
        help="Monitor a job"
    )
    monitor_parser.add_argument(
        "plugin_name",
        help="Name of the plugin"
    )
    monitor_parser.add_argument(
        "job_id",
        help="Job ID to monitor"
    )
    
    # Enable plugin
    enable_parser = plugin_subparsers.add_parser(
        "enable",
        help="Enable a plugin"
    )
    enable_parser.add_argument(
        "plugin_name",
        help="Name of the plugin"
    )
    
    # Disable plugin
    disable_parser = plugin_subparsers.add_parser(
        "disable",
        help="Disable a plugin"
    )
    disable_parser.add_argument(
        "plugin_name",
        help="Name of the plugin"
    )
    
    # Configure plugin
    config_parser = plugin_subparsers.add_parser(
        "config",
        help="Configure a plugin"
    )
    config_parser.add_argument(
        "plugin_name",
        help="Name of the plugin"
    )
    
    return parser


def handle_rag_commands(args: argparse.Namespace) -> None:
    """Handle RAG system commands"""
    if args.rag_command == "info":
        rag.system_info()
    elif args.rag_command == "test":
        rag.test_system()
    elif args.rag_command == "query":
        rag.query_documents(args.question, args.max_chunks)
    elif args.rag_command == "ingest-text":
        rag.ingest_text(args.text)
    elif args.rag_command == "ingest-file":
        rag.ingest_file(args.file_path, use_smart_chunking=not args.no_smart_chunking)
    elif args.rag_command == "models":
        rag.list_models()
    elif args.rag_command == "pull-model":
        rag.pull_model(args.model_name)
    else:
        display_helper.print_error("Unknown RAG command")


def handle_plugin_commands(args: argparse.Namespace) -> None:
    """Handle plugin management commands"""
    if args.plugin_command == "list":
        plugins.list_plugins()
    elif args.plugin_command == "info":
        plugins.show_plugin_info(args.plugin_name)
    elif args.plugin_command == "sources":
        plugins.list_plugin_sources(args.plugin_name)
    elif args.plugin_command == "ingest":
        full_sync = not args.incremental
        plugins.trigger_ingestion(args.plugin_name, args.source_id, full_sync)
    elif args.plugin_command == "monitor":
        plugins.monitor_job(args.plugin_name, args.job_id)
    elif args.plugin_command == "enable":
        plugins.enable_plugin(args.plugin_name)
    elif args.plugin_command == "disable":
        plugins.disable_plugin(args.plugin_name)
    elif args.plugin_command == "config":
        plugins.configure_plugin(args.plugin_name)
    else:
        display_helper.print_error("Unknown plugin command")


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entry point"""
    # Set up logging
    log_level = logging.DEBUG if "-v" in (args or sys.argv) or "--verbose" in (args or sys.argv) else logging.INFO
    setup_logging(level=log_level)
    
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    # Update API client URL if specified
    if parsed_args.api_url:
        api_client.base_url = parsed_args.api_url.rstrip('/')
    
    # Handle commands
    try:
        if parsed_args.command == "health":
            rag.health_check()
        elif parsed_args.command == "rag":
            handle_rag_commands(parsed_args)
        elif parsed_args.command == "plugins":
            handle_plugin_commands(parsed_args)
        else:
            # No command specified, show help
            parser.print_help()
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        if parsed_args.verbose:
            raise
        else:
            display_helper.print_error(f"An error occurred: {e}")
            return 1


if __name__ == "__main__":
    sys.exit(main()) 