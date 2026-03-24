# POLE Neo4j — Natural Language to Cypher QA System
## Design Specification

**Date:** 2026-03-25
**Status:** Approved Design
**Target Users:** Crime analysts and investigators
**Implementation Approach:** Direct Generation (3-Step Pipeline)

---

## Executive Summary

Build a natural-language-to-Cypher QA system for crime investigation analysts working with a POLE (Person, Object, Location, Event) knowledge graph in Neo4j. The system allows analysts to ask questions in plain English and receive answers with transparent Cypher query generation, tabular results, and graph visualization.

**Key Design Decisions:**
- **Architecture**: 3-step pipeline (Generate → Execute with Retry → Answer)
- **LLM**: LLaMA 3.3 70B via Groq (free tier)
- **Frontend**: React + Vite with full-featured UI (chat, graph viz, export)
- **Backend**: FastAPI (Python) with comprehensive retry logic
- **Testing**: Automated test suite covering 24 few-shot examples + novel queries

---

## 1. System Context

### Database Analysis Summary

The POLE crime investigation database contains:
- **Nodes**: ~61,569 records across 11 types (Person, Crime, Location, Officer, Vehicle, Phone, etc.)
- **Relationships**: ~110,563 records across 17 types (PARTY_TO, INVESTIGATED_BY, KNOWS, etc.)
- **Crime records**: 28,762 crimes with 100% officer and location coverage
- **Geographic hierarchy**: Complete Location → PostCode → AREA linkage

**Data Quality Insights:**
- ✅ **Strong coverage**: Crime investigations, locations, officers, vehicles, phone communications
- ⚠️ **Sparse data**: Only 55 PARTY_TO relationships, Person.age (100% empty), Crime.note/charge (99% empty)
- ⚠️ **Minimal objects**: Only 7 Object records (unreliable for queries)

**Design Implication**: Few-shot examples and prompts will focus on well-populated data paths and gracefully handle sparse fields.

### User Requirements

**Primary Users:** Crime analysts/investigators who:
- Need quick investigative queries
- Prefer accuracy over speed
- Value transparency (want to see generated Cypher)
- Are comfortable with technical details

**Use Cases:**
1. Find officers investigating specific crime types
2. Identify crime patterns by geographic area
3. Explore social networks (who knows criminals)
4. Analyze phone communication patterns
5. Track vehicle involvement in crimes
6. Examine family relationships in investigations

---

## 2. System Architecture

### High-Level Design

```
┌─────────────────┐
│  React Frontend │
│  (Port 5173)    │
└────────┬────────┘
         │ HTTP/JSON
         ↓
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │         POST /api/ask Pipeline              │  │
│  │                                              │  │
│  │  [1] Cypher Generator                       │  │
│  │      • Full schema + 24 examples            │  │
│  │      • Property values for filtering        │  │
│  │      • LLaMA 3.3 70B (Groq)                │  │
│  │           ↓                                  │  │
│  │  [2] Query Executor (with retry)            │  │
│  │      • Execute on Neo4j                     │  │
│  │      • Self-correct syntax errors           │  │
│  │      • Reformulate if empty results         │  │
│  │      • Max 3 attempts                       │  │
│  │           ↓                                  │  │
│  │  [3] Answer Generator                       │  │
│  │      • Synthesize natural language          │  │
│  │      • Professional analyst tone            │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  Supporting Components:                             │
│  • Schema Introspector (cached at startup)         │
│  • Few-Shot Example Loader (24 Q→Cypher pairs)    │
│  • Graph Data Extractor (for visualization)        │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
            ┌──────────────┐
            │  Neo4j POLE  │
            │   Database   │
            └──────────────┘
```

### Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Frontend | React 18 + Vite | Modern, fast dev experience |
| Backend | FastAPI (Python) | Fast, async, auto-docs |
| Database | Neo4j (existing) | Already populated |
| LLM | LLaMA 3.3 70B (Groq) | Free tier, good with few-shots |
| Graph Viz | vis-network | Lightweight, Neo4j-compatible |
| Testing | pytest + pytest-mock | Standard Python testing |

---

## 3. API Design

### Core Endpoint: POST /api/ask

**Request:**
```json
{
  "question": "Which officers investigated drug crimes?"
}
```

