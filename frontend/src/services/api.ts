import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  RAGQueryResponse,
  FileUploadResponse,
  FileUploadMetadata,
  ModelsResponse,
  ModelPullResponse,
  APIService,
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
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to upload file');
    }
  },

  // Get available models
  getModels: async (): Promise<ModelsResponse> => {
    try {
      const response: AxiosResponse<ModelsResponse> = await api.get('/models');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to list models');
    }
  },

  // Pull a model
  pullModel: async (modelName: string): Promise<ModelPullResponse> => {
    try {
      const response: AxiosResponse<ModelPullResponse> = await api.post('/models/pull', null, {
        params: { model_name: modelName },
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to pull model');
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