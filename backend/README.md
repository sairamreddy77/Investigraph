# POLE NL-to-Cypher QA System - Backend

FastAPI backend for natural language to Cypher query generation over a POLE (Person, Object, Location, Event) crime investigation knowledge graph.

## Overview

This backend implements a 3-step pipeline with intelligent retry logic:
1. **Cypher Generation**: LLM generates Cypher query from natural language question
2. **Query Execution**: Execute query on Neo4j with automatic retry on errors
3. **Answer Generation**: Convert results into natural language response

### Key Features

- **Intelligent Query Generation**: Uses schema introspection + 24 few-shot examples
- **Self-Healing Retry**: Automatically retries on syntax errors or empty results (up to 3 attempts)
- **Multi-Provider LLM Support**: Groq, OpenAI, Anthropic, Google Gemini
- **Graph Visualization Data**: Returns nodes and edges for frontend visualization
- **Comprehensive Testing**: Unit tests, integration tests, and manual test checklists

---

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Main Dependencies:**
- `fastapi` >= 0.111.0 - Web framework
- `uvicorn` >= 0.30.1 - ASGI server
- `neo4j` >= 5.23.1 - Neo4j driver
- `langchain` >= 0.2.10 - LLM orchestration
- `langchain-openai` >= 0.1.17 - OpenAI/compatible LLMs
- `pydantic` >= 2.8.2 - Data validation
- `python-dotenv` >= 1.0.1 - Environment configuration
- `pyyaml` >= 6.0 - YAML parsing for few-shot examples

### 3. Configure Environment

Create a `.env` file in the backend directory:

```bash
# Neo4j Connection
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=pole

# LLM Provider (choose one or multiple for fallback)
GROQ_API_KEY=gsk_xxxxx              # For LLaMA 3.3 70B (free, fast)
# OPENAI_API_KEY=sk-xxxxx           # For GPT-4o
# ANTHROPIC_API_KEY=sk-ant-xxxxx    # For Claude Sonnet 4
# GOOGLE_API_KEY=AIzaSyxxxxx        # For Gemini 2.0 Flash

# Optional: Logging
LOG_LEVEL=INFO
```

**LLM Provider Priority** (if multiple keys configured):
1. Anthropic (Claude Sonnet 4) - Best quality
2. OpenAI (GPT-4o) - Very close second
3. Google (Gemini 2.0 Flash) - Best value
4. Groq (LLaMA 3.3 70B) - Budget option, free tier

### 4. Run Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

Server will be available at `http://localhost:8000`

### 5. Verify Installation

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "neo4j_connected": true,
  "llm_provider": "groq"
}
```

---

## API Documentation

### Base URL
`http://localhost:8000`

### Endpoints

#### `POST /api/ask`
Submit a natural language question and get Cypher query + results.

**Request:**
```json
{
  "question": "Find people involved in drug crimes in area WN"
}
```

**Response:**
```json
{
  "question": "Find people involved in drug crimes in area WN",
  "answer": "Found 3 people involved in drug crimes in the WN area: John Smith, Sarah Jones, and Mike Brown.",
  "cypher": "MATCH (p:Person)-[:PARTY_TO]->(c:Crime)-[:OCCURRED_AT]->(l:Location)-[:LOCATION_IN_AREA]->(a:AREA)\nWHERE toLower(c.type) CONTAINS 'drug' AND toLower(a.areaCode) = 'wn'\nRETURN p.name, p.surname, c.type, a.areaCode",
  "results": [
    {"p.name": "John", "p.surname": "Smith", "c.type": "Drugs", "a.areaCode": "WN"},
    {"p.name": "Sarah", "p.surname": "Jones", "c.type": "Drugs", "a.areaCode": "WN"},
    {"p.name": "Mike", "p.surname": "Brown", "c.type": "Drugs", "a.areaCode": "WN"}
  ],
  "attempts": 1,
  "execution_time_ms": 1250,
  "graph_data": {
    "nodes": [
      {"id": "p1", "label": "Person", "properties": {"name": "John", "surname": "Smith"}},
      {"id": "c1", "label": "Crime", "properties": {"type": "Drugs"}}
    ],
    "edges": [
      {"id": "e1", "from": "p1", "to": "c1", "label": "PARTY_TO"}
    ]
  }
}
```

