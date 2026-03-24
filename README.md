# Investigraph - POLE NL-to-Cypher QA System

> A production-ready natural language to Cypher query system for crime investigation knowledge graphs.

Ask questions in plain English, get intelligent answers backed by Neo4j graph database queries.

---

## Overview

**Investigraph** is an intelligent question-answering system built for law enforcement and crime investigators. It translates natural language questions into Cypher queries, executes them against a POLE (Person, Object, Location, Event) knowledge graph in Neo4j, and returns clear, actionable answers with interactive graph visualizations.

### What is POLE?

POLE is a data model used in law enforcement for organizing investigation intelligence:
- **Person**: Individuals involved in investigations
- **Object**: Evidence items, vehicles, weapons
- **Location**: Crime scenes, addresses, geographic areas
- **Event**: Criminal incidents, phone calls, interactions

### Key Features

- **Natural Language Interface**: Ask questions like "Who is involved in drug crimes in area WN?"
- **Intelligent Query Generation**: Uses LLM with schema context and 24 curated examples
- **Self-Healing Retry Logic**: Automatically fixes syntax errors and reformulates failed queries (up to 3 attempts)
- **Multi-Provider LLM Support**: Works with Groq (LLaMA 3.3), OpenAI (GPT-4o), Anthropic (Claude), Google (Gemini)
- **Interactive Graph Visualization**: Explore relationships visually with node/edge rendering
- **Real-Time Results**: See generated Cypher queries, execution metadata, and natural language answers
- **Comprehensive Testing**: Unit tests, integration tests, manual test checklists

---

## Architecture

### System Design

```
┌─────────────────┐
│  User Question  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Frontend (React + TypeScript + Vite)   │
│  - Query input & example questions      │
│  - Results display & graph viz          │
│  - Real-time feedback                   │
└────────┬────────────────────────────────┘
         │ HTTP (POST /api/ask)
         ▼
┌─────────────────────────────────────────┐
│  Backend (FastAPI + Python)             │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  1. Cypher Generator (LLM)      │   │
│  │     - Schema introspection      │   │
│  │     - 24 few-shot examples      │   │
│  │     - Error context (on retry)  │   │
│  └──────────────┬──────────────────┘   │
│                 ▼                       │
│  ┌─────────────────────────────────┐   │
│  │  2. Query Executor              │   │
│  │     - Execute on Neo4j          │   │
│  │     - Retry on syntax error     │   │
│  │     - Retry on empty results    │   │
│  │     - Extract graph data        │   │
│  └──────────────┬──────────────────┘   │
│                 ▼                       │
│  ┌─────────────────────────────────┐   │
│  │  3. Answer Generator (LLM)      │   │
│  │     - Natural language answer   │   │
│  └─────────────────────────────────┘   │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Neo4j Database │
│  (POLE Schema)  │
└─────────────────┘
```

### Technology Stack

**Frontend:**
- React 18 with TypeScript
- Vite (build tool)
- vis-network (graph visualization)
- Modern CSS with dark/light mode support

**Backend:**
- FastAPI (Python web framework)
- LangChain (LLM orchestration)
- Neo4j Python Driver
- Pydantic (data validation)

**Database:**
- Neo4j Graph Database (POLE schema with 11 node types, 17 relationships)

**LLM Providers:**
- Groq (LLaMA 3.3 70B) - Free tier, fastest
- OpenAI (GPT-4o) - Best accuracy
- Anthropic (Claude Sonnet 4) - Best quality
- Google (Gemini 2.0 Flash) - Best value

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Neo4j Database (local or cloud)
- API key for at least one LLM provider (Groq/OpenAI/Anthropic/Google)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/investigraph.git
cd investigraph
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Neo4j and LLM credentials

# Run backend
uvicorn app.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

### 4. Verify Installation

Open `http://localhost:3000` in your browser and try an example question:
- "How many crimes are recorded?"
- "Find people involved in drug crimes"
- "Which area has the most crimes?"

---

## Setup Instructions

### Backend Configuration

Create `backend/.env`:

```env
# Neo4j Connection
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=pole

# LLM Provider (choose at least one)
GROQ_API_KEY=gsk_xxxxx              # Groq (free tier)
# OPENAI_API_KEY=sk-xxxxx           # OpenAI (paid)
# ANTHROPIC_API_KEY=sk-ant-xxxxx    # Anthropic (paid)
# GOOGLE_API_KEY=AIzaSyxxxxx        # Google (paid)

# Optional
LOG_LEVEL=INFO
```

### Neo4j Database Setup

Your Neo4j database should have the POLE schema:

