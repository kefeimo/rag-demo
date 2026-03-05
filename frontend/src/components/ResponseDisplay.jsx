import SourceCard from './SourceCard';

/**
 * ResponseDisplay Component
 * Shows the answer and sources from a RAG query
 */
function ResponseDisplay({ response }) {
  if (!response) return null;

  return (
    <div className="w-full space-y-4">
      {/* Query Display */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm font-medium text-blue-900 mb-1">Your Question:</p>
        <p className="text-gray-800">{response.query}</p>
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
        <div className="prose prose-sm max-w-none">
          <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{response.answer}</p>
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
