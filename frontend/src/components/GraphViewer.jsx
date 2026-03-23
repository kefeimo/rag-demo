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
  const [graphView, setGraphView] = useState('enhanced');
  const [svgByView, setSvgByView] = useState({
    enhanced: '',
    raw: '',
  });

  const currentSvg = svgByView[graphView];

  const loadGraph = async (view) => {
    if (svgByView[view] || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await getRagGraphMermaid(view);
      const mermaidText = result?.mermaid;

      if (!mermaidText) {
        throw new Error('No mermaid graph returned from backend.');
      }

      const graphId = `rag-graph-${view}-${Date.now()}`;
      const rendered = await mermaid.render(graphId, mermaidText);
      setSvgByView((prev) => ({ ...prev, [view]: rendered.svg }));
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to render graph');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggle = async () => {
    const nextOpen = !isOpen;
    setIsOpen(nextOpen);

    if (!nextOpen) return;
    await loadGraph(graphView);
  };

  const handleViewChange = async (view) => {
    if (view === graphView) return;
    setGraphView(view);
    if (isOpen) {
      await loadGraph(view);
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
          <div className="mb-3 inline-flex rounded-lg border border-gray-300 bg-white p-1">
            <button
              onClick={() => handleViewChange('enhanced')}
              className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                graphView === 'enhanced'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              Enhanced
            </button>
            <button
              onClick={() => handleViewChange('raw')}
              className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                graphView === 'raw'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              Raw
            </button>
          </div>

          {isLoading && <p className="text-sm text-gray-600">Rendering graph...</p>}
          {error && <p className="text-sm text-red-600">{error}</p>}
          {!isLoading && !error && currentSvg && (
            <div
              className="min-w-[700px]"
              dangerouslySetInnerHTML={{ __html: currentSvg }}
            />
          )}
        </div>
      )}
    </div>
  );
}

export default GraphViewer;