**Response:**
```json
{
  "answer": "Found 145 officers investigating drug-related crimes. Top investigators: Sergeant James Miller (23 cases), PC Sarah Thompson (19 cases), Inspector David Chen (17 cases).",
  "cypher": "MATCH (o:Officer)<-[:INVESTIGATED_BY]-(c:Crime)\nWHERE toLower(c.type) CONTAINS 'drug'\nRETURN o.name, o.rank, count(c) AS cases\nORDER BY cases DESC",
  "results": [
    {"o.name": "James Miller", "o.rank": "Sergeant", "cases": 23},
    {"o.name": "Sarah Thompson", "o.rank": "Police Constable", "cases": 19},
    {"o.name": "David Chen", "o.rank": "Inspector", "cases": 17}
  ],
  "graph_data": {
    "nodes": [
      {"id": "o123", "label": "Officer", "properties": {"name": "James Miller", "rank": "Sergeant"}},
      {"id": "c456", "label": "Crime", "properties": {"type": "Drugs", "date": "24/08/2017"}}
    ],
    "edges": [
      {"from": "c456", "to": "o123", "type": "INVESTIGATED_BY"}
    ]
  },
  "attempts": 1,
  "execution_time_ms": 2450
}
```

**Error Response:**
```json
{
  "answer": "Unable to process query after 3 attempts. Please try rephrasing your question.",
  "cypher": "MATCH (n:InvalidLabel) RETURN n",
  "results": [],
  "error": "Syntax error: InvalidLabel not found in schema",
  "attempts": 3,
  "execution_time_ms": 8200
}
```

### Supporting Endpoints

**GET /api/health**
- Check Neo4j connectivity
- Verify Groq API key validity
- Return system status

**GET /api/schema**
- Return introspected Neo4j schema
- Useful for debugging and manual query building

**GET /api/examples**
- Return all 24 few-shot examples
- For UI reference/documentation

---

## 4. Backend Implementation

### Project Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI app, startup hooks
│   ├── config.py                  # Load .env, validate config
│   ├── database.py                # Neo4j connection singleton
│   ├── llm.py                     # Groq client wrapper
│   ├── api/
│   │   └── routes.py              # /api/ask, /api/health, /api/schema
│   └── models/
│       └── schemas.py             # Pydantic request/response models
├── core/
│   ├── schema_introspector.py     # Fetch schema from Neo4j (cached)
│   ├── few_shot_loader.py         # Load YAML examples
│   ├── cypher_generator.py        # LLM-based Cypher generation
│   ├── query_executor.py          # Execute + retry loop
│   ├── answer_generator.py        # NL answer synthesis
│   └── pipeline.py                # Orchestrate 3-step flow
├── data/
│   └── few_shot_examples.yaml     # 24 Q→Cypher pairs
├── tests/
│   ├── test_generator.py          # Unit tests
│   ├── test_integration.py        # Pipeline tests
│   └── benchmark.py               # Performance benchmarks
├── .env                           # Credentials (not committed)
└── requirements.txt
```

### Key Components

#### Schema Introspector (`core/schema_introspector.py`)

Runs once at FastAPI startup, caches results in memory.

**Queries Neo4j for:**
1. Node labels with properties
2. Relationship types with source/target
3. Categorical property values (Crime.type, Officer.rank, Vehicle.make, etc.)
4. Sample data (3 records per label for reference)

**Output Format:**
```
NODES:
  Person(name: string, surname: string, age: string, nhs_no: string)
  Crime(type: string, date: string, charge: string, last_outcome: string, note: string)
  Location(address: string, postcode: string, latitude: double, longitude: double)
  ...

RELATIONSHIPS:
  (Person)-[:PARTY_TO]->(Crime)
  (Person)-[:CURRENT_ADDRESS]->(Location)
  (Crime)-[:OCCURRED_AT]->(Location)
  (Crime)-[:INVESTIGATED_BY]->(Officer)
  ...

PROPERTY VALUES:
  Crime.type: ["Burglary", "Criminal damage and arson", "Drugs", "Public order", "Robbery", "Shoplifting", "Theft from the person", "Vehicle crime", "Violence and sexual offences"]
  Crime.last_outcome: ["Investigation complete; no suspect identified", "Unable to prosecute suspect", "Under investigation", "Offender sent to prison", "Awaiting court outcome"]
  Officer.rank: ["Police Constable", "Sergeant", "Inspector", "Chief Inspector"]
  Vehicle.make: ["Audi", "BMW", "Chevrolet", "Dodge", "Ford", "Honda", "Jaguar", "Mercedes-Benz", "Toyota", "Volkswagen", ...]

