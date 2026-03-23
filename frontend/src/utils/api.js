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
 * @returns {Promise<Object>} Health status object including model and version
 */
export const checkHealth = async () => {
  try {
    console.log('Checking health at:', `${API_BASE_URL}/health`);
    const response = await apiClient.get('/health');
    console.log('Health check response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Health check failed:', {
      message: error.message,
      code: error.code,
      response: error.response?.data,
      status: error.response?.status
    });
    throw error;
  }
};

/**
 * Submit a query to the RAG system
 * @param {string} query - The question to ask
 * @param {number} topK - Number of top results to retrieve (default: 3)
 * @param {string|null} collection - ChromaDB collection name ('fastapi_docs')
 * @returns {Promise<Object>} Query response with answer and sources
 */
export const queryRAG = async (query, topK = 3, collection = null) => {
  const body = { query, top_k: topK };
  if (collection) body.collection = collection;
  const response = await apiClient.post('/api/v1/query', body);
  return response.data;
};

/**
 * Submit a query and receive live thinking steps + final answer via SSE stream.
 *
 * @param {string} query
 * @param {number} topK
 * @param {string|null} collection
 * @param {{ onThinking?: (thinking: {step?: string, thought?: string} | string) => void, onCot?: (content: string) => void, onResult?: (data: Object) => void, onError?: (msg: string) => void }} callbacks
 * @returns {Promise<void>} Resolves when the stream is fully consumed.
 */
export const queryRAGStream = async (query, topK = 3, collection = null, callbacks = {}) => {
  const { onThinking, onCot, onResult, onError } = callbacks;
  const body = { query, top_k: topK };
  if (collection) body.collection = collection;

  const res = await fetch(`${API_BASE_URL}/api/v1/query/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split('\n\n');
    buffer = parts.pop() ?? '';

    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith('data: ')) continue;
      const raw = line.slice(6).trim();
      if (raw === '[DONE]') return;
      try {
        const msg = JSON.parse(raw);
        if (msg.type === 'thinking') onThinking?.(msg.thought ? { step: msg.step, thought: msg.thought } : msg.step);
        else if (msg.type === 'cot') onCot?.(msg.content);
        else if (msg.type === 'result') onResult?.(msg.data);
        else if (msg.type === 'error') onError?.(msg.message);
      } catch (_) {
        // ignore malformed SSE frames
      }
    }
  }
};

/**
 * Ingest FastAPI documents into the RAG system
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

/**
 * Check collection status (document count)
 * @returns {Promise<Object>} Collection status with count
 */
export const checkCollectionStatus = async () => {
  try {
    // Use a simple query to check if collection has documents
    const response = await apiClient.post('/api/v1/query', {
      query: 'test',
      top_k: 1,
    });
    // If we get sources, collection has documents
    return {
      hasDocuments: response.data?.sources?.length > 0,
      sourceCount: response.data?.sources?.length || 0
    };
  } catch (error) {
    // If error, assume collection is empty
    return { hasDocuments: false, sourceCount: 0 };
  }
};

/**
 * Fetch LangGraph Mermaid diagram source from backend
 * @param {"enhanced"|"raw"} view - Mermaid view mode
 * @returns {Promise<{graph: string, view: string, mermaid: string}>}
 */
export const getRagGraphMermaid = async (view = 'enhanced') => {
  const response = await apiClient.get('/api/v1/rag/graph/mermaid', {
    params: { view },
  });
  return response.data;
};

export default apiClient;
