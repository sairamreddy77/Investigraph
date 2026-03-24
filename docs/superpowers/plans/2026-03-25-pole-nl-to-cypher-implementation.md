# POLE Neo4j NL-to-Cypher QA System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a natural language to Cypher QA system for crime investigation analysts with React frontend, FastAPI backend, and LLaMA 3.3 70B via Groq.

**Architecture:** 3-step pipeline (Cypher Generator → Query Executor with Retry → Answer Generator) using direct generation approach with 24 few-shot examples.

**Tech Stack:** React 18 + Vite, FastAPI, Neo4j (existing), Groq (LLaMA 3.3 70B), vis-network, pytest

---

## File Structure Overview

### Backend (`backend/`)
```
backend/
├── app/
│   ├── main.py                    # FastAPI app, CORS, startup hooks
│   ├── config.py                  # Environment config loader
│   ├── database.py                # Neo4j connection singleton
│   ├── llm.py                     # Groq client wrapper
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py              # API endpoints
│   └── models/
│       ├── __init__.py
│       └── schemas.py             # Pydantic models
├── core/
│   ├── __init__.py
│   ├── schema_introspector.py     # Fetch & cache Neo4j schema
│   ├── few_shot_loader.py         # Load YAML examples
│   ├── cypher_generator.py        # LLM Cypher generation
│   ├── query_executor.py          # Execute with retry loop
│   ├── answer_generator.py        # NL answer synthesis
│   └── pipeline.py                # 3-step orchestrator
├── data/
│   └── few_shot_examples.yaml     # 24 Q→Cypher pairs
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # pytest fixtures
│   ├── test_config.py             # Config tests
│   ├── test_database.py           # Neo4j connection tests
│   ├── test_schema_introspector.py
│   ├── test_cypher_generator.py
│   ├── test_query_executor.py
│   ├── test_pipeline.py
│   ├── test_integration.py        # Full pipeline tests
│   └── benchmark.py               # Performance benchmarks
├── .env.example                   # Template for .env
├── .gitignore
├── requirements.txt
└── README.md
```

### Frontend (`frontend/`)
```
frontend/
├── src/
│   ├── main.jsx                   # React entry
│   ├── App.jsx                    # Main app
│   ├── components/
│   │   ├── ChatInterface.jsx      # Main container
│   │   ├── QuestionInput.jsx      # Input + submit
│   │   ├── MessageList.jsx        # Conversation history
│   │   ├── AnswerCard.jsx         # Single Q&A display
│   │   ├── CypherPanel.jsx        # Collapsible Cypher viewer
│   │   ├── ResultsTable.jsx       # Tabular display
│   │   ├── GraphVisualization.jsx # vis-network graph
│   │   └── ExportButton.jsx       # CSV export
│   ├── services/
│   │   └── api.js                 # Axios backend calls
│   ├── hooks/
│   │   └── useChat.js             # Chat state management
│   └── styles/
│       └── main.css               # Styling
├── public/
├── index.html
├── package.json
├── vite.config.js
└── .gitignore
```

---

## Phase 1: Backend Foundation

### Task 1: Project Setup & Configuration

**Files:**
- Create: `backend/.env.example`
- Create: `backend/.gitignore`
- Create: `backend/requirements.txt`
- Create: `backend/README.md`

- [ ] **Step 1: Create .env.example template**

```bash
# Create backend directory structure
mkdir -p backend/app/api backend/app/models backend/core backend/data backend/tests
touch backend/app/__init__.py backend/app/api/__init__.py backend/app/models/__init__.py backend/core/__init__.py backend/tests/__init__.py
```

```env
# backend/.env.example
# Neo4j Configuration
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=pole

# Groq API
GROQ_API_KEY=gsk_your_api_key_here

# Server Config
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:5173

# Logging
LOG_LEVEL=INFO
LOG_QUERIES=true
```

- [ ] **Step 2: Create .gitignore**

```gitignore
# backend/.gitignore
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.env
.venv
venv/
ENV/
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.DS_Store
```

- [ ] **Step 3: Create requirements.txt**

```txt
# backend/requirements.txt
fastapi==0.111.0
uvicorn[standard]==0.30.1
neo4j==5.23.1
pydantic==2.8.2
pydantic-settings==2.3.4
python-dotenv==1.0.1
pyyaml==6.0
groq==0.9.0
pytest==8.2.0
pytest-mock==3.14.0
pytest-asyncio==0.23.7
httpx==0.27.0
```

- [ ] **Step 4: Create README.md**

```markdown
# backend/README.md
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
```

- [ ] **Step 5: Install dependencies**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Expected: All packages install successfully

- [ ] **Step 6: Create .env from template**

```bash
cp .env.example .env
# Manually edit .env with actual credentials
```

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat: initialize backend project structure

- Add requirements.txt with FastAPI, Neo4j, Groq dependencies
- Add .env.example template for configuration
- Add .gitignore for Python projects
- Add README with setup instructions

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 2: Configuration Module

**Files:**
- Create: `backend/app/config.py`
- Test: `backend/tests/test_config.py`

- [ ] **Step 1: Write failing test for config loading**

```python
# backend/tests/test_config.py
import pytest
from pydantic import ValidationError


def test_config_loads_from_env(monkeypatch):
    """Test that config loads environment variables correctly"""
    monkeypatch.setenv("NEO4J_URI", "neo4j://localhost:7687")
    monkeypatch.setenv("NEO4J_USERNAME", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "password")
    monkeypatch.setenv("NEO4J_DATABASE", "pole")
    monkeypatch.setenv("GROQ_API_KEY", "test_key")

    from app.config import get_settings

    settings = get_settings()
    assert settings.NEO4J_URI == "neo4j://localhost:7687"
    assert settings.NEO4J_USERNAME == "neo4j"
    assert settings.NEO4J_PASSWORD == "password"
    assert settings.NEO4J_DATABASE == "pole"
    assert settings.GROQ_API_KEY == "test_key"


def test_config_validates_required_fields():
    """Test that missing required fields raise validation error"""
    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings()  # Missing required fields
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_config.py -v
```

Expected: FAIL - "ModuleNotFoundError: No module named 'app.config'"

- [ ] **Step 3: Implement config module**

```python
# backend/app/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Neo4j Configuration
    NEO4J_URI: str
    NEO4J_USERNAME: str
    NEO4J_PASSWORD: str
    NEO4J_DATABASE: str = "pole"

    # Groq API
    GROQ_API_KEY: str

    # Server Config
    BACKEND_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_QUERIES: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_config.py -v
```

Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/tests/test_config.py
git commit -m "feat: add configuration module with Pydantic settings

- Load config from .env with validation
- Cache settings with lru_cache
- Add tests for config loading and validation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 3: Neo4j Database Connection

**Files:**
- Create: `backend/app/database.py`
- Test: `backend/tests/test_database.py`
- Test: `backend/tests/conftest.py`

- [ ] **Step 1: Create pytest fixtures**

```python
# backend/tests/conftest.py
import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver for testing"""
    driver = Mock()
    session = MagicMock()
    driver.session.return_value.__enter__.return_value = session
    driver.session.return_value.__exit__.return_value = None
    return driver


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing"""
    monkeypatch.setenv("NEO4J_URI", "neo4j://localhost:7687")
    monkeypatch.setenv("NEO4J_USERNAME", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "password")
    monkeypatch.setenv("NEO4J_DATABASE", "pole")
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
```

- [ ] **Step 2: Write failing test for database connection**

```python
# backend/tests/test_database.py
import pytest
from unittest.mock import Mock, patch


def test_neo4j_client_connects(mock_settings):
    """Test Neo4j client establishes connection"""
    with patch('app.database.GraphDatabase') as mock_graphdb:
        mock_driver = Mock()
        mock_graphdb.driver.return_value = mock_driver

        from app.database import Neo4jClient

        client = Neo4jClient()
        client.connect()

        mock_graphdb.driver.assert_called_once()
        assert client.driver is not None


def test_neo4j_client_query_executes(mock_settings, mock_neo4j_driver):
    """Test query execution returns results"""
    with patch('app.database.GraphDatabase') as mock_graphdb:
        mock_graphdb.driver.return_value = mock_neo4j_driver

        # Mock query result
        mock_result = Mock()
        mock_result.data.return_value = [{"name": "John", "age": 30}]
        mock_neo4j_driver.session.return_value.__enter__.return_value.run.return_value = mock_result

        from app.database import Neo4jClient

        client = Neo4jClient()
        client.connect()
        results = client.query("MATCH (n) RETURN n LIMIT 1")

        assert len(results) == 1
        assert results[0]["name"] == "John"


def test_neo4j_client_closes_connection(mock_settings, mock_neo4j_driver):
    """Test client closes connection properly"""
    with patch('app.database.GraphDatabase') as mock_graphdb:
        mock_graphdb.driver.return_value = mock_neo4j_driver

        from app.database import Neo4jClient

        client = Neo4jClient()
        client.connect()
        client.close()

        mock_neo4j_driver.close.assert_called_once()
```

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest tests/test_database.py -v
```

Expected: FAIL - "ModuleNotFoundError: No module named 'app.database'"

- [ ] **Step 4: Implement database module**

```python
# backend/app/database.py
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Singleton Neo4j database client"""

    _instance: Optional['Neo4jClient'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.driver = None
            cls._instance.settings = get_settings()
        return cls._instance

    def connect(self) -> None:
        """Establish connection to Neo4j database"""
        if self.driver is not None:
            return

        try:
            self.driver = GraphDatabase.driver(
                self.settings.NEO4J_URI,
                auth=(self.settings.NEO4J_USERNAME, self.settings.NEO4J_PASSWORD)
            )
            # Test connection
            self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.settings.NEO4J_URI}")
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def query(self, cypher: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute Cypher query and return results

        Args:
            cypher: Cypher query string
            parameters: Query parameters (optional)

        Returns:
            List of result records as dictionaries
        """
        if self.driver is None:
            raise RuntimeError("Neo4j client not connected. Call connect() first.")

        if parameters is None:
            parameters = {}

        with self.driver.session(database=self.settings.NEO4J_DATABASE) as session:
            result = session.run(cypher, parameters)
            return result.data()

    def close(self) -> None:
        """Close Neo4j connection"""
        if self.driver is not None:
            self.driver.close()
            self.driver = None
            logger.info("Neo4j connection closed")


# Global singleton instance
_neo4j_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """Get or create Neo4j client singleton"""
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
        _neo4j_client.connect()
    return _neo4j_client
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_database.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/app/database.py backend/tests/test_database.py backend/tests/conftest.py
git commit -m "feat: add Neo4j database client with singleton pattern

- Implement Neo4jClient with connect, query, close methods
- Add connection verification and error handling
- Create pytest fixtures for mocking
- Add tests for connection, querying, and closing

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 4: Groq LLM Client

**Files:**
- Create: `backend/app/llm.py`
- Test: `backend/tests/test_llm.py`

- [ ] **Step 1: Write failing test for LLM client**

```python
# backend/tests/test_llm.py
import pytest
from unittest.mock import Mock, patch


def test_groq_client_initializes(mock_settings):
    """Test Groq client initializes with API key"""
    with patch('app.llm.Groq') as mock_groq:
        from app.llm import get_groq_client

        client = get_groq_client()

        mock_groq.assert_called_once_with(api_key="test_key")


def test_groq_client_generates_response(mock_settings):
    """Test Groq client generates LLM response"""
    with patch('app.llm.Groq') as mock_groq:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Generated Cypher query"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client

        from app.llm import generate_completion

        result = generate_completion(
            system_prompt="You are a Cypher generator",
            user_prompt="Generate query",
            temperature=0
        )

        assert result == "Generated Cypher query"
        mock_client.chat.completions.create.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_llm.py -v
```

Expected: FAIL - "ModuleNotFoundError: No module named 'app.llm'"

- [ ] **Step 3: Implement LLM client module**

