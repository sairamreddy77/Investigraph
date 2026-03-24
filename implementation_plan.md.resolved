# POLE Neo4j — Intelligent Crime Investigation QA System

> A from-scratch implementation plan for building a natural-language-to-Cypher QA system over a POLE (Person, Object, Location, Event) crime knowledge graph.

---

## 1. System Overview

### Goal
Users ask natural-language questions about crime investigations → the system generates Cypher → executes against Neo4j → returns a clear answer with optional graph visualization.

### Architecture (3-Step Pipeline with Retry)

```mermaid
flowchart TD
    A["🧑 User Question"] --> B["⚡ Cypher Generator<br/>(Schema + Few-Shots + Property Values)"]
    B --> C["🗄️ Execute on Neo4j"]
    C -->|Syntax Error| D["🔄 Self-Correct<br/>(Feed error back to LLM)"]
    D --> B
    C -->|Empty Results| E["🔄 Reformulate<br/>(Relax filters, try alternate paths)"]
    E --> B
    C -->|Success| F["💬 Answer Generator"]
    F --> G["📊 Response + Graph Data"]

    style A fill:#4CAF50,color:#fff
    style B fill:#2196F3,color:#fff
    style C fill:#FF9800,color:#fff
    style F fill:#9C27B0,color:#fff
    style G fill:#4CAF50,color:#fff
```

### Why This Design?

| Current System (7 steps) | New System (3 steps) |
|---|---|
| Intent Parser → Schema Retriever → Planner → Generator → Validator → Executor → Answer | **Generator → Executor (with retry) → Answer** |
| 4 LLM calls per question | **1–2 LLM calls** (1 generate + 1 answer) |
| No retry on failure | **Up to 3 retry attempts** with error context |
| Narrow schema (2 nodes) | **Full schema** always available |
| No examples | **24 curated few-shot examples** |
| Rigid intent JSON bottleneck | **Direct question→Cypher generation** |

---

## 2. Knowledge Graph Schema (POLE Dataset)

### Node Labels (11)

| Label | Key Properties | Description |
|---|---|---|
| `Person` | `name`, `surname`, `age`, `nhs_no` | Individuals in the investigation |
| `Crime` | `type`, `date`, `charge`, `last_outcome`, `note` | Criminal incidents |
| `Location` | `address`, `postcode`, `latitude`, `longitude` | Physical locations |
| `Vehicle` | `make`, `model`, `reg`, `year` | Vehicles linked to crimes |
| `Object` | `description`, `type` | Evidence items |
| `Officer` | `name`, `surname`, `badge_no`, `rank` | Investigating officers |
| `Phone` | `phoneNo` | Phone numbers |
| `PhoneCall` | `call_date`, `call_time`, `call_duration`, `call_type` | Call records |
| `Email` | `email_address` | Email addresses |
| `PostCode` | `code` | Postal codes |
| `AREA` | `areaCode` | Geographic regions |

### Relationships (17)

```
Person  ─── PARTY_TO ──────→ Crime
Person  ─── CURRENT_ADDRESS → Location
Person  ─── HAS_PHONE ──────→ Phone
Person  ─── HAS_EMAIL ──────→ Email
Person  ─── KNOWS ──────────→ Person
Person  ─── KNOWS_LW ───────→ Person
Person  ─── KNOWS_PHONE ────→ Person
Person  ─── FAMILY_REL ─────→ Person      (rel_type property)

Crime   ─── OCCURRED_AT ────→ Location
Crime   ─── INVESTIGATED_BY → Officer

Vehicle ─── INVOLVED_IN ────→ Crime
Object  ─── INVOLVED_IN ────→ Crime

PhoneCall── CALLER ──────────→ Phone
PhoneCall── CALLED ──────────→ Phone

Location ── HAS_POSTCODE ───→ PostCode
Location ── LOCATION_IN_AREA→ AREA
PostCode ── POSTCODE_IN_AREA→ AREA
```

---

## 3. Project Structure