**Node Labels (11):**
- Person, Crime, Location, Vehicle, Object, Officer, Phone, PhoneCall, Email, PostCode, AREA

**Relationships (17):**
- PARTY_TO, CURRENT_ADDRESS, HAS_PHONE, HAS_EMAIL, KNOWS, KNOWS_LW, KNOWS_PHONE, FAMILY_REL
- OCCURRED_AT, INVESTIGATED_BY, INVOLVED_IN, CALLER, CALLED, HAS_POSTCODE, LOCATION_IN_AREA, POSTCODE_IN_AREA

See `implementation_plan.md` for complete schema details.

### LLM Provider Setup

**Groq (Recommended for Development):**
1. Sign up at https://console.groq.com/
2. Get free API key (generous rate limits)
3. Add to `.env`: `GROQ_API_KEY=gsk_xxxxx`

**OpenAI:**
1. Sign up at https://platform.openai.com/
2. Add payment method
3. Add to `.env`: `OPENAI_API_KEY=sk-xxxxx`

**Anthropic:**
1. Sign up at https://console.anthropic.com/
2. Add payment method
3. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-xxxxx`

**Google Gemini:**
1. Get API key from https://ai.google.dev/
2. Add to `.env`: `GOOGLE_API_KEY=AIzaSyxxxxx`

---

## Usage Examples

### Example Questions

**Basic Queries:**
```
- "How many crimes are recorded?"
- "What are the different types of crimes?"
- "Show all crimes related to drugs"
```

**Relationship Queries:**
```
- "Who are the people involved in crimes?"
- "Which vehicles are linked to crimes?"
- "Where do crimes occur?"
```

**Multi-Hop Queries:**
```
- "Find people involved in crimes in each area"
- "Find people involved in drug crimes in area WN"
- "Find vehicles used in crimes in specific areas"
```

**Network Queries:**
```
- "Find people who know criminals"
- "Find family members of people involved in crimes"
- "Find phone numbers of people involved in crimes"
```

**Aggregation Queries:**
```
- "Which area has the highest number of crimes?"
- "Which officer investigates the most crimes?"
- "Average duration of phone calls"
```

### Using the API Directly

```bash
# Submit a question
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How many crimes are recorded?"}'

# Check health
curl http://localhost:8000/api/health

# View schema
curl http://localhost:8000/api/schema

# View examples
curl http://localhost:8000/api/examples
```

---

## Features in Detail

### 1. Intelligent Cypher Generation

The system uses an LLM with:
- **Full schema context**: All 11 node types and 17 relationships
- **24 curated examples**: Covering basic, relationship, multi-hop, and aggregation queries
- **Property value lists**: Known categorical values (crime types, officer ranks, etc.)

This provides context for accurate query generation without requiring narrow intent parsing.

### 2. Self-Healing Retry Logic

When a query fails, the system:
1. **On Syntax Error**: Feeds the error back to the LLM with the failed query for self-correction
2. **On Empty Results**: Asks the LLM to relax filters or try alternate traversal paths
3. **Max 3 Attempts**: Returns gracefully with helpful message if all retries fail

### 3. Graph Visualization

Results include structured graph data (nodes and edges) that the frontend renders interactively:
- Color-coded nodes by type (Person, Crime, Location, etc.)
- Interactive zoom, pan, and selection
- Relationship labels on edges
- Node property inspection on click

### 4. Natural Language Answers

The system generates human-readable answers:
- "Found 42 crimes in the database"
- "The area with the highest crime rate is WN with 45 incidents"
- "John Smith and Sarah Jones are involved in drug crimes in area WN"

---

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run integration tests
pytest tests/test_integration.py -v

# Run with coverage
pytest tests/ --cov=app --cov=core --cov-report=html
```

### Manual Testing

See `backend/tests/manual_test_checklist.md` for comprehensive manual test scenarios (55+ tests).

### Test Coverage

- Unit tests for each component (schema introspector, cypher generator, query executor, etc.)
- Integration tests for full pipeline with mocked Neo4j and LLM
- Manual test checklist covering:
  - Basic queries, relationships, multi-hop, aggregations
  - Error handling and retry logic
  - UI/UX verification
  - Cross-browser compatibility
  - Performance testing

---

## Deployment

See `DEPLOYMENT.md` for detailed deployment instructions including:
- Docker containerization
- Cloud platform deployment (Heroku, Render, Railway, Vercel)
- Environment configuration
- Production best practices

### Quick Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up -d

# Access application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

---

## Project Structure

