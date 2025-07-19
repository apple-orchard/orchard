import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  RAGQueryResponse,
  FileUploadResponse,
  FileUploadMetadata,
  APIService,
  PluginListResponse,
  FullConfig,
  PluginConfig,
  IngestionResponse,
  JobStatus,
  SourceListResponse,
  GlobalSettings,
  JobInfo,
  JobListResponse,
  JobStatsResponse,
  AsyncJobResponse,
} from '../types';

const API_BASE_URL: string = process.env.REACT_APP_API_URL || 'http://localhost:8011';

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log('Making request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const ragAPI: APIService = {
  // Query the RAG system
  query: async function* (question: string, maxChunks: number = 5): AsyncGenerator<string> {
    try {
      const res = await fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        body: JSON.stringify({ question, max_chunks: maxChunks }),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/stream+plain',
        },
      });
      if (!res.ok) throw new Error(res.statusText);

      const reader  = res.body!.getReader();
      const decoder = new TextDecoder();
      let done = false;

      try {
        while (!done) {
          const { value, done: doneReading } = await reader.read();
          done = doneReading;
          if (!value) continue;

          const chunkText = decoder.decode(value, { stream: true });
          for (const char of chunkText) {
            // yield answer;
            yield char as unknown as string;
            await new Promise((r) => setTimeout(r, 0));
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to query');
    }
  },

  // Upload a file
  uploadFile: async (file: File, metadata: FileUploadMetadata = {} as FileUploadMetadata): Promise<FileUploadResponse> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('metadata', JSON.stringify(metadata));

      const response: AxiosResponse<FileUploadResponse> = await api.post('/ingest', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to upload file');
    }
  },
};

// Plugin API methods
export const pluginAPI = {
  // List all plugins
  listPlugins: async (): Promise<PluginListResponse> => {
    try {
      const response: AxiosResponse<PluginListResponse> = await api.get('/api/plugins');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to list plugins');
    }
  },

  // Get full configuration
  getFullConfig: async (): Promise<FullConfig> => {
    try {
      const response: AxiosResponse<FullConfig> = await api.get('/api/plugins/config');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get configuration');
    }
  },

  // Get plugin configuration
  getPluginConfig: async (pluginName: string): Promise<PluginConfig> => {
    try {
      const response = await api.get(`/api/plugins/${pluginName}/config`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get plugin config');
    }
  },

  // Update plugin configuration
  updatePluginConfig: async (pluginName: string, config: PluginConfig): Promise<PluginConfig> => {
    try {
      const response = await api.put(`/api/plugins/${pluginName}/config`, config);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to update plugin config');
    }
  },

  // Enable plugin
  enablePlugin: async (pluginName: string): Promise<void> => {
    try {
      await api.post(`/api/plugins/${pluginName}/enable`);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to enable plugin');
    }
  },

  // Disable plugin
  disablePlugin: async (pluginName: string): Promise<void> => {
    try {
      await api.post(`/api/plugins/${pluginName}/disable`);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to disable plugin');
    }
  },

  // Trigger ingestion
  triggerIngestion: async (pluginName: string, sourceId: string, fullSync: boolean = true): Promise<IngestionResponse> => {
    try {
      const response: AxiosResponse<IngestionResponse> = await api.post(
        `/api/plugins/${pluginName}/ingest`,
        {
          source_id: sourceId,
          full_sync: fullSync,
        },
        {
          timeout: 600000,
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to trigger ingestion');
    }
  },

  // Get job status
  getJobStatus: async (pluginName: string, jobId: string): Promise<JobStatus> => {
    try {
      const response: AxiosResponse<JobStatus> = await api.get(
        `/api/plugins/${pluginName}/status/${jobId}`
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get job status');
    }
  },

  // Get plugin sources
  getPluginSources: async (pluginName: string): Promise<SourceListResponse> => {
    try {
      const response: AxiosResponse<SourceListResponse> = await api.get(
        `/api/plugins/${pluginName}/sources`
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get plugin sources');
    }
  },

  // Get global settings
  getGlobalSettings: async (): Promise<GlobalSettings> => {
    try {
      const response: AxiosResponse<GlobalSettings> = await api.get('/api/plugins/settings/global');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get global settings');
    }
  },

  // Update global settings
  updateGlobalSettings: async (settings: GlobalSettings): Promise<GlobalSettings> => {
    try {
      const response: AxiosResponse<GlobalSettings> = await api.put(
        '/api/plugins/settings/global',
        settings
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to update global settings');
    }
  },
};

// Job Management API methods
export const jobAPI = {
  // Get specific job status
  getJobStatus: async (jobId: string): Promise<JobInfo> => {
    try {
      const response: AxiosResponse<JobInfo> = await api.get(`/jobs/${jobId}`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get job status');
    }
  },

  // List all jobs with optional filtering
  listJobs: async (status?: string, limit: number = 50): Promise<JobListResponse> => {
    try {
      const params = new URLSearchParams();
      if (status) params.append('status', status);
      params.append('limit', limit.toString());

      const response: AxiosResponse<JobListResponse> = await api.get(`/jobs?${params}`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to list jobs');
    }
  },

  // Cancel a job
  cancelJob: async (jobId: string): Promise<void> => {
    try {
      await api.delete(`/jobs/${jobId}`);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to cancel job');
    }
  },

  // Get job statistics
  getJobStats: async (): Promise<JobStatsResponse> => {
    try {
      const response: AxiosResponse<JobStatsResponse> = await api.get('/jobs/stats');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get job statistics');
    }
  },

  // Start async text ingestion
  ingestTextAsync: async (textContent: string, metadata: Record<string, any> = {}): Promise<AsyncJobResponse> => {
    try {
      const response: AxiosResponse<AsyncJobResponse> = await api.post('/ingest/text/async', {
        text_content: textContent,
        metadata,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to start text ingestion');
    }
  },

  // Start async batch ingestion
  ingestBatchAsync: async (messages: Array<{text: string, metadata?: Record<string, any>}>, metadata: Record<string, any> = {}): Promise<AsyncJobResponse> => {
    try {
      const response: AxiosResponse<AsyncJobResponse> = await api.post('/ingest/batch/async', {
        messages,
        metadata,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to start batch ingestion');
    }
  },
};

// Additional utility functions
export const apiUtils = {
  // Ingest text content
  ingestText: async (textContent: string, metadata: Record<string, any> = {}): Promise<FileUploadResponse> => {
    try {
      const response: AxiosResponse<FileUploadResponse> = await api.post('/ingest/text', {
        text_content: textContent,
        metadata,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to ingest text');
    }
  },

  // Get knowledge base info
  getKnowledgeBaseInfo: async (): Promise<any> => {
    try {
      const response: AxiosResponse<any> = await api.get('/knowledge-base/info');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get knowledge base info');
    }
  },

  // Health check
  healthCheck: async (): Promise<any> => {
    try {
      const response: AxiosResponse<any> = await api.get('/health');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Health check failed');
    }
  },

  // Test system
  testSystem: async (): Promise<any> => {
    try {
      const response: AxiosResponse<any> = await api.get('/test');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'System test failed');
    }
  },
};

export default api;