```
project/
├── .env                              # Credentials
├── requirements.txt                  # Python dependencies
│
├── app/
│   ├── main.py                       # FastAPI entry point
│   ├── config.py                     # Env config loader
│   ├── database.py                   # Neo4j connection (singleton)
│   ├── llm.py                        # LLM provider factory
│   ├── routes/
│   │   └── query.py                  # POST /ask endpoint
│   └── models/
│       └── schemas.py                # Pydantic request/response
│
├── core/
│   ├── schema_introspector.py        # Auto-fetch schema from Neo4j
│   ├── few_shot_examples.yaml        # 24 curated question→Cypher pairs
│   ├── cypher_generator.py           # Main LLM-based Cypher generation
│   ├── query_executor.py             # Execute + retry loop
│   ├── answer_generator.py           # NL answer synthesis
│   └── pipeline.py                   # 3-step orchestration
│
├── frontend/
│   ├── index.html                    # Main UI page
│   ├── style.css                     # Styling
│   └── app.js                        # Frontend logic
│
└── scripts/
    ├── introspect_schema.py          # One-off: dump schema to console
    └── test_queries.py               # Automated test harness
```

---

## 4. Component Specifications

### 4.1 Schema Introspector — `core/schema_introspector.py`

Runs **once at startup**, caches results in memory.

**Fetches via Cypher:**
```cypher
-- 1. Node labels with properties
MATCH (n) WITH DISTINCT labels(n) AS lbls, keys(n) AS props
RETURN lbls, props LIMIT 100

-- 2. Relationship types with source/target
CALL db.schema.visualization()

-- 3. Distinct values for categorical properties (≤50 values)
MATCH (c:Crime) RETURN DISTINCT c.type AS val ORDER BY val
MATCH (c:Crime) RETURN DISTINCT c.last_outcome AS val ORDER BY val
MATCH (o:Officer) RETURN DISTINCT o.rank AS val ORDER BY val
MATCH (v:Vehicle) RETURN DISTINCT v.make AS val ORDER BY val
-- ... etc for all string-typed categorical properties

-- 4. Sample data (3 rows per label)
MATCH (p:Person) RETURN p LIMIT 3
MATCH (c:Crime) RETURN c LIMIT 3
-- ... etc
```

**Output format** — a structured string like:
```
NODES:
  Person(name: string, surname: string, age: string, nhs_no: string)
  Crime(type: string, date: string, charge: string, last_outcome: string, note: string)
  ...

RELATIONSHIPS:
  (Person)-[:PARTY_TO]->(Crime)
  (Crime)-[:OCCURRED_AT]->(Location)
  ...

PROPERTY VALUES:
  Crime.type: ["Burglary", "Drugs", "Robbery", "Theft", "Violence"]
  Crime.last_outcome: ["Charged", "No suspect identified", "Under investigation"]
  Officer.rank: ["Constable", "Inspector", "Sergeant"]
  ...

SAMPLE DATA:
  Person: {name: "John", surname: "Smith", age: "34"}, {name: "Sarah", surname: "Jones", age: "28"}, ...
  Crime: {type: "Drugs", date: "2023-01-15", last_outcome: "Charged"}, ...
```

---

### 4.2 Few-Shot Examples — `core/few_shot_examples.yaml`

> [!IMPORTANT]
> This file is the **single biggest driver of query quality**. Each example teaches the LLM a query pattern.

