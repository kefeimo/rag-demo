import { useState, useEffect } from 'react';

const STEP_DETAILS = {
  'Planning retrieval strategy': 'Classifying query shape and selecting semantic-first or hybrid-first path.',
  'Searching vector index': 'Running semantic retrieval against embedded document chunks and collecting top matches.',
  'Running hybrid search': 'Combining semantic and keyword/BM25 signals, then picking the stronger retrieval result.',
  'Evaluating document relevance': 'Checking score threshold and evidence quality to decide generate vs reject.',
  'Generating answer': 'Synthesizing a grounded response from retrieved context and formatting citations/sources.',
};

/**
 * ThinkingPanel — live "reasoning" display, Copilot-agent style.
 *
 * While `isThinking` is true the panel shows an animated pulse and each step
 * appears as it arrives.  Once thinking is done it auto-collapses to a summary
 * line after a short pause.  The user can expand/collapse or dismiss entirely.
 *
 * Props:
 *   steps      {string[]}  — ordered list of steps received so far
 *   isThinking {boolean}   — true while SSE stream is still open
 *   onDismiss  {() => void} — called when user clicks ✕
 */
function ThinkingPanel({ steps = [], isThinking = false, cotReasoning = '', onDismiss }) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isDismissed, setIsDismissed] = useState(false);

  const thoughtItems = steps.map((item) => {
    if (typeof item === 'string') {
      return {
        step: item,
        thought: STEP_DETAILS[item] || item,
      };
    }
    return {
      step: item?.step || 'Reasoning step',
      thought: item?.thought || STEP_DETAILS[item?.step] || 'Processing current pipeline state.',
    };
  });

  // Auto-collapse shortly after thinking completes
  useEffect(() => {
    if (!isThinking && steps.length > 0) {
      const t = setTimeout(() => setIsExpanded(false), 1800);
      return () => clearTimeout(t);
    }
  }, [isThinking, steps.length]);

  // Re-open & un-dismiss when a new thinking session begins
  useEffect(() => {
    if (isThinking && steps.length === 1) {
      setIsExpanded(true);
      setIsDismissed(false);
    }
  }, [isThinking, steps.length]);

  if (isDismissed || thoughtItems.length === 0) return null;

  const handleDismiss = (e) => {
    e.stopPropagation();
    setIsDismissed(true);
    onDismiss?.();
  };

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg overflow-hidden shadow-sm">
      {/* ── Header — always visible, click to expand/collapse ── */}
      <div
        className="flex items-center justify-between px-4 py-2.5 cursor-pointer select-none hover:bg-gray-100 transition-colors"
        onClick={() => setIsExpanded((v) => !v)}
      >
        <div className="flex items-center gap-2.5">
          {isThinking ? (
            /* Three bouncing dots */
            <span className="flex gap-1 items-center h-4">
              <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
              <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
              <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" />
            </span>
          ) : (
            /* Green check when done */
            <svg className="w-4 h-4 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          )}
          <span className="text-sm font-medium text-gray-700">
            {isThinking
              ? `Thinking… (${thoughtItems.length} thought${thoughtItems.length !== 1 ? 's' : ''})`
              : `Reasoned in ${thoughtItems.length} thought${thoughtItems.length !== 1 ? 's' : ''}`}
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          {/* Chevron */}
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
          {/* Dismiss ✕ */}
          <button
            onClick={handleDismiss}
            className="p-0.5 rounded text-gray-400 hover:text-gray-600 hover:bg-gray-200 transition-colors"
            title="Dismiss"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* ── Step list — shown when expanded ── */}
      {isExpanded && (
        <div className="px-4 pb-3 pt-1 space-y-1.5 border-t border-gray-100">
          {thoughtItems.map((item, i) => (
            <div key={i} className="rounded-md border border-gray-200 bg-white px-3 py-2">
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <svg className="w-3.5 h-3.5 text-green-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-medium">{i + 1}.</span>
                {item.step && (
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 border border-gray-200">
                    {item.step}
                  </span>
                )}
              </div>
              <p className="mt-1 ml-5 text-xs text-gray-500">
                {item.thought}
              </p>
            </div>
          ))}
          {isThinking && (
            <div className="flex items-center gap-2 text-sm text-gray-400 animate-pulse">
              <span className="w-3.5 flex-shrink-0 text-center">·</span>
              <span>Working…</span>
            </div>
          )}

          {/* ── Model Reasoning (CoT) block — visible when available ── */}
          {cotReasoning && (
            <div className="rounded-md border border-indigo-200 bg-indigo-50 px-3 py-2 mt-2">
              <div className="flex items-center gap-2 text-sm text-indigo-700 mb-1">
                <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <span className="font-medium text-xs uppercase tracking-wide">Model Reasoning</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-500 border border-indigo-200">CoT · demo</span>
              </div>
              <pre className="text-xs text-indigo-800 whitespace-pre-wrap font-mono leading-relaxed">
                {cotReasoning}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ThinkingPanel;