```python
# backend/app/llm.py
from typing import Optional
from groq import Groq
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)


class GroqClient:
    """Groq LLM client wrapper"""

    def __init__(self):
        settings = get_settings()
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0
    ) -> str:
        """
        Generate chat completion using Groq LLaMA 3.3 70B

        Args:
            system_prompt: System instructions
            user_prompt: User query
            temperature: Sampling temperature (0 for deterministic)

        Returns:
            Generated text completion
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=4096
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise


# Global client instance
_groq_client: Optional[GroqClient] = None


def get_groq_client() -> GroqClient:
    """Get or create Groq client singleton"""
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client


def generate_completion(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0
) -> str:
    """
    Convenience function for generating completions

    Args:
        system_prompt: System instructions
        user_prompt: User query
        temperature: Sampling temperature

    Returns:
        Generated text
    """
    client = get_groq_client()
    return client.chat_completion(system_prompt, user_prompt, temperature)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_llm.py -v
```

Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/llm.py backend/tests/test_llm.py
git commit -m "feat: add Groq LLM client wrapper

- Implement GroqClient with chat completion method
- Use LLaMA 3.3 70B model via Groq API
- Add convenience function for generating completions
- Add tests for client initialization and response generation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 5: Schema Introspector

**Files:**
- Create: `backend/core/schema_introspector.py`
- Test: `backend/tests/test_schema_introspector.py`

- [ ] **Step 1: Write failing test for schema introspection**

```python
# backend/tests/test_schema_introspector.py
import pytest
from unittest.mock import Mock, patch


def test_schema_introspector_fetches_node_labels(mock_settings, mock_neo4j_driver):
    """Test introspector fetches node labels and properties"""
    with patch('core.schema_introspector.get_neo4j_client') as mock_get_client:
        mock_client = Mock()
        mock_client.query.return_value = [
            {"labels": ["Person"], "properties": ["name", "surname", "age"]},
            {"labels": ["Crime"], "properties": ["type", "date", "last_outcome"]}
        ]
        mock_get_client.return_value = mock_client

        from core.schema_introspector import SchemaIntrospector

        introspector = SchemaIntrospector()
        schema = introspector.introspect()

        assert "Person" in schema
        assert "Crime" in schema
        assert "name" in schema


def test_schema_introspector_fetches_relationships(mock_settings, mock_neo4j_driver):
    """Test introspector fetches relationship types"""
    with patch('core.schema_introspector.get_neo4j_client') as mock_get_client:
        mock_client = Mock()
        mock_client.query.side_effect = [
            [{"labels": ["Person"], "properties": ["name"]}],  # Nodes
            [{"type": "PARTY_TO", "start": "Person", "end": "Crime"}]  # Relationships
        ]
        mock_get_client.return_value = mock_client

        from core.schema_introspector import SchemaIntrospector

        introspector = SchemaIntrospector()
        schema = introspector.introspect()

        assert "PARTY_TO" in schema
        assert "(Person)-[:PARTY_TO]->(Crime)" in schema


def test_schema_introspector_caches_result(mock_settings):
    """Test introspector caches schema after first fetch"""
    with patch('core.schema_introspector.get_neo4j_client') as mock_get_client:
        mock_client = Mock()
        mock_client.query.return_value = [{"labels": ["Person"], "properties": ["name"]}]
        mock_get_client.return_value = mock_client

        from core.schema_introspector import SchemaIntrospector

        introspector = SchemaIntrospector()
        schema1 = introspector.introspect()
        schema2 = introspector.introspect()

        # Should only query once (cached)
        assert mock_client.query.call_count == 1
        assert schema1 == schema2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_schema_introspector.py -v
```

Expected: FAIL - "ModuleNotFoundError: No module named 'core.schema_introspector'"

- [ ] **Step 3: Implement schema introspector (part 1: basic structure)**

```python
# backend/core/schema_introspector.py
from typing import Dict, List, Any, Optional
import logging

from app.database import get_neo4j_client

logger = logging.getLogger(__name__)


class SchemaIntrospector:
    """Introspects Neo4j schema and caches results"""

    def __init__(self):
        self.client = get_neo4j_client()
        self._schema_cache: Optional[str] = None

    def introspect(self) -> str:
        """
        Fetch complete schema from Neo4j and format for LLM prompt

        Returns:
            Formatted schema text with nodes, relationships, property values
        """
        if self._schema_cache is not None:
            return self._schema_cache

        logger.info("Introspecting Neo4j schema...")

        nodes = self._fetch_node_labels()
        relationships = self._fetch_relationships()
        property_values = self._fetch_property_values()

        schema_text = self._format_schema(nodes, relationships, property_values)
        self._schema_cache = schema_text

        logger.info("Schema introspection complete")
        return schema_text

    def _fetch_node_labels(self) -> Dict[str, List[str]]:
        """Fetch all node labels with their properties"""
        query = """
        CALL db.labels() YIELD label
        CALL apoc.meta.nodeTypeProperties() YIELD nodeType, propertyName
        WHERE nodeType = ':' + label
        RETURN label, collect(propertyName) AS properties
        """

        # Fallback if APOC not available
        fallback_query = """
        MATCH (n)
        WITH DISTINCT labels(n)[0] AS label, keys(n) AS props
        RETURN label, props AS properties
        LIMIT 100
        """

        try:
            results = self.client.query(query)
        except Exception:
            logger.warning("APOC not available, using fallback query")
            results = self.client.query(fallback_query)

        nodes = {}
        for record in results:
            label = record.get("label")
            properties = record.get("properties", [])
            if label and label not in ["", None]:
                nodes[label] = list(set(properties)) if properties else []

        return nodes

    def _fetch_relationships(self) -> List[Dict[str, str]]:
        """Fetch all relationship types with start/end nodes"""
        query = """
        CALL db.relationshipTypes() YIELD relationshipType
        MATCH ()-[r]-()
        WHERE type(r) = relationshipType
        WITH relationshipType,
             labels(startNode(r))[0] AS startLabel,
             labels(endNode(r))[0] AS endLabel
        RETURN DISTINCT relationshipType AS type,
               startLabel AS start,
               endLabel AS end
        LIMIT 100
        """

        results = self.client.query(query)

        relationships = []
        for record in results:
            rel_type = record.get("type")
            start = record.get("start")
            end = record.get("end")
            if all([rel_type, start, end]):
                relationships.append({
                    "type": rel_type,
                    "start": start,
                    "end": end
                })

        return relationships

    def _fetch_property_values(self) -> Dict[str, List[str]]:
        """Fetch categorical property values for filtering"""
        property_values = {}

        # Crime types
        query = "MATCH (c:Crime) RETURN DISTINCT c.type AS val ORDER BY val LIMIT 50"
        try:
            results = self.client.query(query)
            values = [r["val"] for r in results if r["val"]]
            if values:
                property_values["Crime.type"] = values
        except Exception as e:
            logger.warning(f"Failed to fetch Crime.type values: {e}")

        # Crime outcomes
        query = "MATCH (c:Crime) RETURN DISTINCT c.last_outcome AS val ORDER BY val LIMIT 50"
        try:
            results = self.client.query(query)
            values = [r["val"] for r in results if r["val"]]
            if values:
                property_values["Crime.last_outcome"] = values
        except Exception as e:
            logger.warning(f"Failed to fetch Crime.last_outcome values: {e}")

        # Officer ranks
        query = "MATCH (o:Officer) RETURN DISTINCT o.rank AS val ORDER BY val LIMIT 50"
        try:
            results = self.client.query(query)
            values = [r["val"] for r in results if r["val"]]
            if values:
                property_values["Officer.rank"] = values
        except Exception as e:
            logger.warning(f"Failed to fetch Officer.rank values: {e}")

        # Vehicle makes
        query = "MATCH (v:Vehicle) RETURN DISTINCT v.make AS val ORDER BY val LIMIT 50"
        try:
            results = self.client.query(query)
            values = [r["val"] for r in results if r["val"]]
            if values:
                property_values["Vehicle.make"] = values
        except Exception as e:
            logger.warning(f"Failed to fetch Vehicle.make values: {e}")

        return property_values

    def _format_schema(
        self,
        nodes: Dict[str, List[str]],
        relationships: List[Dict[str, str]],
        property_values: Dict[str, List[str]]
    ) -> str:
        """Format schema into text for LLM prompt"""
        lines = []

        # Nodes section
        lines.append("NODES:")
        for label, properties in sorted(nodes.items()):
            props_str = ", ".join([f"{p}: string" for p in properties])
            lines.append(f"  {label}({props_str})")
        lines.append("")

        # Relationships section
        lines.append("RELATIONSHIPS:")
        for rel in relationships:
            lines.append(f"  ({rel['start']})-[:{rel['type']}]->({rel['end']})")
        lines.append("")

        # Property values section
        lines.append("PROPERTY VALUES:")
        for prop, values in sorted(property_values.items()):
            values_str = ", ".join([f'"{v}"' for v in values[:20]])  # Limit to 20
            lines.append(f"  {prop}: [{values_str}]")
        lines.append("")

        # Data limitations section
        lines.append("DATA LIMITATIONS:")
        lines.append("  • Person.age: Not available (field is empty)")
        lines.append("  • Crime.note and Crime.charge: Rarely populated (99% empty)")
        lines.append("  • PARTY_TO relationships: Sparse (only 55 records for 28,762 crimes)")
        lines.append("  • Object data: Minimal (7 records)")

        return "\n".join(lines)


# Global singleton
_schema_introspector: Optional[SchemaIntrospector] = None


def get_schema_introspector() -> SchemaIntrospector:
    """Get or create schema introspector singleton"""
    global _schema_introspector
    if _schema_introspector is None:
        _schema_introspector = SchemaIntrospector()
    return _schema_introspector
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_schema_introspector.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/core/schema_introspector.py backend/tests/test_schema_introspector.py
git commit -m "feat: add schema introspector for Neo4j

- Fetch node labels, relationships, property values
- Cache schema result for performance
- Format schema as text for LLM prompts
- Include data limitation warnings
- Add fallback queries when APOC unavailable
- Add tests for introspection and caching

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 2: Few-Shot Examples

### Task 6: Few-Shot Examples YAML

**Files:**
- Create: `backend/data/few_shot_examples.yaml`
- Create: `backend/core/few_shot_loader.py`
- Test: `backend/tests/test_few_shot_loader.py`

- [ ] **Step 1: Create few-shot examples YAML (24 examples)**

```yaml
# backend/data/few_shot_examples.yaml
examples:
  # ── CRIME BASICS ────────────────────────────────────
  - question: "How many crimes are recorded?"
    cypher: |
      MATCH (c:Crime)
      RETURN count(c) AS total_crimes

  - question: "What are the different types of crimes?"
    cypher: |
      MATCH (c:Crime)
      RETURN DISTINCT c.type AS crime_type
      ORDER BY crime_type

  - question: "Show all crimes related to drugs"
    cypher: |
      MATCH (c:Crime)
      WHERE toLower(c.type) CONTAINS 'drug'
      RETURN c.id, c.type, c.date, c.last_outcome
      LIMIT 50

  - question: "Find crimes where no suspect was identified"
    cypher: |
      MATCH (c:Crime)
      WHERE toLower(c.last_outcome) CONTAINS 'no suspect'
      RETURN c.id, c.type, c.date, c.last_outcome
      LIMIT 50

  # ── INVESTIGATION QUERIES ───────────────────────────
  - question: "Which officers investigated drug crimes?"
    cypher: |
      MATCH (o:Officer)<-[:INVESTIGATED_BY]-(c:Crime)
      WHERE toLower(c.type) CONTAINS 'drug'
      RETURN o.name, o.surname, o.rank, count(c) AS cases
      ORDER BY cases DESC

  - question: "Which officer investigated the most crimes?"
    cypher: |
      MATCH (o:Officer)<-[:INVESTIGATED_BY]-(c:Crime)
      RETURN o.name, o.surname, o.rank, count(c) AS total_cases
      ORDER BY total_cases DESC
      LIMIT 1

  - question: "Show all officers and their crime types"
    cypher: |
      MATCH (o:Officer)<-[:INVESTIGATED_BY]-(c:Crime)
      RETURN o.name, o.surname, o.rank, c.type
      LIMIT 100

  # ── GEOGRAPHIC ANALYSIS ─────────────────────────────
  - question: "Where do crimes occur?"
    cypher: |
      MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
      RETURN c.type, l.address, l.postcode
      LIMIT 50

  - question: "Which area has the most crimes?"
    cypher: |
      MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
            -[:LOCATION_IN_AREA]->(a:AREA)
      RETURN a.areaCode, count(c) AS crime_count
      ORDER BY crime_count DESC
      LIMIT 1

  - question: "How many crimes occurred in area WN?"
    cypher: |
      MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
            -[:LOCATION_IN_AREA]->(a:AREA)
      WHERE toLower(a.areaCode) CONTAINS 'wn'
      RETURN count(c) AS crime_count

  # ── SOCIAL NETWORKS ─────────────────────────────────
  - question: "Find people who know criminals"
    cypher: |
      MATCH (p1:Person)-[:KNOWS]->(p2:Person)-[:PARTY_TO]->(c:Crime)
      RETURN p1.name, p1.surname, p2.name AS criminal_name, c.type
      LIMIT 50

  - question: "Find family members of people involved in crimes"
    cypher: |
      MATCH (p1:Person)-[r:FAMILY_REL]->(p2:Person)
            -[:PARTY_TO]->(c:Crime)
      RETURN p1.name, p1.surname, p2.name AS relative_name,
             r.rel_type AS relationship, c.type
      LIMIT 50

  # ── COMMUNICATION PATTERNS ──────────────────────────
  - question: "Find phone calls made by phones"
    cypher: |
      MATCH (pc:PhoneCall)-[:CALLER]->(ph:Phone)
      RETURN ph.phoneNo, pc.call_time, pc.call_duration, pc.call_type
      LIMIT 50

  - question: "Find communication between two phones"
    cypher: |
      MATCH (pc:PhoneCall)-[:CALLER]->(ph1:Phone)
      MATCH (pc)-[:CALLED]->(ph2:Phone)
      RETURN ph1.phoneNo AS caller, ph2.phoneNo AS receiver,
             pc.call_time, pc.call_duration
      LIMIT 50

  - question: "Find phones of people involved in crimes"
    cypher: |
      MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
      MATCH (p)-[:HAS_PHONE]->(ph:Phone)
      RETURN p.name, p.surname, ph.phoneNo, c.type
      LIMIT 50

  # ── VEHICLES ────────────────────────────────────────
  - question: "Which vehicles are linked to crimes?"
    cypher: |
      MATCH (v:Vehicle)-[:INVOLVED_IN]->(c:Crime)
      RETURN v.make, v.model, v.reg, c.type
      LIMIT 50

  - question: "Find vehicles used in robbery crimes"
    cypher: |
      MATCH (v:Vehicle)-[:INVOLVED_IN]->(c:Crime)
      WHERE toLower(c.type) CONTAINS 'robber'
      RETURN v.make, v.model, v.reg, c.type, c.date
      LIMIT 50

  # ── MULTI-HOP QUERIES ───────────────────────────────
  - question: "Find people involved in crimes in each area"
    cypher: |
      MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
            -[:OCCURRED_AT]->(l:Location)
            -[:LOCATION_IN_AREA]->(a:AREA)
      RETURN p.name, p.surname, c.type, a.areaCode
      LIMIT 50

  - question: "Find people involved in drug crimes in area WN"
    cypher: |
      MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
            -[:OCCURRED_AT]->(l:Location)
            -[:LOCATION_IN_AREA]->(a:AREA)
      WHERE toLower(c.type) CONTAINS 'drug'
        AND toLower(a.areaCode) CONTAINS 'wn'
      RETURN p.name, p.surname, c.type, a.areaCode
      LIMIT 50

  - question: "Find vehicles used in crimes in specific areas"
    cypher: |
      MATCH (v:Vehicle)-[:INVOLVED_IN]->(c:Crime)
            -[:OCCURRED_AT]->(l:Location)
            -[:LOCATION_IN_AREA]->(a:AREA)
      RETURN v.make, v.model, a.areaCode, c.type
      LIMIT 50

  - question: "Find officers investigating drug crimes"
    cypher: |
      MATCH (c:Crime)-[:INVESTIGATED_BY]->(o:Officer)
      WHERE toLower(c.type) CONTAINS 'drug'
      RETURN o.name, o.surname, o.rank, count(c) AS case_count
      ORDER BY case_count DESC

  # ── AGGREGATIONS ────────────────────────────────────
  - question: "Count crimes by type"
    cypher: |
      MATCH (c:Crime)
      RETURN c.type, count(c) AS count
      ORDER BY count DESC

  - question: "Average duration of phone calls"
    cypher: |
      MATCH (pc:PhoneCall)
      WHERE pc.call_duration IS NOT NULL
      RETURN avg(toFloat(pc.call_duration)) AS avg_duration

  - question: "Count crimes by area"
    cypher: |
      MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
            -[:LOCATION_IN_AREA]->(a:AREA)
      RETURN a.areaCode, count(c) AS crime_count
      ORDER BY crime_count DESC
