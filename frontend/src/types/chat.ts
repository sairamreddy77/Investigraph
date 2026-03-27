// Chat session types

export interface ChatMessage {
  id: string;
  question: string;
  answer: string;
  cypher: string;
  results: Array<Record<string, any>>;
  graph_data?: {
    nodes: Array<{ id: string; label: string; properties: Record<string, any> }>;
    edges: Array<{ source: string; target: string; relationship: string; properties: Record<string, any> }>;
  };
  attempts: number;
  execution_time_ms: number;
  timestamp: number;
  error?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}
