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
          <div>
            <p className="text-sm font-medium text-blue-900 mb-1">Your Question:</p>
            <p className="text-gray-800">{response.query}</p>
          </div>
          {ragSystem && (
            <span className={`text-xs px-2 py-1 rounded-full font-medium ${
              ragSystem === 'vcc' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-blue-100 text-blue-800'
            }`}>
              {ragSystem === 'vcc' ? 'VCC Docs' : 'FastAPI Docs'}
            </span>
          )}
        </div>
      </div>

      {/* Answer Display */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <div className="flex items-start justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900">Answer</h3>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">
              Confidence: {(response.confidence * 100).toFixed(1)}%
            </span>
            {response.model && (
              <span className="text-xs text-gray-400">• {response.model}</span>
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