```

- [ ] **Step 2: Write failing test for few-shot loader**

```python
# backend/tests/test_few_shot_loader.py
import pytest
from pathlib import Path


def test_few_shot_loader_loads_yaml():
    """Test few-shot loader reads YAML file"""
    from core.few_shot_loader import FewShotLoader

    loader = FewShotLoader()
    examples = loader.load()

    assert len(examples) > 0
    assert "question" in examples[0]
    assert "cypher" in examples[0]


def test_few_shot_loader_has_24_examples():
    """Test loader returns exactly 24 examples"""
    from core.few_shot_loader import FewShotLoader

    loader = FewShotLoader()
    examples = loader.load()

    assert len(examples) == 24


def test_few_shot_loader_formats_examples():
    """Test loader formats examples for LLM prompt"""
    from core.few_shot_loader import FewShotLoader

    loader = FewShotLoader()
    formatted = loader.format_for_prompt()

    assert "Question:" in formatted
    assert "Cypher:" in formatted
    assert "How many crimes" in formatted


def test_few_shot_loader_caches_result():
    """Test loader caches examples after first load"""
    from core.few_shot_loader import FewShotLoader

    loader = FewShotLoader()
    examples1 = loader.load()
    examples2 = loader.load()

    assert examples1 is examples2  # Same object reference (cached)
```

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest tests/test_few_shot_loader.py -v
```

Expected: FAIL - "ModuleNotFoundError: No module named 'core.few_shot_loader'"

- [ ] **Step 4: Implement few-shot loader**

```python
# backend/core/few_shot_loader.py
from typing import List, Dict, Optional
from pathlib import Path
import yaml
import logging

logger = logging.getLogger(__name__)


class FewShotLoader:
    """Loads and formats few-shot examples from YAML"""

    def __init__(self, examples_path: Optional[Path] = None):
        if examples_path is None:
            # Default path relative to this file
            self.examples_path = Path(__file__).parent.parent / "data" / "few_shot_examples.yaml"
        else:
            self.examples_path = examples_path

        self._examples_cache: Optional[List[Dict[str, str]]] = None

    def load(self) -> List[Dict[str, str]]:
        """
        Load few-shot examples from YAML file

        Returns:
            List of example dictionaries with 'question' and 'cypher' keys
        """
        if self._examples_cache is not None:
            return self._examples_cache

        logger.info(f"Loading few-shot examples from {self.examples_path}")

        try:
            with open(self.examples_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            examples = data.get("examples", [])

            if not examples:
                logger.warning("No examples found in YAML file")
                return []

            self._examples_cache = examples
            logger.info(f"Loaded {len(examples)} few-shot examples")

            return examples

        except FileNotFoundError:
            logger.error(f"Few-shot examples file not found: {self.examples_path}")
            return []
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML: {e}")
            return []

    def format_for_prompt(self) -> str:
        """
        Format examples as text for LLM prompt

        Returns:
            Formatted string with all examples
        """
        examples = self.load()

        lines = []
        for i, example in enumerate(examples, 1):
            question = example.get("question", "")
            cypher = example.get("cypher", "").strip()

            lines.append(f"Example {i}:")
            lines.append(f"Question: {question}")
            lines.append(f"Cypher:")
            lines.append(f"```")
            lines.append(cypher)
            lines.append(f"```")
            lines.append("")

        return "\n".join(lines)


# Global singleton
_few_shot_loader: Optional[FewShotLoader] = None


def get_few_shot_loader() -> FewShotLoader:
    """Get or create few-shot loader singleton"""
    global _few_shot_loader
    if _few_shot_loader is None:
        _few_shot_loader = FewShotLoader()
    return _few_shot_loader
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_few_shot_loader.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/data/few_shot_examples.yaml backend/core/few_shot_loader.py backend/tests/test_few_shot_loader.py
git commit -m "feat: add 24 few-shot examples for Cypher generation

- Create YAML file with curated question-Cypher pairs
- Examples cover crime basics, investigations, geography, social networks
- Implement FewShotLoader with caching and prompt formatting
- Add tests for loading, formatting, and caching

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 3: Core Pipeline Components

### Task 7: Cypher Generator

**Files:**
- Create: `backend/core/cypher_generator.py`
- Test: `backend/tests/test_cypher_generator.py`

- [ ] **Step 1: Write failing test for Cypher generator**

```python
# backend/tests/test_cypher_generator.py
import pytest
from unittest.mock import Mock, patch


def test_cypher_generator_builds_prompt(mock_settings):
    """Test generator builds complete prompt with schema and examples"""
    with patch('core.cypher_generator.get_groq_client'):
        with patch('core.cypher_generator.get_schema_introspector') as mock_schema:
            with patch('core.cypher_generator.get_few_shot_loader') as mock_loader:
                mock_schema.return_value.introspect.return_value = "NODES: Person, Crime"
                mock_loader.return_value.format_for_prompt.return_value = "Example 1: ..."

                from core.cypher_generator import CypherGenerator

                generator = CypherGenerator()
                prompt = generator._build_system_prompt("")

                assert "NODES: Person, Crime" in prompt
                assert "Example 1: ..." in prompt
                assert "RULES" in prompt


def test_cypher_generator_generates_cypher(mock_settings):
    """Test generator calls LLM and returns Cypher"""
    with patch('core.cypher_generator.get_groq_client') as mock_groq:
        with patch('core.cypher_generator.get_schema_introspector') as mock_schema:
            with patch('core.cypher_generator.get_few_shot_loader') as mock_loader:
                mock_schema.return_value.introspect.return_value = "NODES: Crime"
                mock_loader.return_value.format_for_prompt.return_value = "Examples"

                mock_client = Mock()
                mock_client.chat_completion.return_value = "MATCH (c:Crime) RETURN count(c)"
                mock_groq.return_value = mock_client

                from core.cypher_generator import CypherGenerator

                generator = CypherGenerator()
                cypher = generator.generate("How many crimes?")

                assert "MATCH (c:Crime)" in cypher
                assert "RETURN count(c)" in cypher
                mock_client.chat_completion.assert_called_once()


def test_cypher_generator_includes_error_context_on_retry(mock_settings):
    """Test generator includes error context when retrying"""
    with patch('core.cypher_generator.get_groq_client') as mock_groq:
        with patch('core.cypher_generator.get_schema_introspector') as mock_schema:
            with patch('core.cypher_generator.get_few_shot_loader') as mock_loader:
                mock_schema.return_value.introspect.return_value = "NODES: Crime"
                mock_loader.return_value.format_for_prompt.return_value = "Examples"
                mock_client = Mock()
                mock_groq.return_value = mock_client

                from core.cypher_generator import CypherGenerator

                generator = CypherGenerator()
                error_context = "Previous query failed with: Invalid syntax"
                generator.generate("How many crimes?", error_context=error_context)

                call_args = mock_client.chat_completion.call_args
                system_prompt = call_args[0][0]

                assert "Invalid syntax" in system_prompt
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_cypher_generator.py -v
```

Expected: FAIL - "ModuleNotFoundError: No module named 'core.cypher_generator'"

- [ ] **Step 3: Implement Cypher generator**

