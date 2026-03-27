// Chat storage service - manages chat sessions in localStorage

import { ChatSession, ChatMessage } from '../types/chat';

const STORAGE_KEY = 'pole_chat_sessions';
const CURRENT_SESSION_KEY = 'pole_current_session';

export class ChatStorage {
  // Get all sessions
  static getSessions(): ChatSession[] {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      if (!data) return [];
      return JSON.parse(data);
    } catch (error) {
      console.error('Error loading sessions:', error);
      return [];
    }
  }

  // Save all sessions
  static saveSessions(sessions: ChatSession[]): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    } catch (error) {
      console.error('Error saving sessions:', error);
    }
  }

  // Get current session ID
  static getCurrentSessionId(): string | null {
    return localStorage.getItem(CURRENT_SESSION_KEY);
  }

  // Set current session ID
  static setCurrentSessionId(sessionId: string): void {
    localStorage.setItem(CURRENT_SESSION_KEY, sessionId);
  }

  // Create new session
  static createSession(firstQuestion?: string): ChatSession {
    const now = Date.now();
    const session: ChatSession = {
      id: `session_${now}`,
      title: firstQuestion ? this.generateTitle(firstQuestion) : 'New Chat',
      messages: [],
      createdAt: now,
      updatedAt: now,
    };

    const sessions = this.getSessions();
    sessions.unshift(session); // Add to beginning
    this.saveSessions(sessions);
    this.setCurrentSessionId(session.id);

    return session;
  }

  // Get session by ID
  static getSession(sessionId: string): ChatSession | null {
    const sessions = this.getSessions();
    return sessions.find(s => s.id === sessionId) || null;
  }

  // Update session
  static updateSession(sessionId: string, updates: Partial<ChatSession>): void {
    const sessions = this.getSessions();
    const index = sessions.findIndex(s => s.id === sessionId);

    if (index !== -1) {
      sessions[index] = {
        ...sessions[index],
        ...updates,
        updatedAt: Date.now(),
      };
      this.saveSessions(sessions);
    }
  }

  // Add message to session
  static addMessage(sessionId: string, message: ChatMessage): void {
    const sessions = this.getSessions();
    const index = sessions.findIndex(s => s.id === sessionId);

    if (index !== -1) {
      sessions[index].messages.push(message);
      sessions[index].updatedAt = Date.now();

      // Update title if this is the first message
      if (sessions[index].messages.length === 1) {
        sessions[index].title = this.generateTitle(message.question);
      }

      this.saveSessions(sessions);
    }
  }

  // Delete session
  static deleteSession(sessionId: string): void {
    const sessions = this.getSessions();
    const filtered = sessions.filter(s => s.id !== sessionId);
    this.saveSessions(filtered);

    // If deleted session was current, clear current
    if (this.getCurrentSessionId() === sessionId) {
      localStorage.removeItem(CURRENT_SESSION_KEY);
    }
  }

  // Generate title from question (first 50 chars)
  static generateTitle(question: string): string {
    return question.length > 50 ? question.substring(0, 50) + '...' : question;
  }

  // Clear all sessions
  static clearAll(): void {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(CURRENT_SESSION_KEY);
  }
}