```
investigraph/
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── main.py              # API entry point
│   │   ├── config.py            # Environment config
│   │   ├── database.py          # Neo4j connection
│   │   ├── llm.py               # LLM provider factory
│   │   └── models.py            # Pydantic models
│   ├── core/
│   │   ├── schema_introspector.py   # Schema auto-detection
│   │   ├── few_shot_loader.py       # Load examples
│   │   ├── cypher_generator.py      # LLM query generation
│   │   ├── query_executor.py        # Execute with retry
│   │   ├── answer_generator.py      # NL answer generation
│   │   ├── pipeline.py              # Pipeline orchestration
│   │   └── few_shot_examples.yaml   # 24 curated examples
│   ├── tests/
│   │   ├── test_*.py                # Unit tests
│   │   ├── test_integration.py      # Integration tests
│   │   └── manual_test_checklist.md # Manual test scenarios
│   ├── .env                     # Environment variables
│   ├── requirements.txt         # Python dependencies
│   └── README.md                # Backend docs
│
├── frontend/                    # React frontend
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── services/            # API client
│   │   ├── App.tsx              # Main component
│   │   └── main.tsx             # Entry point
│   ├── package.json             # Node dependencies
│   ├── vite.config.ts           # Vite configuration
│   └── README.md                # Frontend docs
│
├── docker-compose.yml           # Docker orchestration
├── Dockerfile                   # Backend Docker image
├── .dockerignore                # Docker ignore patterns
├── DEPLOYMENT.md                # Deployment guide
├── implementation_plan.md       # Technical specification
└── README.md                    # This file
```

---

## Configuration

### Backend Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NEO4J_URI` | Yes | Neo4j connection URI |
| `NEO4J_USERNAME` | Yes | Neo4j username |
| `NEO4J_PASSWORD` | Yes | Neo4j password |
| `NEO4J_DATABASE` | No | Database name (default: neo4j) |
| `GROQ_API_KEY` | No* | Groq API key |
| `OPENAI_API_KEY` | No* | OpenAI API key |
| `ANTHROPIC_API_KEY` | No* | Anthropic API key |
| `GOOGLE_API_KEY` | No* | Google API key |
| `LOG_LEVEL` | No | Logging level (default: INFO) |

*At least one LLM API key is required

### Frontend Configuration

Edit `frontend/src/services/api.ts` to change API base URL (default: `/api`).

Edit `frontend/vite.config.ts` to change backend proxy target (default: `http://localhost:8000`).

---

## Performance

### Response Times

Typical response times (on successful first attempt):
- Simple count query: < 1 second
- Relationship query: 1-2 seconds
- Multi-hop query: 2-3 seconds
- Complex aggregation: 3-5 seconds

### Optimization

- Schema cached at startup (not per-request)
- Neo4j connection pooling
- Groq for fastest responses (< 500ms LLM calls)
- Claude/GPT-4o for highest accuracy

### Scaling

For production:
- Use gunicorn with multiple workers
- Enable Redis caching for frequent queries
- Add rate limiting with slowapi
- Use managed Neo4j cluster for HA

---

## Troubleshooting

### "Neo4j connection failed"
- Verify `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` in `.env`
- Check database is online and accessible
- Test connection: `curl http://localhost:8000/api/health`

### "No LLM provider configured"
- Add at least one API key to `.env` (GROQ_API_KEY, OPENAI_API_KEY, etc.)
- Verify API key is valid: check provider dashboard
- Restart backend after updating `.env`

### "Empty results" on valid questions
- Check Neo4j has data: `MATCH (n) RETURN count(n)`
- Verify schema matches POLE structure
- Check logs for Cypher syntax errors
- Try simpler questions first

### Frontend "Connection refused"
- Ensure backend is running on port 8000
- Check CORS configuration in `app/main.py`
- Verify proxy settings in `vite.config.ts`

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Write tests for new features
4. Follow existing code style and structure
5. Update documentation
6. Run full test suite: `pytest tests/ -v`
7. Submit pull request

---

## License

MIT License - see LICENSE file for details.

---

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Neo4j](https://neo4j.com/) - Graph database platform
- [LangChain](https://www.langchain.com/) - LLM orchestration framework
- [React](https://react.dev/) - Frontend library
- [vis-network](https://visjs.org/) - Graph visualization library

---

## Support

- Documentation: See `backend/README.md` and `frontend/README.md`
- Issues: Open a GitHub issue
- Manual Testing: See `backend/tests/manual_test_checklist.md`

---

## Roadmap

Future enhancements:
- [ ] Voice input for questions
- [ ] Export results to PDF/CSV
- [ ] Save and share queries
- [ ] Query history and favorites
- [ ] Advanced graph analytics
- [ ] Real-time collaboration
- [ ] Custom dashboards
- [ ] Role-based access control