```python
# backend/core/cypher_generator.py
from typing import Optional
import logging

from app.llm import get_groq_client
from core.schema_introspector import get_schema_introspector
from core.few_shot_loader import get_few_shot_loader

logger = logging.getLogger(__name__)


class CypherGenerator:
    """Generates Cypher queries using LLM with schema and examples"""

    def __init__(self):
        self.llm_client = get_groq_client()
        self.schema_introspector = get_schema_introspector()
        self.few_shot_loader = get_few_shot_loader()

    def generate(self, question: str, error_context: str = "") -> str:
        """
        Generate Cypher query for natural language question

        Args:
            question: Natural language question
            error_context: Error context from previous attempt (for retry)

        Returns:
            Generated Cypher query string
        """
        logger.info(f"Generating Cypher for: {question}")

        system_prompt = self._build_system_prompt(error_context)
        user_prompt = f"Generate a Cypher query for: {question}"

        cypher = self.llm_client.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0
        )

        # Clean up response (remove markdown fences if present)
        cypher = self._clean_cypher(cypher)

        logger.info(f"Generated Cypher: {cypher[:100]}...")
        return cypher

    def _build_system_prompt(self, error_context: str) -> str:
        """Build complete system prompt with schema, examples, and rules"""
        schema_text = self.schema_introspector.introspect()
        few_shot_text = self.few_shot_loader.format_for_prompt()

        prompt = f"""You are an expert Neo4j Cypher query generator for a POLE (Person, Object,
Location, Event) crime investigation knowledge graph.

═══ GRAPH SCHEMA ═══
{schema_text}

═══ EXAMPLE QUERIES ═══
{few_shot_text}

═══ RULES ═══
1. Use ONLY the node labels, relationships, and properties from the schema
2. Follow relationship directions EXACTLY as shown
3. For string filtering: toLower(n.prop) CONTAINS 'value'
4. Use exact property values from schema when possible
5. Return ONLY the Cypher query - no explanations, no markdown fences
6. NEVER generate MERGE, DELETE, SET, CREATE, DROP, REMOVE
7. For "who" questions → target Person nodes
8. For count/most/least → use count(), ORDER BY, LIMIT
9. Use CONTAINS for partial matching when unsure of exact values
10. Always include meaningful RETURN aliases
"""

        if error_context:
            prompt += f"\n\n═══ ERROR CONTEXT ═══\n{error_context}\n"

        return prompt

    def _clean_cypher(self, cypher: str) -> str:
        """Remove markdown fences and extra whitespace from generated Cypher"""
        # Remove markdown code fences
        cypher = cypher.replace("```cypher", "").replace("```", "")

        # Remove leading/trailing whitespace
        cypher = cypher.strip()

        return cypher


# Global singleton
_cypher_generator: Optional[CypherGenerator] = None


def get_cypher_generator() -> CypherGenerator:
    """Get or create Cypher generator singleton"""
    global _cypher_generator
    if _cypher_generator is None:
        _cypher_generator = CypherGenerator()
    return _cypher_generator
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_cypher_generator.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/core/cypher_generator.py backend/tests/test_cypher_generator.py
git commit -m "feat: add Cypher generator with LLM integration

- Build comprehensive prompt with schema and examples
- Generate Cypher using Groq LLaMA 3.3 70B
- Support error context for retry attempts
- Clean markdown fences from LLM responses
- Add tests for prompt building and generation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 8: Query Executor with Retry

**Files:**
- Create: `backend/core/query_executor.py`
- Test: `backend/tests/test_query_executor.py`

- [ ] **Step 1: Write failing test for query executor**

```python
# backend/tests/test_query_executor.py
import pytest
from unittest.mock import Mock, patch
from neo4j.exceptions import CypherSyntaxError


def test_query_executor_executes_successful_query(mock_settings, mock_neo4j_driver):
    """Test executor runs query and returns results"""
    with patch('core.query_executor.get_neo4j_client') as mock_get_client:
        with patch('core.query_executor.get_cypher_generator'):
            mock_client = Mock()
            mock_client.query.return_value = [{"count": 100}]
            mock_get_client.return_value = mock_client

            from core.query_executor import QueryExecutor

            executor = QueryExecutor()
            result = executor.execute("MATCH (c:Crime) RETURN count(c)", "How many crimes?")

            assert result["results"] == [{"count": 100}]
            assert result["attempts"] == 1
            assert "error" not in result


def test_query_executor_retries_on_syntax_error(mock_settings):
    """Test executor retries when syntax error occurs"""
    with patch('core.query_executor.get_neo4j_client') as mock_get_client:
        with patch('core.query_executor.get_cypher_generator') as mock_gen:
            mock_client = Mock()
            # First call fails, second succeeds
            mock_client.query.side_effect = [
                CypherSyntaxError("Invalid syntax"),
                [{"count": 100}]
            ]
            mock_get_client.return_value = mock_client

            mock_generator = Mock()
            mock_generator.generate.return_value = "MATCH (c:Crime) RETURN count(c)"
            mock_gen.return_value = mock_generator

            from core.query_executor import QueryExecutor

            executor = QueryExecutor()
            result = executor.execute("BAD QUERY", "How many crimes?")

            assert result["attempts"] == 2
            assert result["results"] == [{"count": 100}]
            mock_generator.generate.assert_called_once()  # Regenerate once


def test_query_executor_reformulates_on_empty_results(mock_settings):
    """Test executor reformulates query when results are empty"""
    with patch('core.query_executor.get_neo4j_client') as mock_get_client:
        with patch('core.query_executor.get_cypher_generator') as mock_gen:
            mock_client = Mock()
            # First call empty, second has results
            mock_client.query.side_effect = [
                [],  # Empty
                [{"count": 50}]
            ]
            mock_get_client.return_value = mock_client

            mock_generator = Mock()
            mock_generator.generate.return_value = "MATCH (c:Crime) RETURN count(c)"
            mock_gen.return_value = mock_generator

            from core.query_executor import QueryExecutor

            executor = QueryExecutor()
            result = executor.execute("MATCH (c:Crime) WHERE c.type='X' RETURN count(c)", "How many crimes?")

            assert result["attempts"] == 2
            assert result["results"] == [{"count": 50}]


def test_query_executor_fails_after_max_retries(mock_settings):
    """Test executor returns error after max retries"""
    with patch('core.query_executor.get_neo4j_client') as mock_get_client:
        with patch('core.query_executor.get_cypher_generator') as mock_gen:
            mock_client = Mock()
            mock_client.query.side_effect = CypherSyntaxError("Invalid")
            mock_get_client.return_value = mock_client

            mock_generator = Mock()
            mock_generator.generate.return_value = "BAD QUERY"
            mock_gen.return_value = mock_generator

            from core.query_executor import QueryExecutor

            executor = QueryExecutor()
            result = executor.execute("BAD QUERY", "How many crimes?")

            assert result["attempts"] == 3
            assert "error" in result
            assert len(result["results"]) == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_query_executor.py -v
```

Expected: FAIL - "ModuleNotFoundError: No module named 'core.query_executor'"

- [ ] **Step 3: Implement query executor (continued in next step due to length)**

```python
# backend/core/query_executor.py
from typing import Dict, List, Any
import logging
from neo4j.exceptions import CypherSyntaxError, ClientError

from app.database import get_neo4j_client
from core.cypher_generator import get_cypher_generator

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


class QueryExecutor:
    """Executes Cypher queries with retry logic"""

    def __init__(self):
        self.neo4j_client = get_neo4j_client()
        self.cypher_generator = get_cypher_generator()

    def execute(self, cypher: str, question: str) -> Dict[str, Any]:
        """
        Execute Cypher query with retry on errors

        Args:
            cypher: Initial Cypher query
            question: Original user question (for retry context)

        Returns:
            Dict with results, cypher, attempts, and optional error
        """
        for attempt in range(1, MAX_RETRIES + 1):
            logger.info(f"Attempt {attempt}/{MAX_RETRIES}: Executing query")

            try:
                # Execute query
                results = self.neo4j_client.query(cypher)

                # Success with results
                if results:
                    logger.info(f"Query succeeded with {len(results)} results")
                    return {
                        "results": results,
                        "cypher": cypher,
                        "attempts": attempt,
                        "graph_data": self._extract_graph_data(results)
                    }

                # Empty results - reformulate if retries left
                if attempt < MAX_RETRIES:
                    logger.warning("Query returned 0 results, reformulating...")
                    error_context = self._build_empty_results_context(cypher)
                    cypher = self.cypher_generator.generate(question, error_context)
                else:
                    logger.warning("No results after max retries")
                    return {
                        "results": [],
                        "cypher": cypher,
                        "attempts": attempt,
                        "error": "No results found after 3 attempts",
                        "graph_data": {"nodes": [], "edges": []}
                    }

            except (CypherSyntaxError, ClientError) as e:
                # Syntax/client error - self-correct if retries left
                logger.error(f"Query error: {e}")

                if attempt < MAX_RETRIES:
                    error_context = self._build_syntax_error_context(cypher, str(e))
                    cypher = self.cypher_generator.generate(question, error_context)
                else:
                    return {
                        "results": [],
                        "cypher": cypher,
                        "attempts": attempt,
                        "error": f"Syntax error: {str(e)}",
                        "graph_data": {"nodes": [], "edges": []}
                    }

            except Exception as e:
                # Other errors (connection, etc) - non-retryable
                logger.error(f"Execution error: {e}")
                return {
                    "results": [],
                    "cypher": cypher,
                    "attempts": attempt,
                    "error": f"Execution error: {str(e)}",
                    "graph_data": {"nodes": [], "edges": []}
                }

        # Should never reach here
        return {
            "results": [],
            "cypher": cypher,
            "attempts": MAX_RETRIES,
            "error": "Max retries exceeded",
            "graph_data": {"nodes": [], "edges": []}
        }

    def _build_empty_results_context(self, cypher: str) -> str:
        """Build error context for empty results"""
        return f"""Previous query returned 0 results:
{cypher}

Suggestions:
- Try relaxing WHERE filters (remove date constraints, age filters)
- Use CONTAINS instead of exact matches
- Check relationship direction matches schema
- Verify property names match schema exactly
- Consider that PARTY_TO relationships are sparse (only 55 records)
"""

    def _build_syntax_error_context(self, cypher: str, error: str) -> str:
        """Build error context for syntax errors"""
        return f"""Previous query failed with syntax error:
Error: {error}
Failed Query:
{cypher}

Please fix the syntax error and generate a corrected query.
Common issues:
- Invalid node labels or relationship types
- Incorrect Cypher syntax
- Missing or extra parentheses/brackets
"""

    def _extract_graph_data(self, results: List[Dict[str, Any]]) -> Dict[str, List]:
        """
        Extract nodes and edges from results for graph visualization

        Args:
            results: Query results

        Returns:
            Dict with 'nodes' and 'edges' lists
        """
        nodes = []
        edges = []
        seen_nodes = set()

        for record in results:
            for key, value in record.items():
                # Check if value is a node
                if isinstance(value, dict) and "labels" in str(type(value)):
                    node_id = value.get("id", value.get("elementId", key))
                    if node_id not in seen_nodes:
                        nodes.append({
                            "id": str(node_id),
                            "label": value.get("labels", ["Unknown"])[0] if "labels" in str(type(value)) else "Node",
                            "properties": {k: v for k, v in value.items() if k not in ["id", "elementId"]}
                        })
                        seen_nodes.add(node_id)

        # Note: Edge extraction requires relationship objects in results
        # This is a simplified version - full implementation would parse relationships

        return {
            "nodes": nodes[:100],  # Limit to 100 nodes for performance
            "edges": edges[:100]
        }


# Global singleton
_query_executor: Optional['QueryExecutor'] = None


def get_query_executor() -> QueryExecutor:
    """Get or create query executor singleton"""
    global _query_executor
    if _query_executor is None:
        _query_executor = QueryExecutor()
    return _query_executor
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_query_executor.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/core/query_executor.py backend/tests/test_query_executor.py
git commit -m "feat: add query executor with retry logic

- Execute Cypher queries on Neo4j
- Retry up to 3 times on syntax errors or empty results
- Regenerate query with error context on failures
- Extract graph data for visualization
- Add tests for successful execution, retries, and failures

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

