# backend/app/main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any

from app.config import get_settings
from app.database import get_neo4j_client
from app.models import (
    QueryRequest,
    QueryResponse,
    HealthResponse,
    SchemaResponse,
    ExamplesResponse,
    Example,
    GraphData
)
from core.pipeline import get_pipeline
from core.schema_introspector import get_schema_introspector
from core.few_shot_loader import get_few_shot_loader

# Configure logging
settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for FastAPI application
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting POLE NL-to-Cypher API...")

    try:
        # Initialize Neo4j connection
        logger.info("Connecting to Neo4j...")
        neo4j_client = get_neo4j_client()
        logger.info("Neo4j connection established")

        # Initialize pipeline (caches schema and examples)
        logger.info("Initializing query pipeline...")
        pipeline = get_pipeline()
        pipeline.initialize()
        logger.info("Pipeline initialization complete")

        logger.info(f"API ready on port {settings.BACKEND_PORT}")

        # Log all registered routes
        logger.info("━━━ REGISTERED ROUTES ━━━")
        for route in app.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                methods = ', '.join(route.methods)
                logger.info(f"  {methods:10} {route.path}")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━")

    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down API...")
    try:
        neo4j_client.close()
        logger.info("Neo4j connection closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# Create FastAPI app
app = FastAPI(
    title="POLE NL-to-Cypher API",
    description="Natural language query API for POLE crime investigation knowledge graph",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
cors_origins = settings.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = time.time()

    # Log detailed request info
    logger.info(f"━━━ INCOMING REQUEST ━━━")
    logger.info(f"Method: {request.method}")
    logger.info(f"URL: {request.url}")
    logger.info(f"Path: {request.url.path}")
    logger.info(f"Query Params: {dict(request.query_params)}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Client: {request.client}")

    # Process request
    response = await call_next(request)

    # Log response
    duration_ms = int((time.time() - start_time) * 1000)
    logger.info(
        f"━━━ RESPONSE ━━━ "
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration_ms}ms"
    )

    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


# ==================== ENDPOINTS ====================


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    logger.info("━━━ ROOT ENDPOINT CALLED ━━━")
    return {
        "service": "POLE NL-to-Cypher API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "query": "/api/query",
            "schema": "/api/schema",
            "examples": "/api/examples",
            "health": "/health"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint

    Checks:
    - Neo4j connectivity
    - Pipeline initialization status

    Returns:
        HealthResponse with status and connection details
    """
    try:
        # Check Neo4j connection
        neo4j_client = get_neo4j_client()
        neo4j_connected = False
        neo4j_error = None

        try:
            # Simple connectivity test
            result = neo4j_client.query("RETURN 1 AS test")
            neo4j_connected = len(result) > 0
        except Exception as e:
            neo4j_error = str(e)
            logger.error(f"Neo4j health check failed: {e}")

        # Check pipeline initialization
        pipeline = get_pipeline()
        pipeline_initialized = pipeline._initialized

        # Determine overall status
        status = "healthy" if (neo4j_connected and pipeline_initialized) else "unhealthy"

        details: Dict[str, Any] = {
            "neo4j_uri": settings.NEO4J_URI,
            "neo4j_database": settings.NEO4J_DATABASE,
        }

        if neo4j_error:
            details["neo4j_error"] = neo4j_error

        return HealthResponse(
            status=status,
            neo4j_connected=neo4j_connected,
            pipeline_initialized=pipeline_initialized,
            details=details
        )

    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return HealthResponse(
            status="unhealthy",
            neo4j_connected=False,
            pipeline_initialized=False,
            details={"error": str(e)}
        )


@app.post("/api/query", response_model=QueryResponse, tags=["Query"])
async def query(request: QueryRequest):
    """
    Natural language query endpoint

    Processes a natural language question through the NL-to-Cypher pipeline:
    1. Generate Cypher query from question
    2. Execute query with retry on errors
    3. Generate natural language answer from results

    Args:
        request: QueryRequest with natural language question

    Returns:
        QueryResponse with answer, Cypher query, results, and metadata

    Raises:
        HTTPException: If pipeline execution fails
    """
    try:
        logger.info(f"━━━ QUERY ENDPOINT START ━━━")
        logger.info(f"Question received: {request.question}")

        # Get pipeline
        logger.info("Getting pipeline instance...")
        pipeline = get_pipeline()
        logger.info(f"Pipeline initialized: {pipeline._initialized}")

        # Run pipeline
        logger.info("Running pipeline...")
        result = pipeline.run(request.question)
        logger.info(f"Pipeline result keys: {result.keys()}")

        # Convert to response model
        logger.info("Converting to response model...")
        response = QueryResponse(
            question=result["question"],
            answer=result["answer"],
            cypher=result["cypher"],
            results=result["results"],
            graph_data=GraphData(**result["graph_data"]),
            attempts=result["attempts"],
            execution_time_ms=result["execution_time_ms"],
            error=result.get("error")
        )

        logger.info(f"━━━ QUERY ENDPOINT SUCCESS ━━━ Completed in {result['execution_time_ms']}ms")
        return response

    except Exception as e:
        logger.error(f"━━━ QUERY ENDPOINT ERROR ━━━")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )


@app.get("/api/schema", response_model=SchemaResponse, tags=["Schema"])
async def get_schema():
    """
    Get graph schema endpoint

    Returns the introspected Neo4j schema including:
    - Node labels and properties
    - Relationship types
    - Known property values for categorical fields

    Returns:
        SchemaResponse with formatted schema and property values

    Raises:
        HTTPException: If schema introspection fails
    """
    try:
        logger.info("Fetching schema")

        schema_introspector = get_schema_introspector()
        schema_text = schema_introspector.get_schema_text()
        property_values = schema_introspector.get_property_values()

        return SchemaResponse(
            schema=schema_text,
            property_values=property_values
        )

    except Exception as e:
        logger.error(f"Schema fetch error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch schema: {str(e)}"
        )


@app.get("/api/examples", response_model=ExamplesResponse, tags=["Examples"])
async def get_examples():
    """
    Get few-shot examples endpoint

    Returns the curated few-shot examples used by the Cypher generator.
    These examples demonstrate various query patterns and serve as
    training data for the LLM.

    Returns:
        ExamplesResponse with list of question-Cypher pairs

    Raises:
        HTTPException: If examples cannot be loaded
    """
    try:
        logger.info("Fetching examples")

        few_shot_loader = get_few_shot_loader()
        examples_data = few_shot_loader.get_examples()

        examples = [
            Example(question=ex["question"], cypher=ex["cypher"])
            for ex in examples_data
        ]

        return ExamplesResponse(
            examples=examples,
            count=len(examples)
        )

    except Exception as e:
        logger.error(f"Examples fetch error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch examples: {str(e)}"
        )


# Run with: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.BACKEND_PORT,
        reload=True
    )