```yaml
examples:
  # ── BASIC + FILTERING ──────────────────────────────
  - question: "How many crimes are recorded?"
    cypher: |
      MATCH (c:Crime)
      RETURN count(c) AS total_crimes

  - question: "What are the different types of crimes?"
    cypher: |
      MATCH (c:Crime)
      RETURN DISTINCT c.type

  - question: "Show all crimes related to drugs"
    cypher: |
      MATCH (c:Crime)
      WHERE toLower(c.type) CONTAINS 'drug'
      RETURN c.id, c.type, c.date

  - question: "Find crimes where no suspect was identified"
    cypher: |
      MATCH (c:Crime)
      WHERE toLower(c.last_outcome) CONTAINS 'no suspect'
      RETURN c.id, c.type, c.last_outcome

  - question: "Find crimes that resulted in a charge"
    cypher: |
      MATCH (c:Crime)
      WHERE c.charge IS NOT NULL AND c.charge <> ''
      RETURN c.id, c.type, c.charge

  # ── RELATIONSHIPS ──────────────────────────────────
  - question: "Who are the people involved in crimes?"
    cypher: |
      MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
      RETURN p.name, p.surname, c.type

  - question: "Which crimes are investigated by officers?"
    cypher: |
      MATCH (c:Crime)-[:INVESTIGATED_BY]->(o:Officer)
      RETURN c.type, o.name, o.rank

  - question: "Which vehicles are linked to crimes?"
    cypher: |
      MATCH (v:Vehicle)-[:INVOLVED_IN]->(c:Crime)
      RETURN v.make, v.model, v.reg, c.type

  - question: "Which objects are associated with crimes?"
    cypher: |
      MATCH (o:Object)-[:INVOLVED_IN]->(c:Crime)
      RETURN o.description, o.type, c.type

  - question: "Where do crimes occur?"
    cypher: |
      MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
      RETURN c.type, l.address, l.postcode

  # ── MULTI-HOP ─────────────────────────────────────
  - question: "Find people involved in crimes in each area"
    cypher: |
      MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
            -[:OCCURRED_AT]->(l:Location)
            -[:LOCATION_IN_AREA]->(a:AREA)
      RETURN p.name, c.type, a.areaCode

  - question: "Find people involved in drug crimes in area WN"
    cypher: |
      MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
            -[:OCCURRED_AT]->(l:Location)
            -[:LOCATION_IN_AREA]->(a:AREA)
      WHERE toLower(c.type) CONTAINS 'drug'
        AND toLower(a.areaCode) CONTAINS 'wn'
      RETURN p.name, c.type, a.areaCode

  - question: "Find vehicles used in crimes in specific areas"
    cypher: |
      MATCH (v:Vehicle)-[:INVOLVED_IN]->(c:Crime)
            -[:OCCURRED_AT]->(l:Location)
            -[:LOCATION_IN_AREA]->(a:AREA)
      RETURN v.make, v.model, a.areaCode, c.type

  - question: "Find officers investigating drug crimes"
    cypher: |
      MATCH (c:Crime)-[:INVESTIGATED_BY]->(o:Officer)
      WHERE toLower(c.type) CONTAINS 'drug'
      RETURN o.name, o.rank, c.type

  # ── NETWORK / GRAPH ───────────────────────────────
  - question: "Find people who know criminals"
    cypher: |
      MATCH (p1:Person)-[:KNOWS]->(p2:Person)-[:PARTY_TO]->(c:Crime)
      RETURN p1.name AS person, p2.name AS criminal, c.type

  - question: "Find family members of people involved in crimes"
    cypher: |
      MATCH (p1:Person)-[r:FAMILY_REL]->(p2:Person)-[:PARTY_TO]->(c:Crime)
      RETURN p1.name, p2.name, r.rel_type, c.type

  - question: "Find people connected to criminals via multiple relationships"
    cypher: |
      MATCH (p1:Person)-[:KNOWS|KNOWS_LW|KNOWS_SN]->(p2:Person)
            -[:PARTY_TO]->(c:Crime)
      RETURN p1.name, p2.name, c.type

  # ── PHONE / COMMUNICATION ─────────────────────────
  - question: "Find phone numbers of people involved in crimes"
    cypher: |
      MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
      MATCH (p)-[:HAS_PHONE]->(ph:Phone)
      RETURN p.name, ph.phoneNo, c.type

  - question: "Find calls made by phones"
    cypher: |
      MATCH (pc:PhoneCall)-[:CALLER]->(ph:Phone)
      RETURN ph.phoneNo, pc.call_time, pc.call_duration

  - question: "Find calls received by phones"
    cypher: |
      MATCH (pc:PhoneCall)-[:CALLED]->(ph:Phone)
      RETURN ph.phoneNo, pc.call_time, pc.call_duration

  - question: "Find communication between two phones"
    cypher: |
      MATCH (pc:PhoneCall)-[:CALLER]->(ph1:Phone)
      MATCH (pc)-[:CALLED]->(ph2:Phone)
      RETURN ph1.phoneNo AS caller, ph2.phoneNo AS receiver, pc.call_time

  # ── AGGREGATIONS ───────────────────────────────────
  - question: "Which area has the highest number of crimes?"
    cypher: |
      MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
            -[:LOCATION_IN_AREA]->(a:AREA)
      RETURN a.areaCode, count(c) AS crime_count
      ORDER BY crime_count DESC LIMIT 1

  - question: "Which officer investigates the most crimes?"
    cypher: |
      MATCH (c:Crime)-[:INVESTIGATED_BY]->(o:Officer)
      RETURN o.name, count(c) AS total_cases
      ORDER BY total_cases DESC LIMIT 1

  - question: "Average duration of phone calls"
    cypher: |
      MATCH (pc:PhoneCall)
      RETURN avg(pc.call_duration) AS avg_duration
```