---

### Task 9: Answer Generator

**Files:**
- Create: `backend/core/answer_generator.py`
- Test: `backend/tests/test_answer_generator.py`

- [ ] **Step 1: Write failing test for answer generator**

```python
# backend/tests/test_answer_generator.py
import pytest
from unittest.mock import Mock, patch


def test_answer_generator_synthesizes_answer(mock_settings):
    """Test generator creates natural language answer"""
    with patch('core.answer_generator.get_groq_client') as mock_groq:
        mock_client = Mock()
        mock_client.chat_completion.return_value = "Found 100 crimes in the database."
        mock_groq.return_value = mock_client

        from core.answer_generator import AnswerGenerator

        generator = AnswerGenerator()
        answer = generator.generate(
            question="How many crimes?",
            cypher="MATCH (c:Crime) RETURN count(c)",
            results=[{"count": 100}]
        )

        assert "100" in answer
        assert "crimes" in answer
        mock_client.chat_completion.assert_called_once()


def test_answer_generator_handles_empty_results(mock_settings):
    """Test generator provides helpful message for empty results"""
    with patch('core.answer_generator.get_groq_client') as mock_groq:
        mock_client = Mock()
        mock_client.chat_completion.return_value = "No records found matching criteria."
        mock_groq.return_value = mock_client

        from core.answer_generator import AnswerGenerator

        generator = AnswerGenerator()
        answer = generator.generate(
            question="Find crimes by Batman",
            cypher="MATCH (c:Crime) WHERE c.type='Batman' RETURN c",
            results=[]
        )

        assert "no" in answer.lower() or "not found" in answer.lower()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_answer_generator.py -v
```

Expected: FAIL - "ModuleNotFoundError: No module named 'core.answer_generator'"

- [ ] **Step 3: Implement answer generator**

```python
# backend/core/answer_generator.py
from typing import List, Dict, Any, Optional
import json
import logging

from app.llm import get_groq_client

logger = logging.getLogger(__name__)


class AnswerGenerator:
    """Generates natural language answers from query results"""

    def __init__(self):
        self.llm_client = get_groq_client()

    def generate(
        self,
        question: str,
        cypher: str,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Generate natural language answer from query results

        Args:
            question: Original user question
            cypher: Executed Cypher query
            results: Query results

        Returns:
            Natural language answer for analysts
        """
        logger.info("Generating natural language answer")

        system_prompt = self._build_system_prompt(question, cypher, results)
        user_prompt = "Provide a clear answer to the analyst's question based on the results."

        answer = self.llm_client.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0
        )

        logger.info("Answer generated successfully")
        return answer

    def _build_system_prompt(
        self,
        question: str,
        cypher: str,
        results: List[Dict[str, Any]]
    ) -> str:
        """Build system prompt with question, query, and results"""
        results_str = self._format_results(results)

        prompt = f"""You are a crime investigation analyst interpreting database query results.

Question: {question}
Cypher Query Used: {cypher}
Results ({len(results)} records):
{results_str}

Instructions:
- Provide a clear, direct answer to the analyst's question
- If results are empty, say so professionally: "No records found matching criteria"
- Format multiple results as numbered lists or summary statistics
- Mention relevant details (counts, key names, patterns)
- Do NOT mention Cypher, databases, or technical details
- Be concise - analysts need quick insights
- If data limitations affected results, mention it briefly (e.g., "Note: Person age data not available")
"""
        return prompt

    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format results for prompt (limit to first 50 records)"""
        if not results:
            return "No results returned"

        # Limit to first 50 records to avoid token limits
        limited_results = results[:50]

        try:
            return json.dumps(limited_results, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to format results as JSON: {e}")
            return str(limited_results)


# Global singleton
_answer_generator: Optional[AnswerGenerator] = None


def get_answer_generator() -> AnswerGenerator:
    """Get or create answer generator singleton"""
    global _answer_generator
    if _answer_generator is None:
        _answer_generator = AnswerGenerator()
    return _answer_generator
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_answer_generator.py -v
```

Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/core/answer_generator.py backend/tests/test_answer_generator.py
git commit -m "feat: add answer generator for NL synthesis

- Generate natural language answers from query results
- Format results for analyst-friendly presentation
- Handle empty results gracefully
- Add tests for answer generation and empty results

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 10: Pipeline Orchestrator

**Files:**
- Create: `backend/core/pipeline.py`
- Test: `backend/tests/test_pipeline.py`

- [ ] **Step 1: Write failing test for pipeline**

```python
# backend/tests/test_pipeline.py
import pytest
from unittest.mock import Mock, patch
import time


def test_pipeline_orchestrates_full_flow(mock_settings):
    """Test pipeline runs all 3 steps and returns complete response"""
    with patch('core.pipeline.get_cypher_generator') as mock_gen:
        with patch('core.pipeline.get_query_executor') as mock_exec:
            with patch('core.pipeline.get_answer_generator') as mock_ans:
                # Mock Cypher generator
                mock_generator = Mock()
                mock_generator.generate.return_value = "MATCH (c:Crime) RETURN count(c)"
                mock_gen.return_value = mock_generator

                # Mock query executor
                mock_executor = Mock()
                mock_executor.execute.return_value = {
                    "results": [{"count": 100}],
                    "cypher": "MATCH (c:Crime) RETURN count(c)",
                    "attempts": 1,
                    "graph_data": {"nodes": [], "edges": []}
                }
                mock_exec.return_value = mock_executor

                # Mock answer generator
                mock_answer_gen = Mock()
                mock_answer_gen.generate.return_value = "Found 100 crimes."
                mock_ans.return_value = mock_answer_gen

                from core.pipeline import Pipeline

                pipeline = Pipeline()
                response = pipeline.run("How many crimes?")

                assert response["question"] == "How many crimes?"
                assert response["answer"] == "Found 100 crimes."
                assert response["cypher"] == "MATCH (c:Crime) RETURN count(c)"
                assert response["results"] == [{"count": 100}]
                assert response["attempts"] == 1
                assert "execution_time_ms" in response


def test_pipeline_initialization_caches_schema_and_examples(mock_settings):
    """Test pipeline initializes schema and examples at startup"""
    with patch('core.pipeline.get_schema_introspector') as mock_schema:
        with patch('core.pipeline.get_few_shot_loader') as mock_loader:
            mock_introspector = Mock()
            mock_introspector.introspect.return_value = "NODES: Crime"
            mock_schema.return_value = mock_introspector

            mock_few_shot = Mock()
            mock_few_shot.load.return_value = [{"question": "test", "cypher": "test"}]
            mock_loader.return_value = mock_few_shot

            from core.pipeline import Pipeline

            pipeline = Pipeline()
            pipeline.initialize()

            mock_introspector.introspect.assert_called_once()
            mock_few_shot.load.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_pipeline.py -v
```

Expected: FAIL - "ModuleNotFoundError: No module named 'core.pipeline'"

- [ ] **Step 3: Implement pipeline orchestrator**

```python
# backend/core/pipeline.py
from typing import Dict, Any
import time
import logging

from core.cypher_generator import get_cypher_generator
from core.query_executor import get_query_executor
from core.answer_generator import get_answer_generator
from core.schema_introspector import get_schema_introspector
from core.few_shot_loader import get_few_shot_loader

logger = logging.getLogger(__name__)


class Pipeline:
    """Orchestrates 3-step NL-to-Cypher pipeline"""

    def __init__(self):
        self.cypher_generator = get_cypher_generator()
        self.query_executor = get_query_executor()
        self.answer_generator = get_answer_generator()
        self.schema_introspector = get_schema_introspector()
        self.few_shot_loader = get_few_shot_loader()
        self._initialized = False

    def initialize(self) -> None:
        """
        Initialize pipeline by caching schema and examples
        Should be called once at application startup
        """
        if self._initialized:
            return

        logger.info("Initializing pipeline...")

        # Trigger schema introspection (cached)
        self.schema_introspector.introspect()

        # Load few-shot examples (cached)
        self.few_shot_loader.load()

        self._initialized = True
        logger.info("Pipeline initialization complete")

    def run(self, question: str) -> Dict[str, Any]:
        """
        Run complete NL-to-Cypher pipeline

        Args:
            question: Natural language question

        Returns:
            Dict with answer, cypher, results, and metadata
        """
        start_time = time.time()

        logger.info(f"Running pipeline for question: {question}")

        try:
            # Step 1: Generate Cypher
            cypher = self.cypher_generator.generate(question)

            # Step 2: Execute with retry
            execution_result = self.query_executor.execute(cypher, question)

            # Step 3: Generate answer
            if execution_result.get("error"):
                # Query failed - use error as answer
                answer = f"Unable to process query: {execution_result['error']}"
            else:
                answer = self.answer_generator.generate(
                    question=question,
                    cypher=execution_result["cypher"],
                    results=execution_result["results"]
                )

            # Build response
            elapsed_ms = int((time.time() - start_time) * 1000)

            response = {
                "question": question,
                "answer": answer,
                "cypher": execution_result["cypher"],
                "results": execution_result["results"],
                "graph_data": execution_result.get("graph_data", {"nodes": [], "edges": []}),
                "attempts": execution_result["attempts"],
                "execution_time_ms": elapsed_ms
            }

            if execution_result.get("error"):
                response["error"] = execution_result["error"]

            logger.info(f"Pipeline completed in {elapsed_ms}ms")
            return response

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "question": question,
                "answer": f"An error occurred: {str(e)}",
                "cypher": "",
                "results": [],
                "graph_data": {"nodes": [], "edges": []},
                "attempts": 1,
                "execution_time_ms": elapsed_ms,
                "error": str(e)
            }


# Global singleton
_pipeline = None


def get_pipeline() -> Pipeline:
    """Get or create pipeline singleton"""
    global _pipeline
    if _pipeline is None:
        _pipeline = Pipeline()
    return _pipeline
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_pipeline.py -v
```

Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/core/pipeline.py backend/tests/test_pipeline.py
git commit -m "feat: add 3-step pipeline orchestrator

- Orchestrate Cypher generation, execution, and answer synthesis
- Initialize schema and examples at startup
- Track execution time and attempts
- Handle errors gracefully with fallback messages
- Add tests for full pipeline flow and initialization

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 4: FastAPI Application

### Task 11: Pydantic Models

**Files:**
- Create: `backend/app/models/schemas.py`

- [ ] **Step 1: Create Pydantic request/response models**

```python
# backend/app/models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class QuestionRequest(BaseModel):
    """Request model for /api/ask endpoint"""
    question: str = Field(..., min_length=1, max_length=500, description="Natural language question")


class GraphData(BaseModel):
    """Graph visualization data"""
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)


class QueryResponse(BaseModel):
    """Response model for /api/ask endpoint"""
    question: str
    answer: str
    cypher: str
    results: List[Dict[str, Any]]
    graph_data: GraphData
    attempts: int
    execution_time_ms: int
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for /api/health endpoint"""
    status: str
    neo4j_connected: bool
    groq_configured: bool
    schema_loaded: bool


class SchemaResponse(BaseModel):
    """Response model for /api/schema endpoint"""
    schema: str


class ExampleItem(BaseModel):
    """Single few-shot example"""
    question: str
    cypher: str


class ExamplesResponse(BaseModel):
    """Response model for /api/examples endpoint"""
    examples: List[ExampleItem]
    count: int
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/models/schemas.py
git commit -m "feat: add Pydantic models for API

- Define request/response models for all endpoints
- Add validation for question length
- Include graph data structure for visualization
- Add health check and examples response models

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 12: FastAPI Routes

**Files:**
- Create: `backend/app/api/routes.py`

- [ ] **Step 1: Implement API routes**

```python
# backend/app/api/routes.py
from fastapi import APIRouter, HTTPException
import logging

