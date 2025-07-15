"""
Plugin Management Commands
"""
import time
from typing import Dict, Any, List
from ..helpers import api_client, display_helper, validation_helper


def list_plugins() -> None:
    """List all available plugins"""
    try:
        response = api_client.get("/api/plugins")
        plugins = response.get("plugins", [])
        
        if not plugins:
            display_helper.print_info("No plugins found")
            return
        
        headers = ["Name", "Display Name", "Status", "Sources", "Description"]
        rows = []
        
        for plugin in plugins:
            status = "✅ Enabled" if plugin.get("enabled") else "❌ Disabled"
            if not plugin.get("initialized"):
                status = "⚠️  Not Initialized"
            
            rows.append([
                plugin.get("name", "Unknown"),
                plugin.get("display_name", "N/A"),
                status,
                str(plugin.get("total_sources", 0)),
                plugin.get("description", "No description")[:50] + "..." if len(plugin.get("description", "")) > 50 else plugin.get("description", "No description")
            ])
        
        display_helper.print_table(headers, rows, "Available Plugins")
        
    except Exception as e:
        display_helper.print_error(f"Failed to list plugins: {e}")


def show_plugin_info(plugin_name: str) -> None:
    """Show detailed information about a specific plugin"""
    try:
        response = api_client.get(f"/api/plugins/{plugin_name}/config")
        
        display_helper.print_info(f"Plugin: {plugin_name}")
        print(f"Enabled: {'Yes' if response.get('enabled') else 'No'}")
        print(f"Configuration:")
        display_helper.print_json(response.get("config", {}))
        
    except Exception as e:
        display_helper.print_error(f"Failed to get plugin info: {e}")


def list_plugin_sources(plugin_name: str) -> None:
    """List sources for a specific plugin"""
    try:
        response = api_client.get(f"/api/plugins/{plugin_name}/sources")
        sources = response.get("sources", [])
        
        if not sources:
            display_helper.print_info(f"No sources found for plugin '{plugin_name}'")
            return
        
        headers = ["ID", "Name", "Type", "Status", "Last Synced", "Sync Mode"]
        rows = []
        
        for source in sources:
            status = "✅ Enabled" if source.get("enabled") else "❌ Disabled"
            last_synced = source.get("last_synced", "Never")
            if last_synced != "Never":
                # Format the timestamp
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(last_synced.replace('Z', '+00:00'))
                    last_synced = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            rows.append([
                source.get("id", "Unknown"),
                source.get("name", "N/A"),
                source.get("type", "Unknown"),
                status,
                last_synced,
                source.get("sync_mode", "Unknown")
            ])
        
        display_helper.print_table(headers, rows, f"Sources for {plugin_name}")
        
    except Exception as e:
        display_helper.print_error(f"Failed to list sources: {e}")


def trigger_ingestion(plugin_name: str, source_id: str = None, full_sync: bool = True) -> None:
    """Trigger ingestion for a plugin"""
    try:
        # If no source_id provided, list available sources
        if not source_id:
            response = api_client.get(f"/api/plugins/{plugin_name}/sources")
            sources = response.get("sources", [])
            
            if not sources:
                display_helper.print_error(f"No sources found for plugin '{plugin_name}'")
                return
            
            print(f"\nAvailable sources for {plugin_name}:")
            for i, source in enumerate(sources, 1):
                print(f"{i}. {source.get('name', 'Unknown')} ({source.get('id', 'Unknown')})")
            
            try:
                choice = int(validation_helper.get_input("Select source number", required=True))
                if 1 <= choice <= len(sources):
                    source_id = sources[choice - 1]["id"]
                else:
                    display_helper.print_error("Invalid selection")
                    return
            except ValueError:
                display_helper.print_error("Invalid input")
                return
        
        # Confirm the action
        sync_type = "full" if full_sync else "incremental"
        if not validation_helper.confirm_action(f"Trigger {sync_type} sync for {plugin_name} source '{source_id}'?"):
            return
        
        # Trigger ingestion
        data = {
            "source_id": source_id,
            "full_sync": full_sync
        }
        
        response = api_client.post(f"/api/plugins/{plugin_name}/ingest", data)
        
        job_id = response.get("job_id")
        display_helper.print_success(f"Ingestion started! Job ID: {job_id}")
        print(f"Plugin: {response.get('plugin_name')}")
        print(f"Source: {response.get('source_id')}")
        print(f"Sync Type: {response.get('sync_type')}")
        
        # Ask if user wants to monitor the job
        if validation_helper.confirm_action("Monitor job progress?"):
            monitor_job(plugin_name, job_id)
        
    except Exception as e:
        display_helper.print_error(f"Failed to trigger ingestion: {e}")


