/**
 * SourceCard Component
 * Displays a single source citation with confidence score and metadata
 */
function SourceCard({ source, index }) {
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'bg-green-100 text-green-800 border-green-300';
    if (confidence >= 0.65) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    return 'bg-red-100 text-red-800 border-red-300';
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.8) return 'High Relevance';
    if (confidence >= 0.65) return 'Medium Relevance';
    return 'Low Relevance';
  };

  // Determine source type icon
  const getSourceIcon = () => {
    if (!source.metadata?.source) return '📄';
    const sourceName = source.metadata.source.toLowerCase();
    if (sourceName.includes('repo_docs')) return '📚';
    if (sourceName.includes('api_reference')) return '🔧';
    if (sourceName.includes('github_issues')) return '🐛';
    return '📄';
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">{getSourceIcon()}</span>
          <span className="text-sm font-semibold text-gray-900">Source {index + 1}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${getConfidenceColor(source.confidence)}`}>
            <svg className="w-3 h-3 inline mr-1 -mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              {source.confidence >= 0.8 ? (
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              ) : source.confidence >= 0.65 ? (
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              ) : (
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              )}
            </svg>
            {getConfidenceLabel(source.confidence)}
          </span>
          <span className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
            {(source.confidence * 100).toFixed(1)}%
          </span>
        </div>
      </div>
      
      {/* Metadata Section */}
      {source.metadata && (
        <div className="mb-3 space-y-1">
          {source.metadata.source && (
            <div className="flex items-start gap-2 text-xs">
              <span className="text-gray-500 font-medium min-w-[60px]">Document:</span>
              <p className="text-gray-700 font-mono text-xs break-all" title={source.metadata.source}>
                {source.metadata.source}
              </p>
            </div>
          )}
          {source.metadata.chunk_id !== undefined && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-gray-500 font-medium min-w-[60px]">Chunk ID:</span>
              <span className="text-gray-700 font-mono">#{source.metadata.chunk_id}</span>
            </div>
          )}
          {source.metadata.doc_type && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-gray-500 font-medium min-w-[60px]">Type:</span>
              <span className="text-gray-700 capitalize">{source.metadata.doc_type}</span>
            </div>
          )}
        </div>
      )}
      
      {/* Content Preview */}
      <div className="bg-gradient-to-r from-blue-50 to-gray-50 border-l-4 border-blue-500 p-3 rounded">
        <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
          {source.content.length > 400 
            ? source.content.substring(0, 400) + '...' 
            : source.content
          }
        </p>
        {source.content.length > 400 && (
          <button 
            className="text-xs text-blue-600 hover:text-blue-800 mt-2 font-medium"
            onClick={() => {
              // Toggle full content (you can implement state for this)
              alert('Full content:\n\n' + source.content);
            }}
          >
            Show full content →
          </button>
        )}
      </div>
    </div>
  );
}

export default SourceCard;