from app.models.schemas import (
    QuestionRequest,
    QueryResponse,
    HealthResponse,
    SchemaResponse,
    ExamplesResponse,
    ExampleItem,
    GraphData
)
from core.pipeline import get_pipeline
from core.schema_introspector import get_schema_introspector
from core.few_shot_loader import get_few_shot_loader
from app.database import get_neo4j_client
from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ask", response_model=QueryResponse)
async def ask_question(request: QuestionRequest):
    """
    Process natural language question and return answer with Cypher query

    Args:
        request: Question request with natural language query

    Returns:
        Query response with answer, Cypher, results, and metadata
    """
    try:
        pipeline = get_pipeline()
        result = pipeline.run(request.question)

        return QueryResponse(
            question=result["question"],
            answer=result["answer"],
            cypher=result["cypher"],
            results=result["results"],
            graph_data=GraphData(**result["graph_data"]),
            attempts=result["attempts"],
            execution_time_ms=result["execution_time_ms"],
            error=result.get("error")
        )

    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check system health - Neo4j connection, Groq config, schema loaded

    Returns:
        Health status response
    """
    neo4j_connected = False
    groq_configured = False
    schema_loaded = False

    # Check Neo4j
    try:
        client = get_neo4j_client()
        client.query("RETURN 1")
        neo4j_connected = True
    except Exception as e:
        logger.warning(f"Neo4j health check failed: {e}")

    # Check Groq
    try:
        settings = get_settings()
        groq_configured = bool(settings.GROQ_API_KEY)
    except Exception as e:
        logger.warning(f"Groq config check failed: {e}")

    # Check schema
    try:
        introspector = get_schema_introspector()
        schema = introspector.introspect()
        schema_loaded = len(schema) > 0
    except Exception as e:
        logger.warning(f"Schema check failed: {e}")

    status = "healthy" if all([neo4j_connected, groq_configured, schema_loaded]) else "degraded"

    return HealthResponse(
        status=status,
        neo4j_connected=neo4j_connected,
        groq_configured=groq_configured,
        schema_loaded=schema_loaded
    )


@router.get("/schema", response_model=SchemaResponse)
async def get_schema():
    """
    Get introspected Neo4j schema

    Returns:
        Schema text with nodes, relationships, property values
    """
    try:
        introspector = get_schema_introspector()
        schema = introspector.introspect()

        return SchemaResponse(schema=schema)

    except Exception as e:
        logger.error(f"Error fetching schema: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/examples", response_model=ExamplesResponse)
async def get_examples():
    """
    Get all few-shot examples

    Returns:
        List of question-Cypher example pairs
    """
    try:
        loader = get_few_shot_loader()
        examples = loader.load()

        return ExamplesResponse(
            examples=[ExampleItem(**ex) for ex in examples],
            count=len(examples)
        )

    except Exception as e:
        logger.error(f"Error fetching examples: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/api/routes.py
git commit -m "feat: add FastAPI routes for all endpoints

- POST /api/ask - process NL questions
- GET /api/health - system health check
- GET /api/schema - return introspected schema
- GET /api/examples - return few-shot examples
- Add error handling and logging

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 13: Main FastAPI Application

**Files:**
- Create: `backend/app/main.py`

- [ ] **Step 1: Create FastAPI app with startup hooks**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys

from app.config import get_settings
from app.api.routes import router
from core.pipeline import get_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="POLE NL-to-Cypher QA System",
    description="Natural language to Cypher query system for crime investigation",
    version="1.0.0"
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Initialize pipeline on startup"""
    logger.info("Starting POLE NL-to-Cypher QA System...")

    try:
        # Initialize pipeline (caches schema and examples)
        pipeline = get_pipeline()
        pipeline.initialize()

        logger.info("Application startup complete")

    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down application...")

    try:
        from app.database import get_neo4j_client
        client = get_neo4j_client()
        client.close()

        logger.info("Application shutdown complete")

    except Exception as e:
        logger.warning(f"Shutdown cleanup warning: {e}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "POLE NL-to-Cypher QA System",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.BACKEND_PORT)
```

- [ ] **Step 2: Test the application starts**

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Expected: Server starts, visit http://localhost:8000/docs to see API documentation

- [ ] **Step 3: Test health endpoint**

```bash
curl http://localhost:8000/api/health
```

Expected: JSON response with health status

- [ ] **Step 4: Stop server and commit**

```bash
# Stop server (Ctrl+C)
git add backend/app/main.py
git commit -m "feat: add FastAPI main application

- Configure FastAPI with CORS middleware
- Add startup hook to initialize pipeline
- Add shutdown hook to close Neo4j connection
- Include API routes with /api prefix
- Add logging configuration

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 5: React Frontend

### Task 14: Frontend Project Setup

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/.gitignore`

- [ ] **Step 1: Initialize React project with Vite**

```bash
cd ..
npm create vite@latest frontend -- --template react
cd frontend
```

- [ ] **Step 2: Install dependencies**

```bash
npm install
npm install axios vis-network
```

- [ ] **Step 3: Update vite.config.js for proxy**

```javascript
// frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

- [ ] **Step 4: Create .gitignore**

```gitignore
# frontend/.gitignore
node_modules
dist
.DS_Store
*.local
```

- [ ] **Step 5: Commit frontend setup**

```bash
git add frontend/
git commit -m "feat: initialize React frontend with Vite

- Set up Vite React project
- Install axios and vis-network dependencies
- Configure proxy to backend API
- Add .gitignore for frontend

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 15: API Service

**Files:**
- Create: `frontend/src/services/api.js`

- [ ] **Step 1: Create API service with axios**

```javascript
// frontend/src/services/api.js
import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const askQuestion = async (question) => {
  try {
    const response = await api.post('/ask', { question });
    return response.data;
  } catch (error) {
    console.error('API error:', error);
    throw error;
  }
};

export const getHealth = async () => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    console.error('Health check error:', error);
    throw error;
  }
};

export const getSchema = async () => {
  try {
    const response = await api.get('/schema');
    return response.data;
  } catch (error) {
    console.error('Schema fetch error:', error);
    throw error;
  }
};

export const getExamples = async () => {
  try {
    const response = await api.get('/examples');
    return response.data;
  } catch (error) {
    console.error('Examples fetch error:', error);
    throw error;
  }
};

export default api;
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/services/api.js
git commit -m "feat: add API service with axios

- Create axios client with base URL
- Add askQuestion, getHealth, getSchema, getExamples functions
- Add error handling for API calls

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 16: Chat Hook

**Files:**
- Create: `frontend/src/hooks/useChat.js`

- [ ] **Step 1: Create chat state management hook**

```javascript
// frontend/src/hooks/useChat.js
import { useState, useCallback } from 'react';
import { askQuestion } from '../services/api';

export const useChat = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const sendQuestion = useCallback(async (question) => {
    if (!question.trim()) return;

    setIsLoading(true);
    setError(null);

    // Add user message immediately
    const userMessage = {
      id: Date.now(),
      type: 'question',
      content: question,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);

    try {
      // Call API
      const response = await askQuestion(question);

      // Add response message
      const responseMessage = {
        id: Date.now() + 1,
        type: 'answer',
        content: response.answer,
        cypher: response.cypher,
        results: response.results,
        graphData: response.graph_data,
        attempts: response.attempts,
        executionTime: response.execution_time_ms,
        error: response.error,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, responseMessage]);

    } catch (err) {
      setError(err.message || 'Failed to get response');

      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'Unable to connect to server. Please try again.',
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendQuestion,
    clearChat
  };
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/useChat.js
git commit -m "feat: add useChat hook for state management

- Manage message history and loading state
- Handle question sending and response receipt
- Add clear chat functionality
- Format messages with metadata (cypher, results, etc)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 17: Core Components (Part 1)

**Files:**
- Create: `frontend/src/components/QuestionInput.jsx`
- Create: `frontend/src/components/AnswerCard.jsx`

- [ ] **Step 1: Create QuestionInput component**

```jsx
// frontend/src/components/QuestionInput.jsx
import { useState } from 'react';

export const QuestionInput = ({ onSend, isLoading }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSend(input);
      setInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="question-input-form">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Type your question here..."
        disabled={isLoading}
        className="question-input"
      />
      <button
        type="submit"
        disabled={isLoading || !input.trim()}
        className="ask-button"
      >
        {isLoading ? 'Processing...' : 'Ask'}
      </button>
    </form>
  );
};
```

- [ ] **Step 2: Create AnswerCard component**

```jsx
// frontend/src/components/AnswerCard.jsx
import { useState } from 'react';
import { CypherPanel } from './CypherPanel';
import { ResultsTable } from './ResultsTable';
import { ExportButton } from './ExportButton';

export const AnswerCard = ({ message }) => {
  const [showCypher, setShowCypher] = useState(false);
  const [showTable, setShowTable] = useState(false);

  if (message.type === 'question') {
    return (
      <div className="message question-message">
        <div className="message-header">
          <strong>Q:</strong>
          <span className="timestamp">{new Date(message.timestamp).toLocaleTimeString()}</span>
        </div>
        <div className="message-content">{message.content}</div>
      </div>
    );
  }

  if (message.type === 'error') {
    return (
      <div className="message error-message">
        <div className="message-header">
          <strong>Error:</strong>
        </div>
        <div className="message-content">{message.content}</div>
      </div>
    );
  }

  // Answer message
  return (
    <div className="message answer-message">
      <div className="message-header">
        <strong>A:</strong>
        <span className="metadata">
          Attempt {message.attempts} | {message.executionTime}ms
        </span>
      </div>

      <div className="message-content">{message.content}</div>

      {message.error && (
        <div className="error-badge">
          ⚠️ {message.error}
        </div>
      )}

      <div className="message-actions">
        <button
          onClick={() => setShowCypher(!showCypher)}
          className="action-button"
        >
          {showCypher ? '▼' : '▶'} Show Cypher
        </button>

        {message.results && message.results.length > 0 && (
          <>
            <button
              onClick={() => setShowTable(!showTable)}
              className="action-button"
            >
              📊 View Table ({message.results.length} records)
            </button>
            <ExportButton results={message.results} />
          </>
        )}
      </div>

      {showCypher && <CypherPanel cypher={message.cypher} />}
      {showTable && <ResultsTable results={message.results} />}
    </div>
  );
};
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/QuestionInput.jsx frontend/src/components/AnswerCard.jsx
git commit -m "feat: add QuestionInput and AnswerCard components

- QuestionInput with submit on Enter key
- AnswerCard displays Q&A with metadata
- Show/hide Cypher and results table
- Display execution time and attempt count

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 18: Core Components (Part 2)

**Files:**
- Create: `frontend/src/components/CypherPanel.jsx`
- Create: `frontend/src/components/ResultsTable.jsx`
- Create: `frontend/src/components/ExportButton.jsx`

- [ ] **Step 1: Create CypherPanel component**

```jsx
// frontend/src/components/CypherPanel.jsx
import { useState } from 'react';

export const CypherPanel = ({ cypher }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(cypher);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="cypher-panel">
      <div className="cypher-header">
        <span>Generated Cypher Query</span>
        <button onClick={handleCopy} className="copy-button">
          {copied ? '✓ Copied' : '📋 Copy'}
        </button>
      </div>
      <pre className="cypher-code">{cypher}</pre>
    </div>
  );
};
```

- [ ] **Step 2: Create ResultsTable component**

```jsx
// frontend/src/components/ResultsTable.jsx
import { useState, useMemo } from 'react';

export const ResultsTable = ({ results }) => {
  const [sortKey, setSortKey] = useState(null);
  const [sortOrder, setSortOrder] = useState('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 20;

  const columns = useMemo(() => {
    if (!results || results.length === 0) return [];
    return Object.keys(results[0]);
  }, [results]);

  const sortedResults = useMemo(() => {
    if (!sortKey) return results;

    return [...results].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];

      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      const comparison = aVal < bVal ? -1 : 1;
      return sortOrder === 'asc' ? comparison : -comparison;
    });
  }, [results, sortKey, sortOrder]);

  const paginatedResults = useMemo(() => {
    const startIndex = (currentPage - 1) * rowsPerPage;
    return sortedResults.slice(startIndex, startIndex + rowsPerPage);
  }, [sortedResults, currentPage]);

  const totalPages = Math.ceil(results.length / rowsPerPage);

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('asc');
    }
  };

  if (!results || results.length === 0) {
    return <div className="no-results">No results to display</div>;
  }

  return (
    <div className="results-table-container">
      <div className="table-info">
        Showing {paginatedResults.length} of {results.length} results
      </div>

      <table className="results-table">
        <thead>
          <tr>
            {columns.map(col => (
              <th key={col} onClick={() => handleSort(col)} className="sortable">
                {col}
                {sortKey === col && (sortOrder === 'asc' ? ' ▲' : ' ▼')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {paginatedResults.map((row, idx) => (
            <tr key={idx}>
              {columns.map(col => (
                <td key={col}>
                  {row[col] === null || row[col] === undefined
                    ? '-'
                    : String(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {totalPages > 1 && (
        <div className="pagination">
          <button
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
          >
            Previous
          </button>
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};
```