---

### 4.3 Cypher Generator — `core/cypher_generator.py`

The core intelligence. One LLM call that receives **everything it needs**.

**System Prompt Template:**

```
You are an expert Neo4j Cypher query generator for a POLE (Person, Object, 
Location, Event) crime investigation knowledge graph.

═══ GRAPH SCHEMA ═══
{schema_text}          ← from schema_introspector

═══ KNOWN PROPERTY VALUES ═══
{property_values_text} ← categorical values from Neo4j

═══ EXAMPLE QUERIES ═══
{few_shot_text}        ← all 24 examples formatted as Q→Cypher pairs

═══ RULES ═══
1. Use ONLY the node labels, relationships, and properties from the schema above.
2. Follow relationship directions EXACTLY as shown.
3. For string filtering, ALWAYS use: toLower(n.prop) CONTAINS 'value'
4. Use the EXACT property values from the "KNOWN PROPERTY VALUES" section.
5. Return ONLY the Cypher query. No explanations, no markdown fences.
6. Never generate MERGE, DELETE, SET, CREATE, DROP, or REMOVE statements.
7. For "who" questions → target Person nodes.
8. For count/most/least → use count(), ORDER BY, LIMIT.
9. When unsure about exact values, use CONTAINS for partial matching.
10. Always include meaningful RETURN aliases for readability.

{error_context}        ← empty on first attempt; error message on retry
```

**Function signature:**
```python
def generate_cypher(
    question: str,
    schema_context: str,
    few_shot_examples: list[dict],
    error_context: str = ""     # Populated on retry
) -> str:
```

---

### 4.4 Query Executor with Retry — `core/query_executor.py`

```python
MAX_RETRIES = 3

def execute_with_retry(cypher, question, schema_ctx, examples):
    for attempt in range(MAX_RETRIES):
        try:
            results = neo4j_graph.query(cypher)
            if results:
                return results, cypher
            
            # Empty results → ask LLM to reformulate
            if attempt < MAX_RETRIES - 1:
                error_ctx = (
                    f"Previous query returned 0 results:\n{cypher}\n"
                    f"Try relaxing filters or using a different traversal path."
                )
                cypher = generate_cypher(question, schema_ctx, examples, error_ctx)
        
        except Exception as e:
            # Syntax/execution error → ask LLM to self-correct
            if attempt < MAX_RETRIES - 1:
                error_ctx = (
                    f"Previous query failed with error:\n{str(e)}\n"
                    f"Failed query:\n{cypher}\nPlease fix the query."
                )
                cypher = generate_cypher(question, schema_ctx, examples, error_ctx)
            else:
                return [], cypher
    
    return [], cypher
```

---

### 4.5 Answer Generator — `core/answer_generator.py`

**System Prompt:**
```
You are a crime investigation analyst interpreting database query results.

Question: {question}
Query Used: {cypher}
Results: {results}

Rules:
- Give a clear, direct answer to the question.
- If results are empty, say so and suggest the user try a different query.
- Format lists and tables when there are multiple results.
- Do not mention Cypher or database internals unless the user asked about them.
- Be concise — analysts need quick answers.
```