DATA LIMITATIONS:
  • Person.age: Not available (field is empty)
  • Crime.note and Crime.charge: Rarely populated (99% empty)
  • PARTY_TO relationships: Sparse (only 55 records for 28,762 crimes)
  • Object data: Minimal (7 records)
```

#### Cypher Generator (`core/cypher_generator.py`)

Single LLM call with comprehensive context.

**Prompt Template:**
```python
SYSTEM_PROMPT = f"""
You are an expert Neo4j Cypher query generator for a POLE (Person, Object,
Location, Event) crime investigation knowledge graph.

═══ GRAPH SCHEMA ═══
{schema_text}

═══ PROPERTY VALUES (for filtering) ═══
{property_values_text}

═══ DATA LIMITATIONS ═══
- Person.age: Not available (empty)
- Crime.note/charge: Rarely populated
- PARTY_TO relationships: Sparse (55 total)
- Objects: Minimal data (7 records)

When users ask about unavailable data:
- For age queries: Don't include age in RETURN clause
- For "who committed crime X": Use available relationships (KNOWS, family, phones)
- For evidence/objects: Generate valid query but results will be limited

═══ EXAMPLE QUERIES ═══
{few_shot_examples}  # All 24 examples formatted as Q→Cypher pairs

═══ RULES ═══
1. Use ONLY the node labels, relationships, and properties from the schema
2. Follow relationship directions EXACTLY as shown
3. For string filtering: toLower(n.prop) CONTAINS 'value'
4. Use exact property values from PROPERTY VALUES section
5. Return ONLY the Cypher query - no explanations, no markdown fences
6. NEVER generate MERGE, DELETE, SET, CREATE, DROP, REMOVE
7. For "who" questions → target Person nodes
8. For count/most/least → use count(), ORDER BY, LIMIT
9. Use CONTAINS for partial matching when unsure of exact values
10. Always include meaningful RETURN aliases

{error_context}  # Empty on first attempt; populated on retry
"""

USER_PROMPT = f"Generate a Cypher query for: {question}"
```

#### Query Executor with Retry (`core/query_executor.py`)

**Logic:**
```python
MAX_RETRIES = 3

def execute_with_retry(cypher, question, schema_ctx, examples):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Execute on Neo4j
            results = neo4j_client.query(cypher)

            # Success with results
            if results:
                return {
                    "results": results,
                    "cypher": cypher,
                    "attempts": attempt,
                    "graph_data": extract_graph_data(results)
                }

            # Empty results - reformulate if retries left
            if attempt < MAX_RETRIES:
                error_ctx = f"""
                Previous query returned 0 results:
                {cypher}

                Suggestions:
                - Try relaxing WHERE filters
                - Use CONTAINS instead of exact matches
                - Check relationship direction
                - Verify property names match schema
                """
                cypher = regenerate_cypher(question, schema_ctx, examples, error_ctx)
            else:
                return {
                    "results": [],
                    "cypher": cypher,
                    "attempts": attempt,
                    "error": "No results found after 3 attempts"
                }

        except Neo4jSyntaxError as e:
            # Syntax error - self-correct if retries left
            if attempt < MAX_RETRIES:
                error_ctx = f"""
                Previous query failed with syntax error:
                Error: {str(e)}
                Failed Query:
                {cypher}

                Please fix the syntax error and generate a corrected query.
                """
                cypher = regenerate_cypher(question, schema_ctx, examples, error_ctx)
            else:
                return {
                    "results": [],
                    "cypher": cypher,
                    "attempts": attempt,
                    "error": f"Syntax error: {str(e)}"
                }

        except Exception as e:
            # Other errors
            return {
                "results": [],
                "cypher": cypher,
                "attempts": attempt,
                "error": f"Execution error: {str(e)}"
            }
