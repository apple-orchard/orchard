"""API routes for plugin management."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.models.plugin_schemas import (
    PluginConfigRequest, PluginConfigResponse, PluginInfoResponse,
    PluginListResponse, IngestionRequest, IngestionResponse,
    JobStatusResponse, SourceListResponse, GlobalSettingsRequest,
    GlobalSettingsResponse, ConfigurationResponse
)
from app.services.plugin_service import plugin_service
from plugins.config import plugin_config_manager

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("", response_model=PluginListResponse)
async def list_plugins():
    """List all available plugins with their status."""
    try:
        plugins = plugin_service.list_plugins()
        return PluginListResponse(plugins=plugins)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config", response_model=ConfigurationResponse)
async def get_full_config():
    """Get the full RAG configuration including all plugins."""
    try:
        config = plugin_config_manager.get_full_config()
        
        # Format plugins section
        plugins_formatted = {}
        for plugin_name, plugin_config in config.get("plugins", {}).items():
            plugins_formatted[plugin_name] = PluginConfigResponse(
                plugin_name=plugin_name,
                enabled=plugin_config.get("enabled", False),
                config=plugin_config.get("config", {})
            )
        
        return ConfigurationResponse(
            version=config.get("version", "1.0"),
            plugins=plugins_formatted,
            global_settings=GlobalSettingsResponse(**config.get("global_settings", {}))
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{plugin_name}/config", response_model=PluginConfigResponse)
async def get_plugin_config(plugin_name: str):
    """Get configuration for a specific plugin."""
    try:
        config = plugin_service.get_plugin_config(plugin_name)
        return PluginConfigResponse(
            plugin_name=plugin_name,
            enabled=config.get("enabled", False),
            config=config.get("config", {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{plugin_name}/config", response_model=PluginConfigResponse)
async def update_plugin_config(plugin_name: str, request: PluginConfigRequest):
    """Update configuration for a specific plugin."""
    try:
        config_dict = request.dict()
        plugin_service.update_plugin_config(plugin_name, config_dict)
        
        return PluginConfigResponse(
            plugin_name=plugin_name,
            enabled=request.enabled,
            config=request.config
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{plugin_name}/enable")
async def enable_plugin(plugin_name: str):
    """Enable a plugin."""
    try:
        success = plugin_service.enable_plugin(plugin_name)
        if success:
            return {"message": f"Plugin {plugin_name} enabled successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to enable plugin {plugin_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{plugin_name}/disable")
async def disable_plugin(plugin_name: str):
    """Disable a plugin."""
    try:
        success = plugin_service.disable_plugin(plugin_name)
        if success:
            return {"message": f"Plugin {plugin_name} disabled successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to disable plugin {plugin_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{plugin_name}/ingest", response_model=IngestionResponse)
async def trigger_ingestion(plugin_name: str, request: IngestionRequest):
    """Trigger ingestion for a specific plugin and source."""
    try:
        job_id = await plugin_service.ingest(
            plugin_name=plugin_name,
            source_id=request.source_id,
            full_sync=request.full_sync
        )
        
        return IngestionResponse(
            job_id=job_id,
            plugin_name=plugin_name,
            source_id=request.source_id,
            sync_type="full" if request.full_sync else "incremental"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{plugin_name}/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(plugin_name: str, job_id: str):
    """Get the status of an ingestion job."""
    try:
        job = plugin_service.get_job_status(plugin_name, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return JobStatusResponse(**job.dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{plugin_name}/jobs")
async def list_plugin_jobs(plugin_name: str):
    """List all jobs for a plugin."""
    try:
        jobs = plugin_service.list_plugin_jobs(plugin_name)
        return {"jobs": [job.dict() for job in jobs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{plugin_name}/sources", response_model=SourceListResponse)
async def get_plugin_sources(plugin_name: str):
    """Get configured sources for a plugin."""
    try:
        sources = await plugin_service.get_plugin_sources(plugin_name)
        return SourceListResponse(sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings/global", response_model=GlobalSettingsResponse)
async def get_global_settings():
    """Get global plugin settings."""
    try:
        settings = plugin_service.get_global_settings()
        return GlobalSettingsResponse(**settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings/global", response_model=GlobalSettingsResponse)
async def update_global_settings(request: GlobalSettingsRequest):
    """Update global plugin settings."""
    try:
        settings_dict = request.dict()
        plugin_service.update_global_settings(settings_dict)
        return GlobalSettingsResponse(**settings_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 