import React, { useState } from 'react';
import { QueryResponse } from '../services/api';
import './ResponsePanel.css';

interface ResponsePanelProps {
  response: QueryResponse | null;
}

const ResponsePanel: React.FC<ResponsePanelProps> = ({ response }) => {
  const [showCypher, setShowCypher] = useState(false);
  const [showRawResults, setShowRawResults] = useState(false);

  if (!response) {
    return null;
  }

  const hasResults = response.results && response.results.length > 0;
  const tableColumns = hasResults ? Object.keys(response.results[0]) : [];

  return (
    <div className="response-panel">
      <h2>Response</h2>

      {/* Natural Language Answer */}
      <div className="answer-section">
        <div className="answer-content">
          {response.answer}
        </div>

        {/* Metadata */}
        <div className="metadata">
          {response.attempts && (
            <span className="metadata-item">
              Attempts: {response.attempts}
            </span>
          )}
          {response.execution_time && (
            <span className="metadata-item">
              Time: {response.execution_time.toFixed(2)}s
            </span>
          )}
        </div>
      </div>

      {/* Generated Cypher Query (Collapsible) */}
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
              onClick={() => navigator.clipboard.writeText(response.cypher)}
            >
              Copy
            </button>
          </div>
        )}
      </div>

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