```

#### Answer Generator (`core/answer_generator.py`)

Second LLM call for natural language synthesis.

**Prompt:**
```python
ANSWER_PROMPT = f"""
You are a crime investigation analyst interpreting database query results.

Question: {question}
Cypher Query Used: {cypher}
Results ({len(results)} records):
{format_results(results)}

Instructions:
- Provide a clear, direct answer to the analyst's question
- If results are empty, say so professionally: "No records found matching criteria"
- Format multiple results as numbered lists or summary statistics
- Mention relevant details (counts, key names, patterns)
- Do NOT mention Cypher, databases, or technical details
- Be concise - analysts need quick insights
- If data limitations affected results, mention it briefly (e.g., "Note: Person age data not available")
"""
```

---

## 5. Frontend Implementation

### Project Structure

```
frontend/
├── src/
│   ├── App.jsx                    # Main app component
│   ├── main.jsx                   # React entry point
│   ├── components/
│   │   ├── ChatInterface.jsx      # Main chat container
│   │   ├── QuestionInput.jsx      # Input + submit button
│   │   ├── MessageList.jsx        # Conversation history
│   │   ├── AnswerCard.jsx         # Single Q&A display
│   │   ├── CypherPanel.jsx        # Collapsible Cypher viewer
│   │   ├── ResultsTable.jsx       # Tabular results
│   │   ├── GraphVisualization.jsx # vis-network graph
│   │   └── ExportButton.jsx       # CSV export
│   ├── services/
│   │   └── api.js                 # Axios backend calls
│   ├── hooks/
│   │   └── useChat.js             # Chat state management
│   └── styles/
│       └── main.css               # Professional analyst theme
├── package.json
└── vite.config.js
```

### UI Layout

```
┌────────────────────────────────────────────────────────────┐
│  🔍 POLE Investigation QA System                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────┬──────────────────────────────┐  │
│  │  Chat Area           │  Visualization Panel         │  │
│  │                      │                              │  │
│  │  Q: Which officers   │  ┌─────────────────────────┐│  │
│  │     investigated     │  │   [Graph/Table Toggle]  ││  │
│  │     drug crimes?     │  │                          ││  │
│  │                      │  │   [Network Graph Shows   ││  │
│  │  A: Found 145        │  │    Officer → Crime       ││  │
│  │     officers...      │  │    relationships]        ││  │
│  │                      │  │                          ││  │
│  │  [▼ Show Cypher]     │  │                          ││  │
│  │  [📊 View Table]     │  │   [Pan, Zoom controls]   ││  │
│  │  [💾 Export CSV]     │  │                          ││  │
│  │                      │  └─────────────────────────┘│  │
│  │  Attempt 1 of 1      │                              │  │
│  │  Executed in 2.4s    │  [Results: 145 records]      │  │
│  │                      │                              │  │
│  └──────────────────────┴──────────────────────────────┘  │
│                                                            │
│  ┌──────────────────────────────────────┐  [Clear Chat]  │
│  │ Type your question here...            │  [    Ask   ]  │
│  └──────────────────────────────────────┘                 │
└────────────────────────────────────────────────────────────┘
```

### Key Features

**1. Chat Interface**
- Session-based conversation history (not persisted)
- Each message shows: question, answer, timestamp, execution time
- Collapsible Cypher panel with syntax highlighting
- Copy-to-clipboard for Cypher queries

**2. Results Display**
- **Table View**: Sortable columns, pagination for >100 rows
- **Graph View**: vis-network visualization with color-coded node types
  - Person: Blue
  - Crime: Red
  - Location: Green
  - Officer: Purple
  - Vehicle: Orange
- Toggle between table and graph views
- Node tooltips show properties on hover

**3. Export Functionality**
- Export current query results to CSV
- Export full conversation history as JSON
- Includes Cypher queries in export

**4. Loading States**
- Spinner during query execution
- Retry indicator: "Attempt 2 of 3..."
- Progress feedback for analysts

**5. Error Handling**
- Network errors: "Unable to connect to server"
- Timeout: "Query took too long - try a simpler question"
- Empty results: "No matching records found. Try rephrasing."
- Syntax failures: "Unable to generate valid query after 3 attempts."

---

## 6. Few-Shot Examples Strategy

### Category Organization

Based on database analysis, examples focus on **well-populated data paths**:

**Category 1: Crime Basics (4 examples)**
- Count total crimes
- List distinct crime types
- Filter crimes by type (e.g., "drug")
- Filter crimes by outcome

**Category 2: Investigation Queries (3 examples)**
- Find officers investigating specific crime types
- Identify officer with most cases
- Show all officer-crime relationships

**Category 3: Geographic Analysis (3 examples)**
- Crimes by location
- Crimes by area
- Area with highest crime count

**Category 4: Communication Patterns (3 examples)**
- Phone calls made/received
- Communication between specific phones
- Phones of people involved in crimes

**Category 5: Social Networks (2 examples)**
- People who know criminals
- Family relationships (SIBLING, PARENT)

**Category 6: Vehicles (2 examples)**
- Vehicles involved in crimes
- Vehicle makes used in specific crime types

**Category 7: Multi-Hop Queries (4 examples)**
- People involved in crimes in specific areas
- Vehicles used in crimes by area
- Friends of family members of criminals
- Complex relationship traversals

**Category 8: Aggregations (3 examples)**
- Count queries with GROUP BY
- Top-N queries with ORDER BY + LIMIT
- Average calculations (e.g., call duration)

### Example Quality Guidelines

Each example demonstrates:
1. **Defensive string matching**: `toLower(c.type) CONTAINS 'drug'`
2. **Meaningful aliases**: `count(c) AS total_crimes`
3. **Proper relationship direction**: Follow schema exactly
4. **Realistic property values**: Use actual values from database

### Sample Examples

```yaml
examples:
  # Crime basics
  - question: "How many crimes are recorded?"
    cypher: |
      MATCH (c:Crime)
      RETURN count(c) AS total_crimes

  - question: "Show all crimes related to drugs"
    cypher: |
      MATCH (c:Crime)
      WHERE toLower(c.type) CONTAINS 'drug'
      RETURN c.id, c.type, c.date, c.last_outcome
      LIMIT 50

  # Investigation
  - question: "Which officers investigated drug crimes?"
    cypher: |
      MATCH (o:Officer)<-[:INVESTIGATED_BY]-(c:Crime)
      WHERE toLower(c.type) CONTAINS 'drug'
      RETURN o.name, o.rank, count(c) AS cases
      ORDER BY cases DESC

  # Geographic
  - question: "Which area has the most crimes?"
    cypher: |
      MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
            -[:LOCATION_IN_AREA]->(a:AREA)
      RETURN a.areaCode, count(c) AS crime_count
      ORDER BY crime_count DESC LIMIT 1

  # Social network with family relationships
  - question: "Find family members of people involved in crimes"
    cypher: |
      MATCH (p1:Person)-[r:FAMILY_REL]->(p2:Person)
            -[:PARTY_TO]->(c:Crime)
      RETURN p1.name, p2.name, r.rel_type, c.type

  # Communication
  - question: "Find communication between two phones"
    cypher: |
      MATCH (pc:PhoneCall)-[:CALLER]->(ph1:Phone)
      MATCH (pc)-[:CALLED]->(ph2:Phone)
      RETURN ph1.phoneNo AS caller, ph2.phoneNo AS receiver,
             pc.call_time, pc.call_duration
      LIMIT 50
