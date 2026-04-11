import React, { useState } from 'react';
import { QueryResponse } from '../services/api';
import './ResponsePanel.css';

interface ResponsePanelProps {
  response: QueryResponse | null;
}

const ResponsePanel: React.FC<ResponsePanelProps> = ({ response }) => {
  const [showCypher, setShowCypher] = useState(true);
  const [showRawResults, setShowRawResults] = useState(false);
  const [showContext, setShowContext] = useState(false);

  if (!response) {
    return null;
  }

  const hasResults = response.results && response.results.length > 0;
  const tableColumns = hasResults ? Object.keys(response.results[0]) : [];

  return (
    <div className="response-panel">
      {/* Question */}
      {response.question && (
        <div className="question-section">
          <h3>Question</h3>
          <p className="question-text">{response.question}</p>
        </div>
      )}

      {/* Natural Language Answer */}
      <div className="answer-section">
        <h3>Answer</h3>
        <div className="answer-content">
          {response.answer}
        </div>

        {/* Metadata */}
        <div className="metadata">
          {response.retriever_used && (
            <span className="metadata-item" title="Retrieval strategy used">
              Strategy: {response.retriever_used}
            </span>
          )}
          {response.attempts && (
            <span className="metadata-item">
              Attempts: {response.attempts}
            </span>
          )}
          {response.execution_time_ms && (
            <span className="metadata-item">
              Time: {response.execution_time_ms}ms
            </span>
          )}
        </div>
      </div>

      {/* Generated Cypher Query (Collapsible) - only if cypher exists */}
      {response.cypher && response.cypher.trim() !== '' && (
        <div className="cypher-section">
          <div
            className="section-header"
            onClick={() => setShowCypher(!showCypher)}
          >
            <h3>Generated Cypher Query</h3>
            <span className="toggle-icon">{showCypher ? '▼' : '▶'}</span>
          </div>

          {showCypher && (
            <div className="cypher-content">
              <pre>
                <code>{response.cypher}</code>
              </pre>
              <button
                className="copy-button"
                onClick={() => navigator.clipboard.writeText(response.cypher || '')}
              >
                Copy
              </button>
            </div>
          )}
        </div>
      )}

      {/* Retriever Context (Collapsible) - shows what context was fed to the LLM */}
      {response.retriever_context && response.retriever_context.length > 0 && (
        <div className="cypher-section">
          <div
            className="section-header"
            onClick={() => setShowContext(!showContext)}
          >
            <h3>Retriever Context ({response.retriever_context.length} items)</h3>
            <span className="toggle-icon">{showContext ? '▼' : '▶'}</span>
          </div>

          {showContext && (
            <div className="cypher-content">
              {response.retriever_context.map((ctx, i) => (
                <pre key={i} style={{ marginBottom: '8px', whiteSpace: 'pre-wrap' }}>
                  {ctx}
                </pre>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Results Table */}
      {hasResults && (
        <div className="results-section">
          <div
            className="section-header"
            onClick={() => setShowRawResults(!showRawResults)}
          >
            <h3>
              Query Results ({response.results.length} rows)
              {response.results.length === 50 && (
                <span className="limit-indicator" title="Results limited to 50 for performance">
                  {' '}• Limited to 50
                </span>
              )}
            </h3>
            <span className="toggle-icon">{showRawResults ? '▼' : '▶'}</span>
          </div>

          {showRawResults && (
            <div className="results-table-container">
              <table className="results-table">
                <thead>
                  <tr>
                    {tableColumns.map((col) => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {response.results.map((row, rowIndex) => (
                    <tr key={rowIndex}>
                      {tableColumns.map((col) => (
                        <td key={col}>
                          {formatCellValue(row[col])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* No Results Message */}
      {!hasResults && (
        <div className="no-results">
          <p>No results returned from the query.</p>
        </div>
      )}
    </div>
  );
};

// Helper function to format cell values
function formatCellValue(value: any): string {
  if (value === null || value === undefined) {
    return '—';
  }
  if (typeof value === 'object') {
    return JSON.stringify(value);
  }
  return String(value);
}

export default ResponsePanel;
