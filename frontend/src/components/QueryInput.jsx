import { useState } from 'react';

/**
 * QueryInput Component
 * Text input and submit button for RAG queries
 */
function QueryInput({ onSubmit, isLoading, ragSystem = 'fastapi' }) {
  const [query, setQuery] = useState('');

  const getPlaceholder = () => {
    if (ragSystem === 'vcc') {
      return "Ask a question about Visa Chart Components... (e.g., 'How do I create a bar chart?')";
    }
    return "Ask a question about FastAPI... (e.g., 'What is FastAPI?')";
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
    }
  };

  const handleKeyDown = (e) => {
    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex flex-col gap-2">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={getPlaceholder()}
          className="w-full px-4 py-3 text-gray-900 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          rows={3}
          disabled={isLoading}
        />
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">
            {query.length > 0 && `${query.length} characters`}
          </span>
          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Searching...
              </span>
            ) : (
              'Ask Question'
            )}
          </button>
        </div>
      </div>
    </form>
  );
}

export default QueryInput;