```

### Handling Data Gaps

The system prompt explicitly warns about sparse fields:
- **Person.age**: Not available → don't include in queries
- **Crime.note/charge**: Rarely populated → valid to query but expect empty results
- **PARTY_TO**: Only 55 records → use alternative paths (KNOWS relationships, phone records)
- **Objects**: Minimal data → generate query but warn about limited results

---

## 7. Testing Strategy

### Automated Test Suite

**1. Few-Shot Validation (24 tests)**
```python
@pytest.mark.parametrize("example", load_few_shot_examples())
def test_example_query(self, example):
    """Test each few-shot example returns valid results"""
    result = run_query(example["question"])

    assert result["results"], f"Empty results for: {example['question']}"
    assert result["attempts"] <= 3
    assert "error" not in result
```

**Success Criteria**: 24/24 pass (100%)

**2. Novel Query Tests (5 tests)**
- "List all officers with rank Inspector"
- "How many crimes happened in area WN?"
- "Find phones of people who know criminals"
- "Which vehicle makes were involved in robbery?"
- "Show family relationships (siblings only)"

**Success Criteria**: ≥4/5 pass (80%+)

**3. Edge Cases (5 tests)**
- Empty results: "Find crimes by person age 100"
- Ambiguous: "Show me everything"
- Invalid entity: "Find crimes by Batman"
- Complex multi-hop: "Friends of family members of criminals in area BL"
- Data limitation: "What's the average age of criminals?"

**Success Criteria**: Graceful handling (no crashes, appropriate error messages)

**4. Retry Logic Tests (3 tests)**
- Syntax error recovery: Inject bad Cypher, verify self-correction
- Empty results reformulation: Too-strict filter, verify relaxation
- Max retries: Force 3 failures, verify error handling

### Performance Benchmarks

**Metrics:**
- **Response time**: Target <5s for 90% of queries
- **Success rate**: Target >85% on novel queries
- **Retry rate**: Target <30% need retries
- **Token usage**: Track average tokens per query

**Benchmark Script** (`tests/benchmark.py`):
```python
def run_benchmark():
    test_queries = load_few_shot_examples() + load_novel_queries()

    results = {
        "total": len(test_queries),
        "success": 0,
        "avg_time_ms": 0,
        "avg_attempts": 0
    }

    for query in test_queries:
        start = time.time()
        result = run_query(query["question"])
        elapsed = (time.time() - start) * 1000

        if result["results"]:
            results["success"] += 1

        results["avg_time_ms"] += elapsed
        results["avg_attempts"] += result["attempts"]

    results["avg_time_ms"] /= results["total"]
    results["avg_attempts"] /= results["total"]

    return results
