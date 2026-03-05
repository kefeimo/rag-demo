import { useState, useEffect } from 'react';
import QueryInput from './components/QueryInput';
import ResponseDisplay from './components/ResponseDisplay';
import ErrorDisplay from './components/ErrorDisplay';
import { queryRAG, checkHealth } from './utils/api';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking');

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

  const handleQuery = async (query) => {
    setIsLoading(true);
    setError(null);
    setResponse(null);

    try {
      const data = await queryRAG(query);
      setResponse(data);
      setBackendStatus('connected');
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
              FastAPI RAG System
            </h1>
            <div className="flex items-center gap-2 px-3 py-1 bg-white rounded-full shadow-sm border border-gray-200">
              <div className={`w-2 h-2 rounded-full ${getStatusColor()} animate-pulse`}></div>
              <span className="text-xs font-medium text-gray-600">{getStatusText()}</span>
            </div>
          </div>
          <p className="text-gray-600">
            Ask questions about FastAPI and get AI-powered answers with sources
          </p>
        </header>

        {/* Main Content */}
        <div className="space-y-6">
          {/* Query Input */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <QueryInput onSubmit={handleQuery} isLoading={isLoading} />
          </div>

          {/* Error Display */}
          {error && (
            <ErrorDisplay error={error} onDismiss={() => setError(null)} />
          )}

          {/* Response Display */}
          {response && (
            <ResponseDisplay response={response} />
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
                Try asking about FastAPI features, usage examples, or best practices
              </p>
              <div className="flex flex-wrap justify-center gap-2">
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
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <footer className="text-center mt-12 text-sm text-gray-500">
          <p>Powered by GPT4All (Mistral 7B) • ChromaDB • FastAPI</p>
        </footer>
      </div>
    </div>
  );
}

export default App;

