import { useState } from 'react';
import mermaid from 'mermaid';
import { getRagGraphMermaid } from '../utils/api';

mermaid.initialize({
  startOnLoad: false,
  securityLevel: 'loose',
  theme: 'default',
});

function GraphViewer() {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [svg, setSvg] = useState('');

  const handleToggle = async () => {
    const nextOpen = !isOpen;
    setIsOpen(nextOpen);

    if (!nextOpen || svg || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await getRagGraphMermaid();
      const mermaidText = result?.mermaid;

      if (!mermaidText) {
        throw new Error('No mermaid graph returned from backend.');
      }

      const graphId = `rag-graph-${Date.now()}`;
      const rendered = await mermaid.render(graphId, mermaidText);
      setSvg(rendered.svg);
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to render graph');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">LangGraph Orchestration</h3>
          <p className="text-xs text-gray-500">View planner and retrieval routing graph directly in UI</p>
        </div>
        <button
          onClick={handleToggle}
          className="text-sm px-3 py-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
        >
          {isOpen ? 'Hide Graph' : 'Show Graph'}
        </button>
      </div>

      {isOpen && (
        <div className="mt-4 border border-gray-200 rounded-lg bg-gray-50 p-3 overflow-x-auto">
          {isLoading && <p className="text-sm text-gray-600">Rendering graph...</p>}
          {error && <p className="text-sm text-red-600">{error}</p>}
          {!isLoading && !error && svg && (
            <div
              className="min-w-[700px]"
              dangerouslySetInnerHTML={{ __html: svg }}
            />
          )}
        </div>
      )}
    </div>
  );
}

export default GraphViewer;
