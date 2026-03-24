# POLE NL-to-Cypher QA System - Backend

FastAPI backend for natural language to Cypher query generation.

## Setup

1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. Run server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

## API Endpoints

- `POST /api/ask` - Submit natural language question
- `GET /api/health` - Health check
- `GET /api/schema` - View introspected Neo4j schema
- `GET /api/examples` - View few-shot examples

## Testing

```bash
pytest tests/ -v
```
