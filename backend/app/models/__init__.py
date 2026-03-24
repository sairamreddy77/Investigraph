# backend/app/models/__init__.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class QueryRequest(BaseModel):
    """Request model for /api/query endpoint"""
    question: str = Field(..., min_length=1, description="Natural language question")


class GraphData(BaseModel):
    """Graph visualization data"""
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []


class QueryResponse(BaseModel):
    """Response model for /api/query endpoint"""
    question: str
    answer: str
    cypher: str
    results: List[Dict[str, Any]]
    graph_data: GraphData
    attempts: int
    execution_time_ms: int
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for /health endpoint"""
    status: str = Field(..., description="'healthy' or 'unhealthy'")
    neo4j_connected: bool
    pipeline_initialized: bool
    details: Dict[str, Any] = {}


class Example(BaseModel):
    """Single example query"""
    question: str
    cypher: str


class ExamplesResponse(BaseModel):
    """Response model for /api/examples endpoint"""
    examples: List[Example]
    count: int


class SchemaResponse(BaseModel):
    """Response model for /api/schema endpoint"""
    schema_text: str = Field(..., alias="schema")
    property_values: Dict[str, List[str]]