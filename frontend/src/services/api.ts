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

  console.log('━━━ API CALL ━━━');
  console.log('URL:', url);
  console.log('Method:', options?.method || 'GET');
  console.log('Options:', options);

  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    console.log('Response status:', response.status);
    console.log('Response OK:', response.ok);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Error response:', errorData);
      throw new Error(
        errorData.detail || errorData.error || `HTTP ${response.status}: ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log('Response data:', data);
    return data;
  } catch (error) {
    console.error('API call error:', error);
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
  console.log('━━━ SUBMIT QUERY ━━━');
  console.log('Question:', question);
  return apiCall<QueryResponse>('/query', {
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
  // Health endpoint is at root level, not under /api
  const url = '/health';
  console.log('━━━ HEALTH CHECK ━━━');
  console.log('URL:', url);

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log('Health response status:', response.status);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Health check error:', errorData);
      throw new Error(
        errorData.detail || errorData.error || `HTTP ${response.status}: ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log('Health data:', data);
    return data;
  } catch (error) {
    console.error('Health check failed:', error);
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('An unknown error occurred');
  }
}
