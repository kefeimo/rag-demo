import axios from 'axios';

// API base URL - configurable via environment variable
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 120 seconds (RAG queries can be slow)
});

/**
 * Check API health status
 * @returns {Promise<Object>} Health status object
 */
export const checkHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

/**
 * Submit a query to the RAG system
 * @param {string} query - The question to ask
 * @param {number} topK - Number of top results to retrieve (default: 3)
 * @returns {Promise<Object>} Query response with answer and sources
 */
export const queryRAG = async (query, topK = 3) => {
  const response = await apiClient.post('/api/v1/query', {
    query,
    top_k: topK,
  });
  return response.data;
};

/**
 * Ingest documents into the RAG system
 * @param {string} documentPath - Path to documents to ingest
 * @param {boolean} forceReingest - Whether to force re-ingestion
 * @returns {Promise<Object>} Ingestion response with statistics
 */
export const ingestDocuments = async (documentPath, forceReingest = false) => {
  const response = await apiClient.post('/api/v1/ingest', {
    document_path: documentPath,
    force_reingest: forceReingest,
  });
  return response.data;
};

export default apiClient;
