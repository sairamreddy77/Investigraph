# backend/app/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class QueryRequest(BaseModel):
    """Request model for NL query endpoint"""
    question: str = Field(
        ...,
        description="Natural language question about crime data",
        min_length=1,
        examples=["How many crimes are recorded?"]
    )


class GraphNode(BaseModel):
    """Node in graph visualization"""
    id: str
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Edge in graph visualization"""
    source: str
    target: str
    relationship: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphData(BaseModel):
    """Graph data for visualization"""
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)


class QueryResponse(BaseModel):
    """Response model for NL query endpoint"""
    question: str = Field(..., description="Original question")
    answer: str = Field(..., description="Natural language answer")
    cypher: str = Field(..., description="Generated Cypher query")
    results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Raw query results from Neo4j"
    )
    graph_data: GraphData = Field(
        default_factory=GraphData,
        description="Graph data for visualization"
    )
    attempts: int = Field(..., description="Number of query attempts")
    execution_time_ms: int = Field(..., description="Total execution time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if query failed")


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str = Field(..., description="Overall health status", examples=["healthy", "unhealthy"])
    neo4j_connected: bool = Field(..., description="Neo4j connection status")
    pipeline_initialized: bool = Field(..., description="Pipeline initialization status")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional health check details"
    )


class SchemaResponse(BaseModel):
    """Response model for schema endpoint"""
    schema: str = Field(..., description="Formatted schema text")
    property_values: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Known property values for categorical fields"
    )


class Example(BaseModel):
    """Few-shot example"""
    question: str
    cypher: str


class ExamplesResponse(BaseModel):
    """Response model for examples endpoint"""
    examples: List[Example] = Field(..., description="List of few-shot examples")
    count: int = Field(..., description="Total number of examples")