- [ ] **Step 3: Create ExportButton component**

```jsx
// frontend/src/components/ExportButton.jsx
export const ExportButton = ({ results }) => {
  const handleExport = () => {
    if (!results || results.length === 0) return;

    // Convert to CSV
    const headers = Object.keys(results[0]);
    const csvContent = [
      headers.join(','),
      ...results.map(row =>
        headers.map(h => {
          const val = row[h];
          // Escape commas and quotes
          if (val === null || val === undefined) return '';
          const str = String(val);
          return str.includes(',') || str.includes('"')
            ? `"${str.replace(/"/g, '""')}"`
            : str;
        }).join(',')
      )
    ].join('\n');

    // Download
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `query-results-${Date.now()}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <button onClick={handleExport} className="action-button export-button">
      💾 Export CSV
    </button>
  );
};
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/CypherPanel.jsx frontend/src/components/ResultsTable.jsx frontend/src/components/ExportButton.jsx
git commit -m "feat: add CypherPanel, ResultsTable, and ExportButton

- CypherPanel with syntax highlighting and copy button
- ResultsTable with sorting and pagination (20 rows/page)
- ExportButton for CSV download
- Handle null/undefined values gracefully

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 19: Graph Visualization & Chat Components

**Files:**
- Create: `frontend/src/components/GraphVisualization.jsx`
- Create: `frontend/src/components/MessageList.jsx`
- Create: `frontend/src/components/ChatInterface.jsx`

- [ ] **Step 1: Create GraphVisualization component**

```jsx
// frontend/src/components/GraphVisualization.jsx
import { useEffect, useRef } from 'react';
import { Network } from 'vis-network';

export const GraphVisualization = ({ graphData }) => {
  const containerRef = useRef(null);
  const networkRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !graphData) return;

    const { nodes, edges } = graphData;

    if (!nodes || nodes.length === 0) {
      return;
    }

    // Color map by node label
    const colorMap = {
      'Person': '#4A90E2',
      'Crime': '#E74C3C',
      'Location': '#2ECC71',
      'Officer': '#9B59B6',
      'Vehicle': '#F39C12',
      'Phone': '#1ABC9C',
      'AREA': '#34495E'
    };

    // Format nodes
    const visNodes = nodes.map(node => ({
      id: node.id,
      label: node.properties?.name || node.properties?.type || node.label || node.id,
      title: Object.entries(node.properties || {})
        .map(([k, v]) => `${k}: ${v}`)
        .join('\n'),
      color: colorMap[node.label] || '#95A5A6',
      shape: 'dot',
      size: 20
    }));

    // Format edges
    const visEdges = edges.map((edge, idx) => ({
      id: idx,
      from: edge.from,
      to: edge.to,
      label: edge.type || '',
      arrows: 'to'
    }));

    // Create network
    const data = {
      nodes: visNodes,
      edges: visEdges
    };

    const options = {
      nodes: {
        font: { size: 14 },
        borderWidth: 2
      },
      edges: {
        font: { size: 12, align: 'middle' },
        smooth: { type: 'continuous' }
      },
      physics: {
        stabilization: { iterations: 100 }
      },
      interaction: {
        hover: true,
        tooltipDelay: 200
      }
    };

    networkRef.current = new Network(containerRef.current, data, options);

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
      }
    };
  }, [graphData]);

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return <div className="no-graph">No graph data to visualize</div>;
  }

  return (
    <div className="graph-visualization">
      <div className="graph-header">Graph Visualization ({graphData.nodes.length} nodes)</div>
      <div ref={containerRef} className="graph-container" />
    </div>
  );
};
```

- [ ] **Step 2: Create MessageList component**

```jsx
// frontend/src/components/MessageList.jsx
import { useEffect, useRef } from 'react';
import { AnswerCard } from './AnswerCard';

