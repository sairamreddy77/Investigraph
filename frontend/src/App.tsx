import React, { useState, useEffect } from 'react';
import QueryPanel from './components/QueryPanel';
import ResponsePanel from './components/ResponsePanel';
import GraphVisualization from './components/GraphVisualization';
import ChatSidebar from './components/ChatSidebar';
import { submitQuery, checkHealth, QueryResponse } from './services/api';
import { ChatStorage } from './services/chatStorage';
import { ChatSession, ChatMessage } from './types/chat';
import './App.css';

function App() {
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [systemStatus, setSystemStatus] = useState<{
    neo4j: boolean;
    llm: boolean;
  } | null>(null);

  useEffect(() => {
    checkSystemHealth();
    loadSessions();
  }, []);

  const loadSessions = () => {
    const allSessions = ChatStorage.getSessions();
    setSessions(allSessions);

    // Load current session or create new one
    const currentId = ChatStorage.getCurrentSessionId();
    if (currentId) {
      const session = ChatStorage.getSession(currentId);
      if (session) {
        setCurrentSession(session);
      } else {
        createNewSession();
      }
    } else if (allSessions.length > 0) {
      // Load most recent session
      setCurrentSession(allSessions[0]);
      ChatStorage.setCurrentSessionId(allSessions[0].id);
    } else {
      createNewSession();
    }
  };

  const createNewSession = (firstQuestion?: string) => {
    const newSession = ChatStorage.createSession(firstQuestion);
    setCurrentSession(newSession);
    setSessions(ChatStorage.getSessions());
  };

  const selectSession = (sessionId: string) => {
    const session = ChatStorage.getSession(sessionId);
    if (session) {
      setCurrentSession(session);
      ChatStorage.setCurrentSessionId(sessionId);
      setError(null);
      setIsSidebarOpen(false);
    }
  };

  const deleteSession = (sessionId: string) => {
    ChatStorage.deleteSession(sessionId);
    const allSessions = ChatStorage.getSessions();
    setSessions(allSessions);

    // If deleted current session, load another or create new
    if (currentSession?.id === sessionId) {
      if (allSessions.length > 0) {
        selectSession(allSessions[0].id);
      } else {
        createNewSession();
      }
    }
  };

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

    // Create new session if none exists or if starting fresh
    if (!currentSession) {
      createNewSession(question);
    }

    setIsLoading(true);
    setError(null);
    console.log('State updated: loading=true, error=null');

    try {
      console.log('Calling submitQuery...');
      const result = await submitQuery(question);
      console.log('━━━ APP: QUERY SUCCESS ━━━');
      console.log('Result:', result);

      // Create message from result
      const message: ChatMessage = {
        id: `msg_${Date.now()}`,
        question: result.question,
        answer: result.answer,
        cypher: result.cypher,
        results: result.results,
        graph_data: result.graph_data,
        attempts: result.attempts,
        execution_time_ms: result.execution_time_ms || 0,
        timestamp: Date.now(),
        error: result.error,
      };

      // Save message to current session
      if (currentSession) {
        ChatStorage.addMessage(currentSession.id, message);
        const updatedSession = ChatStorage.getSession(currentSession.id);
        if (updatedSession) {
          setCurrentSession(updatedSession);
          setSessions(ChatStorage.getSessions());
        }
      }
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
      <ChatSidebar
        sessions={sessions}
        currentSessionId={currentSession?.id || null}
        onSelectSession={selectSession}
        onNewChat={() => createNewSession()}
        onDeleteSession={deleteSession}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />

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

        {/* Render message history */}
        {currentSession && currentSession.messages.length > 0 && (
          <div className="message-history">
            {currentSession.messages.map((message) => (
              <div key={message.id} className="message-item">
                <ResponsePanel response={{
                  question: message.question,
                  answer: message.answer,
                  cypher: message.cypher,
                  results: message.results,
                  graph_data: message.graph_data,
                  attempts: message.attempts,
                  execution_time_ms: message.execution_time_ms,
                  error: message.error,
                }} />
                <GraphVisualization response={{
                  question: message.question,
                  answer: message.answer,
                  cypher: message.cypher,
                  results: message.results,
                  graph_data: message.graph_data,
                  attempts: message.attempts,
                  execution_time_ms: message.execution_time_ms,
                  error: message.error,
                }} />
              </div>
            ))}
          </div>
        )}

        {!currentSession?.messages.length && !isLoading && !error && (
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
                <strong>Graph Visualization:</strong> Interactive network visualization (shown only when graph data is available)
              </div>
              <div className="feature-item">
                <strong>Chat History:</strong> All conversations are saved locally for context and reference
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
