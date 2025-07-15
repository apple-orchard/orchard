import React, { useState, useEffect } from 'react';
import { pluginAPI } from '../services/api';
import { PluginInfo, PluginListResponse } from '../types';

const PluginManager: React.FC = () => {
  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPlugin, setSelectedPlugin] = useState<string | null>(null);

  useEffect(() => {
    loadPlugins();
  }, []);

  const loadPlugins = async () => {
    try {
      setLoading(true);
      const response = await pluginAPI.listPlugins();
      setPlugins(response.plugins);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTogglePlugin = async (pluginName: string, currentEnabled: boolean) => {
    try {
      if (currentEnabled) {
        await pluginAPI.disablePlugin(pluginName);
      } else {
        await pluginAPI.enablePlugin(pluginName);
      }
      await loadPlugins(); // Reload to get updated status
    } catch (err: any) {
      setError(`Failed to toggle plugin: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
        Error: {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold mb-4">Plugin Manager</h2>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {plugins.map((plugin) => (
          <div
            key={plugin.name}
            className={`border rounded-lg p-4 cursor-pointer transition-all ${
              selectedPlugin === plugin.name ? 'border-blue-500 shadow-lg' : 'border-gray-300'
            } ${!plugin.enabled ? 'opacity-60' : ''}`}
            onClick={() => setSelectedPlugin(plugin.name)}
          >
            <div className="flex justify-between items-start mb-2">
              <h3 className="text-lg font-semibold">{plugin.display_name}</h3>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleTogglePlugin(plugin.name, plugin.enabled);
                }}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  plugin.enabled
                    ? 'bg-green-100 text-green-800 hover:bg-green-200'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {plugin.enabled ? 'Enabled' : 'Disabled'}
              </button>
            </div>
            
            <p className="text-sm text-gray-600 mb-2">{plugin.description}</p>
            
            <div className="space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-500">Version:</span>
                <span className="font-medium">{plugin.version}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Sources:</span>
                <span className="font-medium">{plugin.total_sources}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Status:</span>
                <span className={`font-medium ${plugin.initialized ? 'text-green-600' : 'text-yellow-600'}`}>
                  {plugin.initialized ? 'Initialized' : 'Not Initialized'}
                </span>
              </div>
            </div>
            
            {plugin.capabilities.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="flex flex-wrap gap-1">
                  {plugin.capabilities.map((cap) => (
                    <span
                      key={cap}
                      className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded"
                    >
                      {cap}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {plugins.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No plugins available
        </div>
      )}
    </div>
  );
};

export default PluginManager; 