import React, { useState, useEffect, useCallback } from 'react';
import { pluginAPI } from '../services/api';
import { SourceInfo, JobStatus } from '../types';

interface SourceManagerProps {
  pluginName: string;
}

const SourceManager: React.FC<SourceManagerProps> = ({ pluginName }) => {
  const [sources, setSources] = useState<SourceInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeJobs, setActiveJobs] = useState<Record<string, JobStatus>>({});
  const [syncing, setSyncing] = useState<Record<string, boolean>>({});
  const [refreshing, setRefreshing] = useState(false);

  const loadSources = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await pluginAPI.getPluginSources(pluginName);
      setSources(response.sources);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [pluginName]);

  const updateJobStatuses = useCallback(async () => {
    const updates: Record<string, JobStatus> = {};
    let hasUpdates = false;

    for (const [sourceId, job] of Object.entries(activeJobs)) {
      if (job.status === 'running' || job.status === 'pending') {
        try {
          const status = await pluginAPI.getJobStatus(pluginName, job.id);
          updates[sourceId] = status;
          hasUpdates = true;
          
          // If job is complete, we'll remove it from active jobs after a delay
          if (status.status === 'completed' || status.status === 'failed') {
            setTimeout(() => {
              setActiveJobs((prev) => {
                const newJobs = { ...prev };
                delete newJobs[sourceId];
                return newJobs;
              });
              // Reload sources to get updated last_synced time
              loadSources();
            }, 5000);
          }
        } catch (err) {
          console.error('Failed to update job status:', err);
        }
      }
    }

    if (hasUpdates) {
      setActiveJobs((prev) => ({ ...prev, ...updates }));
    }
  }, [activeJobs, pluginName, loadSources]);

  useEffect(() => {
    loadSources();
  }, [loadSources]);

  useEffect(() => {
    // Poll for job updates every 2 seconds
    const interval = setInterval(updateJobStatuses, 2000);
    return () => clearInterval(interval);
  }, [updateJobStatuses]);

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      setError(null);
      await loadSources();
    } finally {
      setRefreshing(false);
    }
  };

  const handleSync = async (sourceId: string, fullSync: boolean) => {
    try {
      setSyncing({ ...syncing, [sourceId]: true });
      setError(null);
      const response = await pluginAPI.triggerIngestion(pluginName, sourceId, fullSync);
      
      // Start tracking this job
      const jobStatus: JobStatus = {
        id: response.job_id,
        plugin_name: response.plugin_name,
        status: 'pending',
        total_documents: 0,
        processed_documents: 0,
        failed_documents: 0,
        metadata: {
          sync_type: response.sync_type,
          source_id: sourceId
        },
      };
      
      setActiveJobs({ ...activeJobs, [sourceId]: jobStatus });
    } catch (err: any) {
      setError(`Failed to start sync: ${err.message}`);
    } finally {
      setSyncing({ ...syncing, [sourceId]: false });
    }
  };

  const getJobProgressMessage = (job: JobStatus): string => {
    if (job.status === 'pending') {
      return 'Initializing ingestion...';
    } else if (job.status === 'running') {
      const metadata = job.metadata || {};
      if (metadata.current_action) {
        switch (metadata.current_action) {
          case 'connecting':
            return 'Connecting to GitHub...';
          case 'fetching':
            return `Fetching repository files... (${job.processed_documents}/${job.total_documents})`;
          case 'chunking':
            return `Creating chunks from documents... (${job.processed_documents}/${job.total_documents})`;
          case 'embedding':
            return `Generating embeddings... (${job.processed_documents}/${job.total_documents})`;
          case 'storing':
            return `Storing in vector database... (${job.processed_documents}/${job.total_documents})`;
          default:
            return `Processing... (${job.processed_documents}/${job.total_documents})`;
        }
      }
      return `Processing documents... (${job.processed_documents}/${job.total_documents})`;
    } else if (job.status === 'completed') {
      return `Completed! Processed ${job.processed_documents} documents`;
    } else if (job.status === 'failed') {
      return `Failed: ${job.error_message || 'Unknown error'}`;
    }
    return job.status;
  };

  if (loading && !refreshing) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-semibold">Configured Sources</h3>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 flex items-center space-x-2"
        >
          <svg 
            className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>{refreshing ? 'Refreshing...' : 'Refresh Sources'}</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}
      
      {sources.length === 0 ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <p className="text-gray-700 mb-4">
            No sources found for {pluginName} plugin.
          </p>
          <p className="text-sm text-gray-600 mb-4">
            Make sure you have:
          </p>
          <ol className="text-sm text-gray-600 text-left max-w-md mx-auto list-decimal list-inside space-y-1">
            <li>Enabled the {pluginName} plugin in the Configuration tab</li>
            <li>Added at least one repository configuration</li>
            <li>Saved the configuration</li>
            <li>Clicked "Refresh Sources" above</li>
          </ol>
        </div>
      ) : (
        <div className="space-y-4">
          {sources.map((source) => {
            const job = activeJobs[source.id];
            const isActive = job && (job.status === 'running' || job.status === 'pending');
            
            return (
              <div
                key={source.id}
                className="bg-white rounded-lg border border-gray-200 p-6"
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h4 className="text-lg font-medium">{source.name}</h4>
                    <p className="text-sm text-gray-600">ID: {source.id}</p>
                  </div>
                  <div className="flex flex-col space-y-2">
                    <button
                      onClick={() => handleSync(source.id, true)}
                      disabled={isActive || syncing[source.id]}
                      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                      </svg>
                      <span>Start Full Ingestion</span>
                    </button>
                    <button
                      onClick={() => handleSync(source.id, false)}
                      disabled={isActive || syncing[source.id]}
                      className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                    >
                      Incremental Sync
                    </button>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Type:</span>
                    <span className="ml-2 font-medium">{source.type}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Sync Mode:</span>
                    <span className="ml-2 font-medium">{source.sync_mode}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Last Synced:</span>
                    <span className="ml-2 font-medium">
                      {source.last_synced
                        ? new Date(source.last_synced).toLocaleString()
                        : 'Never'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Status:</span>
                    <span className={`ml-2 font-medium ${source.enabled ? 'text-green-600' : 'text-red-600'}`}>
                      {source.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                </div>
                
                {/* Show active job status */}
                {job && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Ingestion Progress:</span>
                        <span className={`text-sm px-2 py-0.5 rounded ${
                          job.status === 'running' ? 'bg-blue-100 text-blue-700' :
                          job.status === 'completed' ? 'bg-green-100 text-green-700' :
                          job.status === 'failed' ? 'bg-red-100 text-red-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {job.status}
                        </span>
                      </div>
                      
                      <div className="text-sm text-gray-600">
                        {getJobProgressMessage(job)}
                      </div>
                      
                      {job.status === 'running' && job.total_documents > 0 && (
                        <div className="mt-2">
                          <div className="bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                              style={{
                                width: `${(job.processed_documents / job.total_documents) * 100}%`
                              }}
                            />
                          </div>
                          <div className="mt-1 text-xs text-gray-500 text-right">
                            {Math.round((job.processed_documents / job.total_documents) * 100)}%
                          </div>
                        </div>
                      )}
                      
                      {job.metadata?.details && (
                        <div className="mt-2 text-xs text-gray-500 bg-gray-50 p-2 rounded">
                          {job.metadata.details}
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {/* Show configuration details for GitHub */}
                {source.type === 'github_repository' && source.config && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <h5 className="text-sm font-medium mb-2">Configuration:</h5>
                    <div className="bg-gray-50 rounded p-3 text-xs font-mono">
                      <div>Repository: {source.config.owner}/{source.config.repo}</div>
                      <div>Branch: {source.config.branch}</div>
                      {source.config.paths && source.config.paths.length > 0 && (
                        <div>Paths: {source.config.paths.join(', ')}</div>
                      )}
                      {source.config.exclude_patterns && source.config.exclude_patterns.length > 0 && (
                        <div>Exclude: {source.config.exclude_patterns.join(', ')}</div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
      
      {/* Manual Ingestion Instructions */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">Manual Ingestion</h4>
        <p className="text-sm text-blue-800">
          Click "Start Full Ingestion" to manually ingest a repository. The progress will show:
        </p>
        <ul className="text-sm text-blue-800 mt-2 space-y-1 list-disc list-inside">
          <li>Connecting to GitHub</li>
          <li>Fetching repository files</li>
          <li>Creating text chunks</li>
          <li>Generating embeddings</li>
          <li>Storing in vector database</li>
        </ul>
      </div>
    </div>
  );
};

export default SourceManager; 