/**
 * SourceCard Component
 * Displays a single source citation with confidence score
 */
function SourceCard({ source, index }) {
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'bg-green-100 text-green-800 border-green-300';
    if (confidence >= 0.65) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    return 'bg-red-100 text-red-800 border-red-300';
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.65) return 'Medium';
    return 'Low';
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-gray-600">Source {index + 1}</span>
          <span className={`text-xs px-2 py-1 rounded-full font-medium border ${getConfidenceColor(source.confidence)}`}>
            {getConfidenceLabel(source.confidence)}: {(source.confidence * 100).toFixed(1)}%
          </span>
        </div>
      </div>
      
      {source.metadata && (
        <div className="mb-2">
          {source.metadata.source && (
            <p className="text-sm font-medium text-gray-700 truncate" title={source.metadata.source}>
              📄 {source.metadata.source}
            </p>
          )}
          {source.metadata.chunk_id !== undefined && (
            <p className="text-xs text-gray-500">Chunk #{source.metadata.chunk_id}</p>
          )}
        </div>
      )}
      
      <div className="bg-gray-50 border-l-4 border-blue-500 p-3 rounded">
        <p className="text-sm text-gray-700 whitespace-pre-wrap">{source.content}</p>
      </div>
    </div>
  );
}

export default SourceCard;