---

### 4.6 Pipeline Orchestrator — `core/pipeline.py`

```python
# Cached at startup
_schema_context = None
_few_shot_examples = None

def init():
    """Call once at app startup."""
    global _schema_context, _few_shot_examples
    _schema_context = introspect_schema()
    _few_shot_examples = load_few_shot_examples("core/few_shot_examples.yaml")

def run_query(question: str) -> dict:
    # Step 1: Generate Cypher
    cypher = generate_cypher(question, _schema_context, _few_shot_examples)
    
    # Step 2: Execute with retry
    results, final_cypher = execute_with_retry(
        cypher, question, _schema_context, _few_shot_examples
    )
    
    # Step 3: Generate answer
    answer = generate_answer(question, final_cypher, results)
    
    return {
        "question": question,
        "cypher": final_cypher,
        "results": results,
        "answer": answer
    }
```

---

## 5. Configuration

### [.env](file:///c:/Users/SAIRAM%20REDDY/OneDrive/Desktop/Project2/code/.env)
```env
# Neo4j
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=xxxxx
NEO4J_PASSWORD=xxxxx
NEO4J_DATABASE=pole

# LLM (pick one)
GROQ_API_KEY=gsk_xxxxx              # For LLaMA 3.3 70B (free)
# OPENAI_API_KEY=sk-xxxxx           # For GPT-4o
# ANTHROPIC_API_KEY=sk-ant-xxxxx    # For Claude Sonnet
# GOOGLE_API_KEY=AIzaSyxxxxx        # For Gemini 2.0 Flash
```

### [requirements.txt](file:///c:/Users/SAIRAM%20REDDY/OneDrive/Desktop/Project2/code/requirements.txt)
```
fastapi>=0.111.0
uvicorn>=0.30.1
langchain>=0.2.10
langchain-neo4j>=0.0.12
langchain-openai>=0.1.17
neo4j>=5.23.1
pydantic>=2.8.2
python-dotenv>=1.0.1
pyyaml>=6.0
```

### [app/llm.py](file:///c:/Users/SAIRAM%20REDDY/OneDrive/Desktop/Project2/code/app/llm.py) — Multi-Provider Support
```python
import os
from langchain_openai import ChatOpenAI

def get_llm():
    # Priority: Anthropic > OpenAI > Gemini > Groq
    if os.getenv("ANTHROPIC_API_KEY"):
        return ChatOpenAI(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            base_url="https://api.anthropic.com/v1",
            temperature=0
        )
    if os.getenv("OPENAI_API_KEY"):
        return ChatOpenAI(model="gpt-4o", temperature=0)
    if os.getenv("GOOGLE_API_KEY"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    # Default: Groq
    return ChatOpenAI(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
        temperature=0
    )
```

---

## 6. API Design

### `POST /ask`

**Request:**
```json
{ "question": "Find people involved in drug crimes in area WN" }
```

**Response:**
```json
{
  "answer": "Found 3 people involved in drug crimes in the WN area: John Smith, Sarah Jones, and Mike Brown.",
  "cypher": "MATCH (p:Person)-[:PARTY_TO]->(c:Crime)...",
  "results": [
    {"p.name": "John", "p.surname": "Smith", "c.type": "Drugs", "a.areaCode": "WN"},
    ...
  ],
  "attempts": 1
}
```

### `GET /schema`
Returns the introspected schema (useful for debugging).

### `GET /health`
Checks Neo4j connection and LLM availability.

---

## 7. Frontend (FastAPI + HTML/JS)

A clean chat interface with:
- **Chat area**: Question/answer history
- **Cypher preview**: Expandable panel showing the generated query
- **Results table**: Formatted tabular results
- **Graph visualization**: Optional — using `neovis.js` or `vis.js` to render returned nodes/edges

---

## 8. Verification Plan

### Automated Tests — `scripts/test_queries.py`

Runs all 24 few-shot examples + 5 novel questions against the live pipeline:

```python
TEST_QUESTIONS = [
    # From few-shots (should work perfectly)
    ("How many crimes are recorded?", lambda r: r["results"][0]["total_crimes"] > 0),
    ("Show all crimes related to drugs", lambda r: len(r["results"]) > 0),
    ...
    # Novel questions (test generalization)
    ("List all people with phone numbers", lambda r: len(r["results"]) > 0),
    ("How many robbery crimes happened?", lambda r: r["results"][0].get("count", 0) >= 0),
]
```

### Manual Smoke Test Sequence

| # | Question | Expected Behavior |
|---|---|---|
| 1 | "How many crimes are in the database?" | Returns a count |
| 2 | "Show all drug-related crimes" | Filters by Crime.type CONTAINS 'drug' |
| 3 | "Who is party to robbery crimes?" | Person→PARTY_TO→Crime multi-hop |
| 4 | "Which officer investigated the most crimes?" | Aggregation with ORDER BY DESC LIMIT 1 |
| 5 | "Find people who know someone involved in drug crimes" | Multi-hop: Person→KNOWS→Person→PARTY_TO→Crime |
| 6 | "Find communication between phones" | Phone call pattern with CALLER + CALLED |
| 7 | "Which area has the most crimes?" | 3-hop: Crime→Location→AREA + aggregation |

### Success Criteria
- ✅ All 24 few-shot questions return non-empty, correct results
- ✅ At least 4/7 novel questions return correct results
- ✅ Failed queries trigger retry and succeed on 2nd/3rd attempt
- ✅ Average response time < 5 seconds

---

## 9. Implementation Order

| Phase | What | Time Est. |
|---|---|---|
| **Phase 1** | [config.py](file:///c:/Users/SAIRAM%20REDDY/OneDrive/Desktop/Project2/code/app/config.py), [database.py](file:///c:/Users/SAIRAM%20REDDY/OneDrive/Desktop/Project2/code/app/database.py), [llm.py](file:///c:/Users/SAIRAM%20REDDY/OneDrive/Desktop/Project2/code/app/llm.py) — foundation | 15 min |
| **Phase 2** | `schema_introspector.py` — auto-fetch schema | 30 min |
| **Phase 3** | `few_shot_examples.yaml` — write all 24 examples | Done ✅ |
| **Phase 4** | [cypher_generator.py](file:///c:/Users/SAIRAM%20REDDY/OneDrive/Desktop/Project2/code/agents/cypher_generator.py) — core LLM prompt | 30 min |
| **Phase 5** | [query_executor.py](file:///c:/Users/SAIRAM%20REDDY/OneDrive/Desktop/Project2/code/agents/query_executor.py) — execute + retry loop | 20 min |
| **Phase 6** | [answer_generator.py](file:///c:/Users/SAIRAM%20REDDY/OneDrive/Desktop/Project2/code/agents/answer_generator.py) — NL answer synthesis | 15 min |
| **Phase 7** | `pipeline.py` + `routes/query.py` + [main.py](file:///c:/Users/SAIRAM%20REDDY/OneDrive/Desktop/Project2/code/app/main.py) | 20 min |
| **Phase 8** | Frontend (chat UI) | 30 min |
| **Phase 9** | Testing + iteration | 30 min |

---

## 10. LLM Comparison for Cypher Generation

| LLM | Cypher Accuracy | Cost | Speed | Recommendation |
|---|---|---|---|---|
| **Claude Sonnet 4** | ⭐⭐⭐⭐⭐ | ~$3/1M tokens | ~2s | Best quality |
| **GPT-4o** | ⭐⭐⭐⭐⭐ | ~$2.5/1M tokens | ~1.5s | Very close second |
| **Gemini 2.0 Flash** | ⭐⭐⭐⭐ | ~$0.10/1M tokens | ~1s | Best value |
| **LLaMA 3.3 70B (Groq)** | ⭐⭐⭐ | Free | ~0.5s | Budget option |

> [!TIP]
> With 24 few-shot examples, even LLaMA 3.3 will be significantly better than the current system. But for production reliability, Gemini Flash or GPT-4o are recommended.
