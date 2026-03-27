import React from 'react';
import { ChatSession } from '../types/chat';
import './ChatSidebar.css';

interface ChatSidebarProps {
  sessions: ChatSession[];
  currentSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onNewChat: () => void;
  onDeleteSession: (sessionId: string) => void;
  isOpen: boolean;
  onToggle: () => void;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  isOpen,
  onToggle,
}) => {
  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
  };

  return (
    <>
      {/* Toggle button */}
      <button className="sidebar-toggle" onClick={onToggle}>
        {isOpen ? '✕' : '☰'}
      </button>

      {/* Sidebar */}
      <div className={`chat-sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2>Chat History</h2>
          <button className="new-chat-button" onClick={onNewChat}>
            + New Chat
          </button>
        </div>

        <div className="sessions-list">
          {sessions.length === 0 ? (
            <div className="empty-state">
              <p>No chat history yet</p>
              <p className="empty-hint">Start a conversation to begin</p>
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={`session-item ${
                  session.id === currentSessionId ? 'active' : ''
                }`}
                onClick={() => onSelectSession(session.id)}
              >
                <div className="session-content">
                  <div className="session-title">{session.title}</div>
                  <div className="session-meta">
                    <span className="message-count">
                      {session.messages.length} message{session.messages.length !== 1 ? 's' : ''}
                    </span>
                    <span className="session-date">
                      {formatDate(session.updatedAt)}
                    </span>
                  </div>
                </div>
                <button
                  className="delete-session-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm('Delete this chat session?')) {
                      onDeleteSession(session.id);
                    }
                  }}
                  title="Delete session"
                >
                  🗑️
                </button>
              </div>
            ))
          )}
        </div>

        {sessions.length > 0 && (
          <div className="sidebar-footer">
            <button
              className="clear-all-button"
              onClick={() => {
                if (confirm('Clear all chat history?')) {
                  sessions.forEach(s => onDeleteSession(s.id));
                }
              }}
            >
              Clear All History
            </button>
          </div>
        )}
      </div>

      {/* Overlay for mobile */}
      {isOpen && <div className="sidebar-overlay" onClick={onToggle}></div>}
    </>
  );
};

export default ChatSidebar;