```

### Manual Testing Checklist

Before deployment:
- [ ] Chat interface loads correctly
- [ ] Questions submit via Enter key
- [ ] Cypher panel expands/collapses
- [ ] Graph visualization renders
- [ ] Table sorting and pagination work
- [ ] CSV export downloads
- [ ] Error messages display properly
- [ ] Loading spinner shows during execution
- [ ] Retry indicator updates correctly
- [ ] All 24 few-shot examples return results

---

## 8. Configuration & Deployment

### Environment Configuration (.env)

```env
# Neo4j Database (already populated)
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=xxxxx
NEO4J_DATABASE=pole

# LLM - Groq (LLaMA 3.3 70B - Free Tier)
GROQ_API_KEY=gsk_xxxxx

# Server Config
BACKEND_PORT=8000
FRONTEND_PORT=5173
CORS_ORIGINS=http://localhost:5173

# Logging
LOG_LEVEL=INFO
LOG_QUERIES=true  # Log generated Cypher for analysis
```

### Dependencies

**Backend** (`requirements.txt`):
```
fastapi==0.111.0
uvicorn[standard]==0.30.1
neo4j==5.23.1
pydantic==2.8.2
python-dotenv==1.0.1
pyyaml==6.0
groq==0.9.0
pytest==8.2.0
pytest-mock==3.14.0
```

**Frontend** (`package.json`):
```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "axios": "^1.7.0",
    "vis-network": "^9.1.9"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^5.3.0"
  }
}
```

### Deployment Options

**Option 1: Local Development** (Recommended for Start)
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev  # Vite dev server on port 5173
```

**Option 2: Docker Compose** (for Production)
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env

  frontend:
    build: ./frontend
    ports: ["80:80"]
    depends_on: [backend]