def monitor_job(plugin_name: str, job_id: str) -> None:
    """Monitor a job's progress"""
    try:
        print(f"\nMonitoring job {job_id}...")
        print("Press Ctrl+C to stop monitoring")
        
        while True:
            try:
                response = api_client.get(f"/api/plugins/{plugin_name}/status/{job_id}")
                
                status = response.get("status", "unknown")
                total = response.get("total_documents", 0)
                processed = response.get("processed_documents", 0)
                failed = response.get("failed_documents", 0)
                
                # Clear line and show progress
                print(f"\rStatus: {status.upper()} | Processed: {processed}/{total} | Failed: {failed}", end="", flush=True)
                
                if status in ["completed", "failed", "cancelled"]:
                    print()  # New line
                    if status == "completed":
                        display_helper.print_success("Job completed successfully!")
                    elif status == "failed":
                        display_helper.print_error("Job failed!")
                        error_msg = response.get("error_message")
                        if error_msg:
                            print(f"Error: {error_msg}")
                    else:
                        display_helper.print_warning("Job was cancelled")
                    break
                
                time.sleep(2)  # Check every 2 seconds
                
            except KeyboardInterrupt:
                print("\nStopped monitoring")
                break
            except Exception as e:
                print(f"\nError monitoring job: {e}")
                break
                
    except Exception as e:
        display_helper.print_error(f"Failed to monitor job: {e}")


def list_jobs(plugin_name: str) -> None:
    """List recent jobs for a plugin (if supported)"""
    try:
        # Note: This would require an endpoint that lists jobs
        # For now, we'll show a message
        display_helper.print_info("Job listing not yet implemented")
        display_helper.print_info("Use the monitor command to check specific job status")
        
    except Exception as e:
        display_helper.print_error(f"Failed to list jobs: {e}")


def enable_plugin(plugin_name: str) -> None:
    """Enable a plugin"""
    try:
        # Get current config
        response = api_client.get(f"/api/plugins/{plugin_name}/config")
        config = response.get("config", {})
        
        # Update config
        config["enabled"] = True
        
        # Save config
        api_client.put(f"/api/plugins/{plugin_name}/config", {"config": config})
        
        display_helper.print_success(f"Plugin '{plugin_name}' enabled")
        
    except Exception as e:
        display_helper.print_error(f"Failed to enable plugin: {e}")


def disable_plugin(plugin_name: str) -> None:
    """Disable a plugin"""
    try:
        # Get current config
        response = api_client.get(f"/api/plugins/{plugin_name}/config")
        config = response.get("config", {})
        
        # Update config
        config["enabled"] = False
        
        # Save config
        api_client.put(f"/api/plugins/{plugin_name}/config", {"config": config})
        
        display_helper.print_success(f"Plugin '{plugin_name}' disabled")
        
    except Exception as e:
        display_helper.print_error(f"Failed to disable plugin: {e}")


def configure_plugin(plugin_name: str) -> None:
    """Configure a plugin interactively"""
    try:
        # Get current config
        response = api_client.get(f"/api/plugins/{plugin_name}/config")
        current_config = response.get("config", {})
        
        print(f"\nConfiguring plugin: {plugin_name}")
        print("Current configuration:")
        display_helper.print_json(current_config)
        
        # For now, we'll just show the current config
        # In a full implementation, you'd add interactive configuration
        display_helper.print_info("Interactive configuration not yet implemented")
        display_helper.print_info("Edit the rag_config.jsonc file directly to modify plugin settings")
        
    except Exception as e:
        display_helper.print_error(f"Failed to configure plugin: {e}") 