**Fields:**
- `question` - Original question
- `answer` - Natural language answer
- `cypher` - Generated Cypher query
- `results` - Raw query results (list of dictionaries)
- `attempts` - Number of retry attempts (1-3)
- `execution_time_ms` - Total execution time
- `graph_data` - Nodes and edges for visualization

**Error Response:**
```json
{
  "detail": "Failed to process query after 3 attempts"
}
```

#### `GET /api/health`
Check system health and connectivity.

**Response:**
```json
{
  "status": "healthy",
  "neo4j_connected": true,
  "llm_provider": "groq",
  "schema_loaded": true,
  "examples_loaded": true,
  "examples_count": 24
}
```

#### `GET /api/schema`
Get the introspected Neo4j schema.

**Response:**
```json
{
  "schema": "NODES:\n  Person(name, surname, age, nhs_no)\n  Crime(type, date, charge, last_outcome)\n...",
  "node_count": 11,
  "relationship_count": 17,
  "property_values": {
    "Crime.type": ["Burglary", "Drugs", "Robbery", "Theft", "Violence"],
    "Officer.rank": ["Constable", "Inspector", "Sergeant"]
  }
}
```

#### `GET /api/examples`
Get all few-shot examples.

**Response:**
```json
{
  "examples": [
    {
      "question": "How many crimes are recorded?",
      "cypher": "MATCH (c:Crime)\nRETURN count(c) AS total_crimes"
    },
    ...
  ],
  "count": 24
}
```

---

## Architecture

### Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Environment configuration
│   ├── database.py          # Neo4j connection management
│   ├── llm.py               # LLM provider factory
│   └── models.py            # Pydantic request/response models
│
├── core/
│   ├── schema_introspector.py   # Auto-fetch Neo4j schema
│   ├── few_shot_loader.py       # Load few-shot examples from YAML
│   ├── cypher_generator.py      # LLM-based Cypher generation
│   ├── query_executor.py        # Execute queries with retry logic
│   ├── answer_generator.py      # Generate natural language answers
│   └── pipeline.py              # 3-step pipeline orchestration
│
├── core/few_shot_examples.yaml  # 24 curated question→Cypher pairs
│
├── tests/
│   ├── conftest.py              # Pytest fixtures
│   ├── test_*.py                # Unit tests for each module
│   ├── test_integration.py      # Full pipeline integration tests
│   └── manual_test_checklist.md # Manual testing scenarios
│
├── .env                         # Environment variables (create from template)
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

### Pipeline Flow

```
User Question
     ↓
[1] Cypher Generator (LLM)
     ├── Schema Context (introspected from Neo4j)
     ├── Few-Shot Examples (24 examples)
     └── Error Context (if retry)
     ↓
[2] Query Executor
     ├── Execute on Neo4j
     ├── On Syntax Error → Retry with error feedback
     ├── On Empty Results → Retry with reformulation hint
     └── On Success → Extract graph data
     ↓
[3] Answer Generator (LLM)
     ├── Question + Cypher + Results
     └── Generate natural language answer
     ↓
Response (JSON)
```

### Retry Logic

The system automatically retries up to 3 times:

1. **Syntax Error**: Feeds error message back to LLM for self-correction
2. **Empty Results**: Asks LLM to relax filters or try alternate paths
3. **Max Retries**: Returns empty results with helpful message

---

## Testing

### Run All Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov=core --cov-report=html

# Run specific test file
pytest tests/test_integration.py -v

# Run specific test
pytest tests/test_pipeline.py::test_pipeline_orchestrates_full_flow -v
```

### Test Categories

1. **Unit Tests**: Test individual components (schema introspector, cypher generator, etc.)
2. **Integration Tests**: Test full pipeline with mocked Neo4j and LLM
3. **Manual Tests**: See `tests/manual_test_checklist.md` for comprehensive scenarios

### Manual Testing

Follow the checklist in `tests/manual_test_checklist.md`:
- 55+ test scenarios covering all features
- Basic queries, relationships, aggregations, error handling
- UI/UX verification
- Performance testing
- Cross-browser compatibility

### Example Test Questions

```bash
# Basic count
curl -X POST http://localhost:8000/api/ask -H "Content-Type: application/json" \
  -d '{"question": "How many crimes are recorded?"}'

