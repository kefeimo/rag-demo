import { useState, useEffect } from 'react';
import QueryInput from './components/QueryInput';
import ResponseDisplay from './components/ResponseDisplay';
import ErrorDisplay from './components/ErrorDisplay';
import { queryRAG, checkHealth, ingestDocuments, ingestVisaDocs } from './utils/api';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking');
  const [ragSystem, setRagSystem] = useState('vcc'); // 'fastapi' or 'vcc'
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const [docsLoaded, setDocsLoaded] = useState({ fastapi: false, vcc: false });
  const [queryHistory, setQueryHistory] = useState([]); // Track query history

  // Check backend health on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        await checkHealth();
        setBackendStatus('connected');
      } catch (err) {
        setBackendStatus('disconnected');
        setError('Backend is not accessible. Make sure the FastAPI server is running on http://localhost:8000');
      }
    };
    checkBackend();
  }, []);

  // Auto-load documents when RAG system changes
  useEffect(() => {
    const loadDocumentsForSystem = async () => {
      // Skip if already loaded or backend not connected
      if (backendStatus !== 'connected') return;
      if (docsLoaded[ragSystem]) return;

      setIsLoadingDocs(true);
      try {
        console.log(`Loading ${ragSystem} documents...`);
        
        if (ragSystem === 'vcc') {
          // Load Visa Chart Components docs
          const result = await ingestVisaDocs(false); // Don't force reingest
          console.log('VCC docs loaded:', result);
        } else {
          // Load FastAPI docs
          const result = await ingestDocuments('docs', false); // Don't force reingest
          console.log('FastAPI docs loaded:', result);
        }
        
        // Mark as loaded
        setDocsLoaded(prev => ({ ...prev, [ragSystem]: true }));
      } catch (err) {
        console.error(`Error loading ${ragSystem} documents:`, err);
        // Don't show error to user - documents might already be loaded
        // Just mark as loaded to avoid repeated attempts
        setDocsLoaded(prev => ({ ...prev, [ragSystem]: true }));
      } finally {
        setIsLoadingDocs(false);
      }
    };

    loadDocumentsForSystem();
  }, [ragSystem, backendStatus, docsLoaded]);

  const handleQuery = async (query) => {
    setIsLoading(true);
    setError(null);
    setResponse(null);

    try {
      // TODO: Pass ragSystem to backend to filter by document source
      // For now, backend returns all documents (FastAPI + VCC mixed)
      // Future: Add `rag_system` parameter to API call
      const data = await queryRAG(query);
      setResponse(data);
      setBackendStatus('connected');
      
      // Add to query history (keep last 10)
      setQueryHistory(prev => {
        const newHistory = [{
          query: data.query,
          timestamp: new Date().toISOString(),
          confidence: data.confidence,
          ragSystem: ragSystem,
          responseTime: data.response_time
        }, ...prev];
        return newHistory.slice(0, 10); // Keep only last 10
      });
    } catch (err) {
      console.error('Query error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to get response from server';
      setError(errorMessage);
      
      // Update backend status if it's a connection error
      if (err.code === 'ECONNREFUSED' || err.code === 'ERR_NETWORK') {
        setBackendStatus('disconnected');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = () => {
    switch (backendStatus) {
      case 'connected': return 'bg-green-500';
      case 'disconnected': return 'bg-red-500';
      default: return 'bg-yellow-500';
    }
  };

  const getStatusText = () => {
    switch (backendStatus) {
      case 'connected': return 'Connected';
      case 'disconnected': return 'Disconnected';
      default: return 'Checking...';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <header className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-2">
            <h1 className="text-4xl font-bold text-gray-900">
              {ragSystem === 'fastapi' ? 'FastAPI' : 'Visa Chart Components'} RAG System
            </h1>
            <div className="flex items-center gap-2 px-3 py-1 bg-white rounded-full shadow-sm border border-gray-200">
              <div className={`w-2 h-2 rounded-full ${getStatusColor()} animate-pulse`}></div>
              <span className="text-xs font-medium text-gray-600">{getStatusText()}</span>
            </div>
          </div>
          
          {/* RAG System Toggle */}
          <div className="flex items-center justify-center gap-3 mb-4">
            <span className="text-sm font-medium text-gray-600">RAG System:</span>
            <div className="relative inline-flex items-center bg-white border-2 border-gray-300 rounded-full p-1 shadow-sm">
              <button
                onClick={() => setRagSystem('fastapi')}
                className={`px-4 py-1.5 text-sm font-medium rounded-full transition-all duration-200 ${
                  ragSystem === 'fastapi'
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                FastAPI Docs
              </button>
              <button
                onClick={() => setRagSystem('vcc')}
                className={`px-4 py-1.5 text-sm font-medium rounded-full transition-all duration-200 ${
                  ragSystem === 'vcc'
                    ? 'bg-green-600 text-white shadow-md'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                VCC Docs
              </button>
            </div>
          </div>
          
          <p className="text-gray-600">
            {ragSystem === 'fastapi' 
              ? 'Ask questions about FastAPI and get AI-powered answers with sources'
              : 'Ask questions about Visa Chart Components and get AI-powered answers with sources'
            }
          </p>

          {/* Document Loading Indicator */}
          {isLoadingDocs && (
            <div className="mt-2 flex items-center justify-center gap-2 text-sm text-gray-600">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
              <span>Loading {ragSystem === 'vcc' ? 'VCC' : 'FastAPI'} documentation...</span>
            </div>
          )}
        </header>

        {/* Main Content */}
        <div className="space-y-6">
          {/* Query Input */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <QueryInput onSubmit={handleQuery} isLoading={isLoading} ragSystem={ragSystem} />
          </div>

          {/* Error Display */}
          {error && (
            <ErrorDisplay error={error} onDismiss={() => setError(null)} />
          )}

          {/* Response Display */}
          {response && (
            <ResponseDisplay response={response} ragSystem={ragSystem} />
          )}

          {/* Welcome/Empty State */}
          {!response && !error && !isLoading && (
            <div className="bg-white rounded-lg shadow-md p-8 text-center">
              <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Ready to Answer Your Questions
              </h3>
              <p className="text-gray-600 mb-4">
                {ragSystem === 'fastapi'
                  ? 'Try asking about FastAPI features, usage examples, or best practices'
                  : 'Try asking about Visa Chart Components, chart creation, or API usage'
                }
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {ragSystem === 'fastapi' ? (
                  <>
                    <button
                      onClick={() => handleQuery('What is FastAPI?')}
                      className="text-sm px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                      disabled={backendStatus !== 'connected'}
                    >
                      What is FastAPI?
                    </button>
                    <button
                      onClick={() => handleQuery('How do I create a path parameter?')}
                      className="text-sm px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                      disabled={backendStatus !== 'connected'}
                    >
                      How do I create a path parameter?
                    </button>
                    <button
                      onClick={() => handleQuery('What are FastAPI\'s main features?')}
                      className="text-sm px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                      disabled={backendStatus !== 'connected'}
                    >
                      What are FastAPI's main features?
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => handleQuery('How do I create a bar chart with Visa Chart Components?')}
                      className="text-sm px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                      disabled={backendStatus !== 'connected'}
                    >
                      How do I create a bar chart?
                    </button>
                    <button
                      onClick={() => handleQuery('What are the props for IDataTableProps?')}
                      className="text-sm px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                      disabled={backendStatus !== 'connected'}
                    >
                      What are IDataTableProps?
                    </button>
                    <button
                      onClick={() => handleQuery('How do I use VCC with React?')}
                      className="text-sm px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                      disabled={backendStatus !== 'connected'}
                    >
                      How to use with React?
                    </button>
                  </>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Query History */}
        {queryHistory.length > 0 && (
          <div className="mt-6 bg-white rounded-lg shadow-md p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Recent Queries ({queryHistory.length})
              </h3>
              <button
                onClick={() => setQueryHistory([])}
                className="text-xs text-gray-500 hover:text-red-600 transition-colors"
              >
                Clear
              </button>
            </div>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {queryHistory.map((item, index) => (
                <div
                  key={index}
                  onClick={() => handleQuery(item.query)}
                  className="group p-3 bg-gray-50 hover:bg-blue-50 rounded-lg cursor-pointer transition-colors border border-gray-200 hover:border-blue-300"
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm text-gray-800 flex-1 line-clamp-2 group-hover:text-blue-900">
                      {item.query}
                    </p>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        item.ragSystem === 'vcc' 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-blue-100 text-blue-700'
                      }`}>
                        {item.ragSystem === 'vcc' ? 'VCC' : 'API'}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        {item.confidence >= 0.8 ? (
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        ) : (
                          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        )}
                      </svg>
                      {(item.confidence * 100).toFixed(0)}%
                    </span>
                    {item.responseTime && (
                      <span className="flex items-center gap-1">
                        ⚡ {item.responseTime.toFixed(1)}s
                      </span>
                    )}
                    <span className="flex-1 text-right">
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <footer className="text-center mt-12 text-sm text-gray-500">
          <p>
            Powered by {response?.model ? (
              response.model === 'openai' ? (
                <span className="font-medium text-blue-600">OpenAI (GPT-3.5-turbo)</span>
              ) : response.model === 'gpt4all' ? (
                <span className="font-medium text-purple-600">GPT4All (Mistral 7B)</span>
              ) : (
                <span className="font-medium">{response.model}</span>
              )
            ) : (
              <span className="font-medium text-gray-600">AI</span>
            )} • ChromaDB • FastAPI
            {response?.api_version && (
              <span className="ml-2 text-xs text-gray-400">v{response.api_version}</span>
            )}
          </p>
        </footer>
      </div>
    </div>
  );
}

export default App;