```

**Option 3: Cloud Deployment**
- **Backend**: Railway, Render, or Fly.io
- **Frontend**: Vercel, Netlify, or Cloudflare Pages
- **Database**: Keep on Neo4j AuraDB (already cloud-hosted)

---

## 9. Success Criteria

### Functional Requirements

| Requirement | Acceptance Criteria |
|-------------|---------------------|
| Natural language queries | Users can ask questions in plain English |
| Valid Cypher generation | Generated queries follow Neo4j syntax |
| Result display | Shows answer + table + graph visualization |
| Self-correction | Retry loop recovers from syntax errors |
| Export functionality | CSV export works for results |
| Transparency | Cypher queries visible to analysts |

### Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Response time | <5s for 90% of queries | Benchmark script |
| Few-shot accuracy | 24/24 (100%) | Automated tests |
| Novel query accuracy | ≥4/5 (80%) | Automated tests |
| Retry rate | <30% need retries | Production logs |

### Quality Requirements

| Aspect | Requirement |
|--------|-------------|
| Cypher quality | Follows Neo4j best practices (proper indexing, relationship direction) |
| Error messages | Professional, helpful, analyst-appropriate |
| UI design | Clean, functional, not consumer-facing |
| Code quality | Documented, tested, maintainable |

---

## 10. Risk Assessment & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| LLaMA 3.3 generates poor Cypher | High | Medium | Retry loop + strong few-shots. Upgrade to Gemini Flash ($0.10/1M) if needed |
| Groq free tier rate limits | Medium | Low | Add exponential backoff. Upgrade to paid tier if needed |
| Empty results confuse users | Low | Medium | Clear messaging: "No records found. Try rephrasing." |
| Graph viz slow on large results | Low | Low | Limit rendering to first 100 nodes/edges |
| PARTY_TO sparsity breaks queries | Medium | Low | Few-shots avoid PARTY_TO, use alternative relationships |
| Schema changes break queries | Medium | Low | Schema introspection runs at startup, adapts automatically |

---

## 11. Implementation Phases

### Phase 1: Backend Core (2-3 days)
**Deliverables:**
- Schema introspector
- Cypher generator with LLM integration
- Query executor with retry loop
- Pipeline orchestrator
- Basic API endpoints

**Validation:** Can execute manual queries via API

### Phase 2: Few-Shot Examples (1 day)
**Deliverables:**
- Complete `few_shot_examples.yaml` with all 24 examples
- Examples tested against actual database
- Property values match real data

**Validation:** All examples return non-empty results

### Phase 3: React Frontend (2-3 days)
**Deliverables:**
- Chat interface
- Results table
- Graph visualization
- Cypher panel
- Export functionality

**Validation:** Full UI workflow works end-to-end

### Phase 4: Testing (1 day)
**Deliverables:**
- Automated test suite (pytest)
- Benchmark script
- Manual test checklist completed

**Validation:** All tests pass, performance targets met

### Phase 5: Polish & Documentation (1 day)
**Deliverables:**
- Error handling refined
- Logging configured
- README with setup instructions
- Deployment guide

**Validation:** System deployable by another developer

**Total Estimate: 7-9 days**

---

## 12. Future Enhancements (Out of Scope for V1)

**Not implementing now, but worth noting for future iterations:**

1. **User Authentication** - Multi-user support with saved sessions
2. **Query History Persistence** - Save queries to database for auditing
3. **Query Templates** - Saved/favorite queries for common investigations
4. **Advanced Filters** - Date range pickers, custom filter UI
5. **RAG Enhancement** - If examples grow beyond 50, switch to vector search
6. **Streaming Responses** - Real-time answer generation
7. **Multi-Database Support** - Switch between Neo4j instances
8. **Fine-Tuned Model** - If LLaMA 3.3 accuracy insufficient
9. **Query Suggestions** - Autocomplete based on common patterns
10. **Audit Logging** - Track all queries for compliance

---

## 13. Database-Specific Insights

### Leveraging Strong Data Paths

**High-Coverage Queries** (prioritize in examples):
- Crime investigations: 28,762 crimes, all have officers
- Geographic analysis: Complete Location → AREA hierarchy
- Officer workload: All crimes have INVESTIGATED_BY
- Phone communication: 534 PhoneCall records with full CALLER/CALLED

**Alternative Paths for Sparse Data**:
- Instead of PARTY_TO (55 records) → Use KNOWS relationships (586 records)
- Instead of Person.age → Focus on Person.name, Person.surname
- Instead of Crime.note → Focus on Crime.type, Crime.last_outcome

### Categorical Value Mapping

**Crime Types** (for few-shot examples):
- Use lowercase + CONTAINS: `toLower(c.type) CONTAINS 'drug'`
- Valid values: "Burglary", "Drugs", "Public order", "Robbery", "Shoplifting", "Theft from the person", "Vehicle crime", "Violence and sexual offences"

**Crime Outcomes**:
- Most common: "Investigation complete; no suspect identified"
- Others: "Unable to prosecute suspect", "Under investigation", "Offender sent to prison"

**Officer Ranks**:
- "Police Constable", "Sergeant", "Inspector", "Chief Inspector"

**Relationship Variants**:
- KNOWS, KNOWS_LW (long-while?), KNOWS_SN (social network?)
- FAMILY_REL with rel_type: "SIBLING", "PARENT"

---

## 14. Conclusion

This design provides a comprehensive, production-ready approach to building a natural-language-to-Cypher QA system for crime investigation analysts. The 3-step pipeline architecture balances simplicity with robustness, while the React frontend provides analysts with the transparency and visualization tools they need.

**Key Design Strengths:**
- ✅ Adapts to actual database quality (focuses on well-populated paths)
- ✅ Transparent for analysts (shows Cypher queries)
- ✅ Self-correcting (retry loop handles errors)
- ✅ Cost-effective (free-tier LLM with strong few-shots)
- ✅ Testable (comprehensive automated test suite)
- ✅ Maintainable (clear component boundaries, well-documented)

**Next Steps:**
1. Review and approve this design specification
2. Create detailed implementation plan with task breakdown
3. Begin Phase 1 development (backend core)

---

**Document Status:** ✅ Approved for Implementation
**Last Updated:** 2026-03-25
