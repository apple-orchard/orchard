import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8011';

const api = axios.create({
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
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const ragAPI = {
  // Query the RAG system
  query: async (question, maxChunks = 5) => {
    try {
      const response = await api.post('/query', {
        question,
        max_chunks: maxChunks,
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to query');
    }
  },

  // Upload a file
  uploadFile: async (file, metadata = {}) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('metadata', JSON.stringify(metadata));

      const response = await api.post('/ingest', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to upload file');
    }
  },

  // Ingest text content
  ingestText: async (textContent, metadata = {}) => {
    try {
      const response = await api.post('/ingest/text', {
        text_content: textContent,
        metadata,
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to ingest text');
    }
  },

  // Get knowledge base info
  getKnowledgeBaseInfo: async () => {
    try {
      const response = await api.get('/knowledge-base/info');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to get knowledge base info');
    }
  },

  // Health check
  healthCheck: async () => {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Health check failed');
    }
  },

  // Test system
  testSystem: async () => {
    try {
      const response = await api.get('/test');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'System test failed');
    }
  },

  // List available models
  listModels: async () => {
    try {
      const response = await api.get('/models');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to list models');
    }
  },

  // Pull a model
  pullModel: async (modelName) => {
    try {
      const response = await api.post('/models/pull', null, {
        params: { model_name: modelName },
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to pull model');
    }
  },
};

export default api; 