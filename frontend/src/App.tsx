import React, { useState, useEffect } from 'react';
import QueryPanel from './components/QueryPanel';
import ResponsePanel from './components/ResponsePanel';
import GraphVisualization from './components/GraphVisualization';
import { submitQuery, checkHealth, QueryResponse } from './services/api';
import './App.css';

function App() {
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [systemStatus, setSystemStatus] = useState<{
    neo4j: boolean;
    llm: boolean;
  } | null>(null);

  useEffect(() => {
    checkSystemHealth();
  }, []);

  const checkSystemHealth = async () => {
    console.log('━━━ APP: CHECKING SYSTEM HEALTH ━━━');
    try {
      const health = await checkHealth();
      console.log('Health response:', health);
      setSystemStatus({
        neo4j: health.neo4j_connected,
        llm: health.llm_available,
      });
      console.log('System status updated:', { neo4j: health.neo4j_connected, llm: health.llm_available });
    } catch (err) {
      console.error('━━━ APP: HEALTH CHECK FAILED ━━━', err);
      setSystemStatus({ neo4j: false, llm: false });
    }
  };

  const handleQuerySubmit = async (question: string) => {
    console.log('━━━ APP: QUERY SUBMIT HANDLER ━━━');
    console.log('Question received:', question);

    setIsLoading(true);
    setError(null);
    setResponse(null);
    console.log('State updated: loading=true, error=null, response=null');

    try {
      console.log('Calling submitQuery...');
      const result = await submitQuery(question);
      console.log('━━━ APP: QUERY SUCCESS ━━━');
      console.log('Result:', result);
      setResponse(result);
    } catch (err) {
      console.error('━━━ APP: QUERY FAILED ━━━');
      console.error('Error:', err);
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(errorMessage);
      console.error('Error message set:', errorMessage);
    } finally {
      setIsLoading(false);
      console.log('Loading state set to false');
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>POLE NL-to-Cypher QA System</h1>
        <p className="app-subtitle">
          Natural Language Crime Investigation Knowledge Graph Query Interface
        </p>

        {systemStatus && (
          <div className="system-status">
            <div className={`status-indicator ${systemStatus.neo4j ? 'online' : 'offline'}`}>
              <span className="status-dot"></span>
              Neo4j: {systemStatus.neo4j ? 'Connected' : 'Disconnected'}
            </div>
            <div className={`status-indicator ${systemStatus.llm ? 'online' : 'offline'}`}>
              <span className="status-dot"></span>
              LLM: {systemStatus.llm ? 'Available' : 'Unavailable'}
            </div>
          </div>
        )}
      </header>

      <main className="app-main">
        <QueryPanel
          onSubmit={handleQuerySubmit}
          isLoading={isLoading}
          error={error}
        />

        {response && (
          <>
            <ResponsePanel response={response} />
            <GraphVisualization response={response} />
          </>
        )}

        {!response && !isLoading && !error && (
          <div className="welcome-message">
            <h2>Welcome!</h2>
            <p>
              Ask questions about the POLE crime investigation knowledge graph using natural language.
              The system will generate Cypher queries, execute them against Neo4j, and provide
              answers with optional graph visualization.
            </p>
            <div className="feature-list">
              <div className="feature-item">
                <strong>Smart Query Generation:</strong> Uses LLM to convert your questions into Cypher
              </div>
              <div className="feature-item">
                <strong>Auto-Retry:</strong> Automatically fixes syntax errors and reformulates empty results
              </div>
              <div className="feature-item">
                <strong>Graph Visualization:</strong> Interactive network visualization of query results
              </div>
            </div>
          </div>
        )}

        {isLoading && (
          <div className="loading-message">
            <div className="spinner"></div>
            <p>Processing your question...</p>
            <small>Generating Cypher query and executing against Neo4j</small>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>
          POLE NL-to-Cypher QA System | Person • Object • Location • Event Knowledge Graph
        </p>
      </footer>
    </div>
  );
}

export default App;
