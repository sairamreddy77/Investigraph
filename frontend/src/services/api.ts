// API Service for POLE NL-to-Cypher QA System

// Type Definitions
export interface QueryRequest {
  question: string;
}

export interface QueryResponse {
  answer: string;
  cypher: string;
  results: Array<Record<string, any>>;
  attempts: number;
  execution_time?: number;
  error?: string;
}

export interface SchemaResponse {
  nodes: Array<{
    label: string;
    properties: string[];
  }>;
  relationships: Array<{
    type: string;
    source: string;
    target: string;
  }>;
  property_values?: Record<string, string[]>;
  sample_data?: Record<string, Array<Record<string, any>>>;
}

export interface ExampleQuery {
  question: string;
  cypher: string;
}

export interface ExamplesResponse {
  examples: ExampleQuery[];
}

export interface HealthResponse {
  status: string;
  neo4j_connected: boolean;
  llm_available: boolean;
  timestamp: string;
}

// API Configuration
const API_BASE_URL = '/api';

// Helper function for API calls
async function apiCall<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || errorData.error || `HTTP ${response.status}: ${response.statusText}`
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('An unknown error occurred');
  }
}

// API Functions

/**
 * Submit a natural language question to the QA system
 */
export async function submitQuery(question: string): Promise<QueryResponse> {
  return apiCall<QueryResponse>('/ask', {
    method: 'POST',
    body: JSON.stringify({ question }),
  });
}

/**
 * Get the Neo4j schema information
 */
export async function getSchema(): Promise<SchemaResponse> {
  return apiCall<SchemaResponse>('/schema', {
    method: 'GET',
  });
}

/**
 * Get example questions and queries
 */
export async function getExamples(): Promise<ExamplesResponse> {
  return apiCall<ExamplesResponse>('/examples', {
    method: 'GET',
  });
}

/**
 * Check system health
 */
export async function checkHealth(): Promise<HealthResponse> {
  return apiCall<HealthResponse>('/health', {
    method: 'GET',
  });
}
