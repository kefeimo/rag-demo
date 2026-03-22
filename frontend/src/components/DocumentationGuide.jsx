import { useState } from 'react';

const DocumentationGuide = ({ onQuestionClick }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const collections = [
    {
      name: 'Asset Score / Audit Template',
      icon: '📦',
      description: 'Docker setup, energy calculations, customizable fields',
      examples: [
        'How do I set up the development environment using Docker Compose?',
        'How does the energy saving calculation work?',
        'How do I add a new customizable enum field?',
      ],
    },
    {
      name: 'FastAPI Framework',
      icon: '📘',
      description: 'Web framework fundamentals, API development, async patterns',
      examples: [
        'What is FastAPI?',
        'How do I create path parameters?',
        'How does dependency injection work in FastAPI?',
      ],
    },
  ];

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* Collapsible Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">📚</span>
          <div className="text-left">
            <h3 className="text-lg font-semibold text-gray-900">
              Available Documentation
            </h3>
            <p className="text-sm text-gray-600">
              Ask anything - we'll search all collections
            </p>
          </div>
        </div>
        <svg
          className={`w-5 h-5 text-gray-500 transition-transform ${
            isExpanded ? 'rotate-180' : ''
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Expandable Content */}
      {isExpanded && (
        <div className="px-6 pb-6 pt-2 space-y-6 border-t border-gray-100">
          {collections.map((collection, idx) => (
            <div key={idx} className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-xl">{collection.icon}</span>
                <div>
                  <h4 className="font-semibold text-gray-900">
                    {collection.name}
                  </h4>
                  <p className="text-xs text-gray-500">
                    {collection.description}
                  </p>
                </div>
              </div>
              <div className="ml-7 space-y-2">
                {collection.examples.map((example, exIdx) => (
                  <button
                    key={exIdx}
                    onClick={() => onQuestionClick(example)}
                    className="block w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-700 rounded-md transition-colors"
                  >
                    • {example}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DocumentationGuide;
