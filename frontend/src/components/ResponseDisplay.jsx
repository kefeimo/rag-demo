import SourceCard from './SourceCard';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/**
 * ResponseDisplay Component
 * Shows the answer and sources from a RAG query
 */
function ResponseDisplay({ response, ragSystem }) {
  if (!response) return null;

  return (
    <div className="w-full space-y-4">
      {/* Query Display */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-blue-900 mb-1">Your Question:</p>
            <p className="text-gray-800">{response.query}</p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0 ml-4">
            {ragSystem && (
              <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                ragSystem === 'vcc' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-blue-100 text-blue-800'
              }`}>
                {ragSystem === 'vcc' ? 'VCC Docs' : 'FastAPI Docs'}
              </span>
            )}
            {response.api_version && (
              <span className="text-xs px-2 py-1 rounded-full font-medium bg-gray-100 text-gray-700 border border-gray-300">
                API v{response.api_version}
              </span>
            )}
            {response.response_time && (
              <span className="text-xs px-2 py-1 rounded-full font-medium bg-purple-100 text-purple-800 border border-purple-300">
                ⚡ {response.response_time.toFixed(2)}s
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Confidence Warning Banner */}
      {response.confidence < 0.65 && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-r-lg">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-yellow-600 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <div>
              <h4 className="text-sm font-semibold text-yellow-800 mb-1">Low Confidence Response</h4>
              <p className="text-sm text-yellow-700">
                The system has low confidence ({(response.confidence * 100).toFixed(1)}%) in this answer. 
                The retrieved documents may not contain relevant information for your query.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Answer Display */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <div className="flex items-start justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900">Answer</h3>
          <div className="flex items-center gap-2">
            {/* Confidence Badge with Color Coding */}
            <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold ${
              response.confidence >= 0.8 
                ? 'bg-green-100 text-green-800 border border-green-300' 
                : response.confidence >= 0.65 
                  ? 'bg-yellow-100 text-yellow-800 border border-yellow-300' 
                  : 'bg-red-100 text-red-800 border border-red-300'
            }`}>
              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                {response.confidence >= 0.8 ? (
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                ) : response.confidence >= 0.65 ? (
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                ) : (
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                )}
              </svg>
              <span>
                {response.confidence >= 0.8 ? 'High' : response.confidence >= 0.65 ? 'Medium' : 'Low'} Confidence
              </span>
              <span className="ml-0.5">({(response.confidence * 100).toFixed(1)}%)</span>
            </div>
            {response.model && (
              <span className="text-xs text-gray-400 px-2 py-1 bg-gray-100 rounded">
                {response.model}
              </span>
            )}
          </div>
        </div>
        <div className="prose prose-sm max-w-none text-gray-700">
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={{
              code: ({node, inline, className, children, ...props}) => (
                inline ? (
                  <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-red-600" {...props}>
                    {children}
                  </code>
                ) : (
                  <code className="block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm font-mono" {...props}>
                    {children}
                  </code>
                )
              ),
              a: ({node, children, ...props}) => (
                <a className="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer" {...props}>
                  {children}
                </a>
              )
            }}
          >
            {response.answer}
          </ReactMarkdown>
        </div>
      </div>

      {/* Sources Display */}
      {response.sources && response.sources.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-md font-semibold text-gray-900">Sources ({response.sources.length})</h4>
          <div className="grid grid-cols-1 gap-3">
            {response.sources.map((source, index) => (
              <SourceCard key={index} source={source} index={index} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ResponseDisplay;
