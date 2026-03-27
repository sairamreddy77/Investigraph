import React, { useState } from 'react';
import './QueryPanel.css';

interface QueryPanelProps {
  onSubmit: (question: string) => void;
  isLoading: boolean;
  error: string | null;
}

const QueryPanel: React.FC<QueryPanelProps> = ({ onSubmit, isLoading, error }) => {
  const [question, setQuestion] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('━━━ QUERY PANEL SUBMIT ━━━');
    console.log('Question:', question.trim());
    console.log('Is loading:', isLoading);
    if (question.trim() && !isLoading) {
      console.log('Calling onSubmit callback...');
      onSubmit(question.trim());
    } else {
      console.log('Submit blocked - empty question or already loading');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  return (
    <div className="query-panel">
      <h2>Ask a Question</h2>

      <form onSubmit={handleSubmit} className="query-form">
        <textarea
          className="query-input"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g., How many crimes are recorded? or Who are the people involved in drug crimes?"
          rows={3}
          disabled={isLoading}
        />

        <div className="form-actions">
          <button
            type="submit"
            className="submit-button"
            disabled={!question.trim() || isLoading}
          >
            {isLoading ? 'Processing...' : 'Submit Query'}
          </button>

          {question && !isLoading && (
            <button
              type="button"
              className="clear-button"
              onClick={() => setQuestion('')}
            >
              Clear
            </button>
          )}
        </div>
      </form>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );
};

export default QueryPanel;