export const MessageList = ({ messages }) => {
  const bottomRef = useRef(null);

  useEffect(() => {
    // Auto-scroll to bottom
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="empty-state">
        <h2>👋 Welcome to POLE Investigation QA</h2>
        <p>Ask questions about crime investigations in natural language</p>
        <div className="example-questions">
          <p>Try asking:</p>
          <ul>
            <li>"How many crimes are recorded?"</li>
            <li>"Which officers investigated drug crimes?"</li>
            <li>"Which area has the most crimes?"</li>
            <li>"Find family members of people involved in crimes"</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map(message => (
        <AnswerCard key={message.id} message={message} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
};
```

- [ ] **Step 3: Create ChatInterface component**

```jsx
// frontend/src/components/ChatInterface.jsx
import { useState } from 'react';
import { MessageList } from './MessageList';
import { QuestionInput } from './QuestionInput';
import { GraphVisualization } from './GraphVisualization';

export const ChatInterface = ({ messages, isLoading, onSendQuestion, onClearChat }) => {
  const [viewMode, setViewMode] = useState('chat'); // 'chat' or 'graph'

  // Get latest graph data from last answer message
  const latestGraphData = messages
    .slice()
    .reverse()
    .find(m => m.type === 'answer')?.graphData;

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h1>🔍 POLE Investigation QA System</h1>
        <div className="header-actions">
          <button
            onClick={() => setViewMode('chat')}
            className={`view-button ${viewMode === 'chat' ? 'active' : ''}`}
          >
            💬 Chat
          </button>
          <button
            onClick={() => setViewMode('graph')}
            className={`view-button ${viewMode === 'graph' ? 'active' : ''}`}
            disabled={!latestGraphData || latestGraphData.nodes.length === 0}
          >
            📊 Graph
          </button>
          <button onClick={onClearChat} className="clear-button">
            🗑️ Clear
          </button>
        </div>
      </div>

      <div className="chat-body">
        {viewMode === 'chat' ? (
          <MessageList messages={messages} />
        ) : (
          <GraphVisualization graphData={latestGraphData} />
        )}
      </div>

      <div className="chat-footer">
        <QuestionInput onSend={onSendQuestion} isLoading={isLoading} />
        {isLoading && <div className="loading-indicator">Processing your question...</div>}
      </div>
    </div>
  );
};
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/GraphVisualization.jsx frontend/src/components/MessageList.jsx frontend/src/components/ChatInterface.jsx
git commit -m "feat: add GraphVisualization, MessageList, and ChatInterface

- GraphVisualization with vis-network and color-coded nodes
- MessageList with auto-scroll and empty state
- ChatInterface with chat/graph view toggle
- Add example questions for first-time users

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 20: Main App & Styling

**Files:**
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/styles/main.css`

- [ ] **Step 1: Create main App component**

```jsx
// frontend/src/App.jsx
import { ChatInterface } from './components/ChatInterface';
import { useChat } from './hooks/useChat';
import './styles/main.css';

function App() {
  const { messages, isLoading, sendQuestion, clearChat } = useChat();

  return (
    <div className="app">
      <ChatInterface
        messages={messages}
        isLoading={isLoading}
        onSendQuestion={sendQuestion}
        onClearChat={clearChat}
      />
    </div>
  );
}

export default App;
```

- [ ] **Step 2: Create comprehensive CSS styling**

```css
/* frontend/src/styles/main.css */
:root {
  --primary: #2563eb;
  --success: #10b981;
  --danger: #ef4444;
  --warning: #f59e0b;
  --text: #1f2937;
  --text-light: #6b7280;
  --bg: #f9fafb;
  --bg-card: #ffffff;
  --border: #e5e7eb;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  background: var(--bg);
  color: var(--text);
}

.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Chat Interface */
.chat-interface {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.chat-header {
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-header h1 {
  font-size: 1.5rem;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.view-button {
  padding: 0.5rem 1rem;
  border: 1px solid var(--border);
  background: white;
  cursor: pointer;
  border-radius: 0.375rem;
}

.view-button.active {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.clear-button {
  padding: 0.5rem 1rem;
  border: 1px solid var(--border);
  background: white;
  cursor: pointer;
  border-radius: 0.375rem;
}

.clear-button:hover {
  background: var(--danger);
  color: white;
  border-color: var(--danger);
}

/* Chat Body */
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.message-list {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.empty-state h2 {
  margin-bottom: 1rem;
}

.example-questions {
  margin-top: 2rem;
  text-align: left;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.example-questions ul {
  list-style: none;
  padding: 0;
}

.example-questions li {
  padding: 0.5rem 1rem;
  background: var(--bg-card);
  margin: 0.5rem 0;
  border-radius: 0.375rem;
  border: 1px solid var(--border);
}

/* Messages */
.message {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1rem;
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-light);
}

.message-content {
  line-height: 1.6;
}

.question-message {
  background: #eff6ff;
  border-color: var(--primary);
}

.error-message {
  background: #fef2f2;
  border-color: var(--danger);
}

.error-badge {
  background: #fef2f2;
  border: 1px solid var(--danger);
  padding: 0.5rem;
  border-radius: 0.375rem;
  margin-top: 0.5rem;
  font-size: 0.875rem;
}

.message-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.action-button {
  padding: 0.5rem 1rem;
  border: 1px solid var(--border);
  background: white;
  cursor: pointer;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.action-button:hover {
  background: var(--bg);
}

/* Cypher Panel */
.cypher-panel {
  margin-top: 1rem;
  border: 1px solid var(--border);
  border-radius: 0.375rem;
  overflow: hidden;
}

.cypher-header {
  background: #1f2937;
  color: white;
  padding: 0.5rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cypher-code {
  background: #111827;
  color: #e5e7eb;
  padding: 1rem;
  overflow-x: auto;
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.875rem;
}

.copy-button {
  background: transparent;
  border: 1px solid white;
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.75rem;
}

/* Results Table */
.results-table-container {
  margin-top: 1rem;
  border: 1px solid var(--border);
  border-radius: 0.375rem;
  overflow: hidden;
}

.table-info {
  background: var(--bg);
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  color: var(--text-light);
}

.results-table {
  width: 100%;
  border-collapse: collapse;
}

.results-table th {
  background: #f3f4f6;
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
}

.results-table th:hover {
  background: #e5e7eb;
}

.results-table td {
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--border);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: var(--bg);
}

.pagination button {
  padding: 0.5rem 1rem;
  border: 1px solid var(--border);
  background: white;
  cursor: pointer;
  border-radius: 0.375rem;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Graph Visualization */
.graph-visualization {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.graph-header {
  background: #1f2937;
  color: white;
  padding: 0.75rem 1rem;
  font-weight: 600;
}

.graph-container {
  flex: 1;
  background: white;
  border: 1px solid var(--border);
}

.no-graph {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-light);
}

/* Question Input */
.chat-footer {
  background: var(--bg-card);
  border-top: 1px solid var(--border);
  padding: 1rem 2rem;
}

.question-input-form {
  display: flex;
  gap: 0.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

.question-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid var(--border);
  border-radius: 0.375rem;
  font-size: 1rem;
}

.question-input:focus {
  outline: none;
  border-color: var(--primary);
}

.ask-button {
  padding: 0.75rem 2rem;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-weight: 600;
  cursor: pointer;
}

.ask-button:hover:not(:disabled) {
  background: #1d4ed8;
}

.ask-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-indicator {
  text-align: center;
  color: var(--text-light);
  font-size: 0.875rem;
  margin-top: 0.5rem;
}
```

- [ ] **Step 3: Test frontend**

```bash
cd frontend
npm run dev
```

Expected: Frontend starts at http://localhost:5173, UI renders

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.jsx frontend/src/styles/main.css
git commit -m "feat: add main App component and comprehensive CSS

- Create App component connecting all pieces
- Add professional analyst-focused styling
- Responsive layout with chat and graph views
- Color-coded messages and components
- Clean, functional design

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 6: Testing & Polish

### Task 21: Integration Tests

**Files:**
- Create: `backend/tests/test_integration.py`

- [ ] **Step 1: Write integration tests**

```python
# backend/tests/test_integration.py
import pytest
from unittest.mock import Mock, patch
from core.pipeline import get_pipeline


@pytest.mark.integration
class TestPipelineIntegration:
    """Integration tests for full pipeline (requires mocking Neo4j/Groq)"""

    def test_full_pipeline_with_successful_query(self, mock_settings):
        """Test complete pipeline flow with successful query"""
        with patch('core.cypher_generator.get_groq_client') as mock_groq:
            with patch('core.query_executor.get_neo4j_client') as mock_neo4j:
                # Mock Groq responses
                mock_llm = Mock()
                mock_llm.chat_completion.side_effect = [
                    "MATCH (c:Crime) RETURN count(c) AS total",  # Cypher generation
                    "There are 100 crimes in the database."     # Answer generation
                ]
                mock_groq.return_value = mock_llm

                # Mock Neo4j response
                mock_client = Mock()
                mock_client.query.return_value = [{"total": 100}]
                mock_neo4j.return_value = mock_client

                # Run pipeline
                pipeline = get_pipeline()
                response = pipeline.run("How many crimes?")

                # Assertions
                assert response["question"] == "How many crimes?"
                assert "100" in response["answer"]
                assert "MATCH (c:Crime)" in response["cypher"]
                assert response["results"] == [{"total": 100}]
                assert response["attempts"] == 1
                assert response["execution_time_ms"] > 0

    def test_pipeline_with_retry_on_syntax_error(self, mock_settings):
        """Test pipeline retries on syntax error"""
        with patch('core.cypher_generator.get_groq_client') as mock_groq:
            with patch('core.query_executor.get_neo4j_client') as mock_neo4j:
                from neo4j.exceptions import CypherSyntaxError

                # Mock Groq - first bad, then good
                mock_llm = Mock()
                mock_llm.chat_completion.side_effect = [
                    "BAD QUERY",                                  # First attempt
                    "MATCH (c:Crime) RETURN count(c)",          # Retry
                    "There are 50 crimes."                        # Answer
                ]
                mock_groq.return_value = mock_llm

                # Mock Neo4j - first fails, then succeeds
                mock_client = Mock()
                mock_client.query.side_effect = [
                    CypherSyntaxError("Invalid syntax"),
                    [{"count": 50}]
                ]
                mock_neo4j.return_value = mock_client

                pipeline = get_pipeline()
                response = pipeline.run("How many crimes?")

                assert response["attempts"] == 2
                assert response["results"] == [{"count": 50}]
                assert "error" not in response
```

- [ ] **Step 2: Run integration tests**

```bash
pytest tests/test_integration.py -v
```

Expected: PASS (2 tests)

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_integration.py
git commit -m "test: add integration tests for full pipeline

- Test successful query execution flow
- Test retry logic with syntax error recovery
- Mock Neo4j and Groq for isolated testing

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 22: End-to-End Manual Testing

**Files:**
- Create: `backend/tests/manual_test_checklist.md`

- [ ] **Step 1: Create manual test checklist**

```markdown
# backend/tests/manual_test_checklist.md
# Manual Testing Checklist

## Backend Tests

### Health Check
- [ ] `curl http://localhost:8000/api/health` returns healthy status
- [ ] Neo4j connected: true
- [ ] Groq configured: true
- [ ] Schema loaded: true

### Schema Endpoint
- [ ] `curl http://localhost:8000/api/schema` returns formatted schema
- [ ] NODES section present
- [ ] RELATIONSHIPS section present
- [ ] PROPERTY VALUES section present

### Examples Endpoint
- [ ] `curl http://localhost:8000/api/examples` returns 24 examples
- [ ] Each example has question and cypher fields

### Ask Endpoint - Basic Queries
- [ ] "How many crimes are recorded?" returns count
- [ ] "Show all crimes related to drugs" returns results
- [ ] "Which area has the most crimes?" returns area code

### Ask Endpoint - Retry Logic
- [ ] Invalid queries trigger retry (check logs)
- [ ] Empty results trigger reformulation
- [ ] Max 3 attempts respected

## Frontend Tests

### UI Load
- [ ] App loads at http://localhost:5173
- [ ] Header displays correctly
- [ ] Empty state shows example questions
- [ ] Input field is enabled

### Question Submission
- [ ] Can type question in input
- [ ] Enter key submits question
- [ ] Ask button submits question
- [ ] Loading indicator appears during processing

### Answer Display
- [ ] Answer appears in chat
- [ ] Execution time displayed
- [ ] Attempt count shown
- [ ] Show Cypher button works
- [ ] Cypher panel displays correctly
- [ ] Copy button copies Cypher

### Results Table
- [ ] View Table button appears when results exist
- [ ] Table displays all columns
- [ ] Column sorting works
- [ ] Pagination works (test with >20 results)

### Graph Visualization
- [ ] Graph toggle button enabled when graph data exists
- [ ] Graph renders nodes and edges
- [ ] Nodes are color-coded by type
- [ ] Hover shows node properties

### Export
- [ ] Export CSV button downloads file
- [ ] CSV contains all results
- [ ] Headers are correct

### Error Handling
- [ ] Backend offline shows error message
- [ ] Invalid queries show error
- [ ] Empty results show "No records found"

## Performance
- [ ] Most queries complete in <5s
- [ ] No memory leaks after 20+ queries
- [ ] Clear chat button clears all messages
```

- [ ] **Step 2: Start both backend and frontend**

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

- [ ] **Step 3: Complete manual test checklist**

Go through each item in `manual_test_checklist.md` and verify

Expected: All items pass

- [ ] **Step 4: Commit**

```bash
git add backend/tests/manual_test_checklist.md
git commit -m "test: add manual testing checklist

- Comprehensive checklist for backend and frontend
- Test all endpoints and UI interactions
- Verify error handling and performance
- Document expected behaviors

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 23: Documentation & Deployment Guide

**Files:**
- Update: `backend/README.md`
- Update: `frontend/README.md`
- Create: `README.md` (root)
- Create: `DEPLOYMENT.md`

- [ ] **Step 1: Update backend README**

```bash
# Enhance backend/README.md with:
# - Complete API documentation
# - Environment setup instructions
# - Testing commands
# - Troubleshooting section
```

- [ ] **Step 2: Create frontend README**

```markdown
# frontend/README.md
# POLE NL-to-Cypher QA System - Frontend

React frontend for crime investigation QA system.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start development server:
   ```bash
   npm run dev
   ```

3. Build for production:
   ```bash
   npm run build
   ```

## Features

- Natural language question input
- Real-time answer display with metadata
- Cypher query visualization with copy button
- Sortable, paginated results table
- Graph visualization with vis-network
- CSV export functionality

## Components

- `ChatInterface` - Main container
- `MessageList` - Conversation history
- `AnswerCard` - Q&A display
- `CypherPanel` - Query viewer
- `ResultsTable` - Tabular results
- `GraphVisualization` - Network graph
- `QuestionInput` - Input component
- `ExportButton` - CSV export

## Customization

Edit `src/styles/main.css` to customize colors and layout.
```

- [ ] **Step 3: Create root README**

```markdown
# README.md
# POLE Neo4j NL-to-Cypher QA System

Natural language to Cypher query system for crime investigation analysts.

## Architecture

- **Backend**: FastAPI (Python) with 3-step pipeline
- **Frontend**: React + Vite
- **Database**: Neo4j (POLE crime graph)
- **LLM**: LLaMA 3.3 70B via Groq

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Neo4j database (populated with POLE data)
- Groq API key

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with credentials
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173

## Features

✅ Natural language question processing
✅ Cypher query generation with LLaMA 3.3 70B
✅ Self-correcting retry logic (max 3 attempts)
✅ Real-time answer synthesis
✅ Interactive graph visualization
✅ Sortable, paginated results table
✅ CSV export
✅ 24 curated few-shot examples

## API Endpoints

- `POST /api/ask` - Submit question
- `GET /api/health` - Health check
- `GET /api/schema` - View schema
- `GET /api/examples` - View examples

## Testing

```bash
cd backend
pytest tests/ -v
```

## Documentation

- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Design Spec](docs/superpowers/specs/2026-03-25-pole-nl-to-cypher-design.md)

## License

MIT
```

- [ ] **Step 4: Create deployment guide**

```markdown
# DEPLOYMENT.md
# Deployment Guide

## Production Deployment

### Option 1: Docker Compose

1. Build containers:
   ```bash
   docker-compose build
   ```

2. Start services:
   ```bash
   docker-compose up -d
   ```

### Option 2: Cloud Platforms

**Backend (Railway/Render):**
- Set environment variables in platform
- Connect to Neo4j AuraDB
- Deploy from GitHub

**Frontend (Vercel/Netlify):**
- Connect GitHub repository
- Set build command: `npm run build`
- Set output directory: `dist`
- Configure API proxy in build settings

## Environment Variables

See `.env.example` for required variables.

## Monitoring

- Check logs: `docker-compose logs -f`
- Health endpoint: `/api/health`

## Scaling

- Backend: Horizontal scaling supported (stateless)
- Frontend: CDN distribution recommended
- Database: Use Neo4j AuraDB for managed service
```

- [ ] **Step 5: Commit**

```bash
git add README.md DEPLOYMENT.md backend/README.md frontend/README.md
git commit -m "docs: add comprehensive documentation

- Root README with quick start guide
- Enhanced backend and frontend READMEs
- Deployment guide for Docker and cloud platforms
- API endpoint documentation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 24: Final Polish & Verification

- [ ] **Step 1: Run all tests**

```bash
cd backend
pytest tests/ -v --cov=app --cov=core
```

Expected: All tests pass with >80% coverage

- [ ] **Step 2: Check code quality**

```bash
# Format code
black app/ core/ tests/

# Check imports
isort app/ core/ tests/ --check-only
```

- [ ] **Step 3: Verify frontend build**

```bash
cd ../frontend
npm run build
```

Expected: Build succeeds with no errors

- [ ] **Step 4: Test production build locally**

```bash
npm run preview
```

Expected: Production build serves correctly

- [ ] **Step 5: Create final commit**

```bash
git add .
git commit -m "chore: final polish and verification

- All tests passing
- Code formatted with black
- Frontend builds successfully
- Documentation complete
- Ready for deployment

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: Create release tag**

```bash
git tag -a v1.0.0 -m "Release v1.0.0 - POLE NL-to-Cypher QA System"
git push origin v1.0.0
```

---

## Success Criteria Verification

### Functional Requirements
- [ ] Users can ask NL questions about crime investigations
- [ ] System generates valid Cypher queries
- [ ] Results display as answer + table + graph visualization
- [ ] Self-correction works (retry loop recovers from errors)
- [ ] Export functionality works (CSV download)
- [ ] Transparent Cypher display for analysts

### Performance Requirements
- [ ] 90% of queries respond in <5 seconds
- [ ] 24/24 few-shot examples return results
- [ ] 4/5 novel queries succeed (80%+)
- [ ] <30% of queries need retries

### Quality Requirements
- [ ] Generated Cypher follows Neo4j best practices
- [ ] Error messages are professional and helpful
- [ ] UI is clean and analyst-appropriate
- [ ] Code is documented and tested

---

## Implementation Complete

All phases completed:
✅ Backend foundation (config, database, LLM, schema)
✅ Few-shot examples (24 curated pairs)
✅ Core pipeline (generator, executor, answer synthesis)
✅ FastAPI application (routes, models, main app)
✅ React frontend (components, hooks, styling)
✅ Testing (unit, integration, manual)
✅ Documentation (README, deployment guide)
✅ Polish & verification

**Estimated implementation time: 7-9 days**

**Next steps:**
1. Deploy to production environment
2. Monitor query success rates
3. Collect user feedback
4. Iterate on few-shot examples based on common failures
