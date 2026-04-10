# POLE GraphRAG Investigation System - Backend

The Investigraph backend is a FastAPI-powered GraphRAG system that transforms natural language questions into structured, semantic, or hybrid graph searches over a Neo4j POLE knowledge graph.

## Architecture

The backend implements a **multi-strategy GraphRAG pipeline** using the `neo4j-graphrag` library:

1. **Question Classification**: Heuristic routing to the best retrieval strategy.
2. **Retrieve Context**:
   - **Text2Cypher**: Precision structured search with self-healing retry logic.
   - **Vector**: Semantic lookup on crime node embeddings.
   - **VectorCypher**: Semantic search enriched with 2-hop graph neighborhood.
3. **Generate Answer**: Groq-powered grounded synthesis of results into human-readable English.

---

## Core Components

- **FastAPI**: Main API framework with async support.
- **Neo4j 5.23+**: Primary graph database with native vector search capabilities.
- **Groq Llama-3.3-70b**: SOTA LLM for Cypher generation and answer synthesis.
- **SentenceTransformers**: `all-MiniLM-L6-v2` (384 dims) for semantic embeddings.

---

## Setup & Migration

### 1. Install Dependencies
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file from the provided `.env.example`:
```bash
# Neo4j
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=pole

# LLM
GROQ_API_KEY=gsk_xxxxx
# EMBEDDING_MODEL=all-MiniLM-L6-v2 (Default)
```

### 3. Run Embedding Migration (IMPORTANT)
Before the first run, you must generate embeddings and create the vector index:
```bash
python -m scripts.create_embeddings
```
This script populates the `embedding` property on `Crime` nodes and initializes the `crime_vector_index`.

### 4. Start Server
```bash
uvicorn app.main:app --reload --port 8000
```

---

## API Documentation

### `POST /api/ask`
Submit a question and receive a grounded answer + metadata.

**Response Fields:**
- `answer`: The natural language response.
- `retriever_used`: The strategy selected (e.g., `vector_cypher`).
- `retriever_context`: The raw text snippets retrieved from the graph.
- `graph_data`: Nodes and edges for frontend visualization.
- `cypher`: The generated query (if using Text2Cypher).

### `GET /api/health`
Checks connectivity to Neo4j, Groq, and verification of the vector index.

---

## Testing

### Unit & Integration Tests
```bash
pytest tests/ -v
```

### Manual Checklist
See `tests/manual_test_checklist.md` for comprehensive investigation scenarios.
