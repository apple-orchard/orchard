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
  query: async (question: string, maxChunks: number = 5): Promise<RAGQueryResponse> => {
    try {
      const response: AxiosResponse<RAGQueryResponse> = await api.post('/query', {
        question,
        max_chunks: maxChunks,
      });
      return response.data;
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

  // Get system prompt
  getSystemPrompt: async (): Promise<{ system_prompt: string }> => {
    try {
      const response: AxiosResponse<{ system_prompt: string }> = await api.get('/system-prompt');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get system prompt');
    }
  },

  // Update system prompt
  updateSystemPrompt: async (systemPrompt: string): Promise<{ system_prompt: string }> => {
    try {
      const response: AxiosResponse<{ system_prompt: string }> = await api.post('/system-prompt', {
        system_prompt: systemPrompt,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to update system prompt');
    }
  },
};

export default api; 