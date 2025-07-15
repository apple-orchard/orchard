import React, { useState } from 'react';
import PluginManager from './PluginManager';
import ConfigEditor from './ConfigEditor';
import SourceManager from './SourceManager';

const PluginDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'plugins' | 'config' | 'sources'>('plugins');
  const [selectedPlugin, setSelectedPlugin] = useState<string>('github');

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">RAG Plugin System</h1>
        
        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex">
              <button
                onClick={() => setActiveTab('plugins')}
                className={`py-4 px-6 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'plugins'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Plugins
              </button>
              <button
                onClick={() => setActiveTab('config')}
                className={`py-4 px-6 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'config'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Configuration
              </button>
              <button
                onClick={() => setActiveTab('sources')}
                className={`py-4 px-6 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'sources'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Sources & Ingestion
              </button>
            </nav>
          </div>
        </div>
        
        {/* Content Area */}
        <div className="bg-white rounded-lg shadow p-6">
          {activeTab === 'plugins' && <PluginManager />}
          
          {activeTab === 'config' && <ConfigEditor />}
          
          {activeTab === 'sources' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Plugin
                </label>
                <select
                  value={selectedPlugin}
                  onChange={(e) => setSelectedPlugin(e.target.value)}
                  className="w-full md:w-64 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="github">GitHub</option>
                  <option value="website" disabled>Website (Coming Soon)</option>
                </select>
              </div>
              
              <SourceManager pluginName={selectedPlugin} />
            </div>
          )}
        </div>
        
        {/* Help Section */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-blue-900 mb-2">Quick Help</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• <strong>Plugins tab:</strong> Enable/disable plugins and view their status</li>
            <li>• <strong>Configuration tab:</strong> Edit global settings and plugin configurations</li>
            <li>• <strong>Sources tab:</strong> Manage data sources and trigger ingestion</li>
            <li>• Remember to set your GITHUB_TOKEN environment variable for GitHub ingestion</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default PluginDashboard; 