# Relationship query
curl -X POST http://localhost:8000/api/ask -H "Content-Type: application/json" \
  -d '{"question": "Who are the people involved in crimes?"}'

# Multi-hop with filter
curl -X POST http://localhost:8000/api/ask -H "Content-Type: application/json" \
  -d '{"question": "Find people involved in drug crimes in area WN"}'

# Aggregation
curl -X POST http://localhost:8000/api/ask -H "Content-Type: application/json" \
  -d '{"question": "Which area has the highest number of crimes?"}'
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEO4J_URI` | Yes | - | Neo4j connection URI |
| `NEO4J_USERNAME` | Yes | - | Neo4j username |
| `NEO4J_PASSWORD` | Yes | - | Neo4j password |
| `NEO4J_DATABASE` | No | `neo4j` | Database name |
| `GROQ_API_KEY` | No* | - | Groq API key |
| `OPENAI_API_KEY` | No* | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | No* | - | Anthropic API key |
| `GOOGLE_API_KEY` | No* | - | Google API key |
| `LOG_LEVEL` | No | `INFO` | Logging level |

*At least one LLM API key is required

### Adding Custom Few-Shot Examples

Edit `core/few_shot_examples.yaml`:

```yaml
examples:
  - question: "Your custom question"
    cypher: |
      MATCH (n:YourPattern)
      WHERE n.property = 'value'
      RETURN n
```

The system automatically loads examples on startup.

---

## Development

### Code Style

```bash
# Format code
black app/ core/ tests/

# Lint code
flake8 app/ core/ tests/

# Type checking
mypy app/ core/
```

### Adding New Endpoints

1. Add route handler in `app/main.py`
2. Define request/response models in `app/models.py`
3. Add tests in `tests/test_api.py`

### Debugging

Enable detailed logging:

```bash
LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

View logs for:
- Generated Cypher queries
- Neo4j execution times
- LLM invocations
- Retry attempts and error contexts

---

## Performance Tuning

### Response Times

Typical response times (on first attempt):
- Simple count query: < 1 second
- Relationship query: 1-2 seconds
- Multi-hop query: 2-3 seconds
- Complex aggregation: 3-5 seconds

### Optimization Tips

1. **Schema Caching**: Schema is introspected once at startup, not per-request
2. **Connection Pooling**: Neo4j driver maintains connection pool
3. **LLM Choice**: Groq is fastest, Claude/GPT-4o most accurate
4. **Few-Shot Examples**: More examples = better accuracy but longer prompts

### Scaling

For production:
- Use gunicorn with multiple workers: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker`
- Enable Neo4j connection pooling (configured in `app/database.py`)
- Consider caching frequent queries with Redis
- Rate limit API with `slowapi`

---

## Troubleshooting

### Neo4j Connection Issues

```bash
# Test connection
neo4j-admin connectivity-test <URI>

# Check credentials in .env
# Verify database exists and is online
```

### LLM API Issues

```bash
# Test Groq
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"

# Test OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Empty Results

Check:
1. Database has data: `MATCH (n) RETURN count(n)`
2. Schema introspection working: `curl http://localhost:8000/api/schema`
3. Few-shot examples loaded: `curl http://localhost:8000/api/examples`

### Slow Queries

Enable query profiling:
```cypher
PROFILE <your_generated_query>
```

Add indexes in Neo4j:
```cypher
CREATE INDEX person_name FOR (p:Person) ON (p.name, p.surname);
CREATE INDEX crime_type FOR (c:Crime) ON (c.type);
```

---

## Contributing

1. Write tests for new features
2. Follow existing code structure
3. Update documentation
4. Run full test suite before committing

---

## License

Part of the Investigraph POLE NL-to-Cypher QA System.
