# Investigraph: NL-to-Cypher → GraphRAG Migration Plan

## Executive Summary

Migrate Investigraph from a rigid NL-to-Cypher pipeline (LLM generates Cypher → Neo4j executes → LLM summarizes) to a Neo4j GraphRAG architecture with multiple retrieval strategies: vector search, graph-enhanced vector search, LLM-generated Cypher, and agentic retriever selection. Uses the `neo4j-graphrag` Python library.

## Decisions Made

| Decision | Choice | Rationale |
|---|---|---|
| Embedding model | SentenceTransformers `all-MiniLM-L6-v2` (384 dims) | Free, local, zero API dependency, native neo4j-graphrag support |
| Primary LLM | Groq (llama-3.3-70b) with custom `LLMInterface` wrapper | Keep existing free tier; build ~40 line wrapper |
| API contract | New enriched API with retriever metadata | User wants richer response showing which retriever was used |
| KG construction | Excluded | Data already in Neo4j from CSV imports |
| Frontend | Minimal updates for new API fields | Keep React + TypeScript + vis-network |
| Migration strategy | Strangler Fig | Build new pipeline alongside old, verify, then cut over |

## Architecture: Before vs After

### BEFORE (Current)
```
User Question → CypherGenerator (LLM + schema + 24 examples)
             → QueryExecutor (Neo4j + retry x3)
             → AnswerGenerator (LLM)
             → Response
```

### AFTER (GraphRAG)
```
User Question → ToolsRetriever (LLM selects best retriever)
             ├─→ Text2CypherRetriever (structured queries, with retry wrapper)
             ├─→ VectorRetriever (semantic search on node embeddings)
             └─→ VectorCypherRetriever (vector + graph traversal)
             → GraphRAG (orchestrates retriever + LLM answer generation)
             → Response (with retriever metadata)
```

---

## Phase 0: Prerequisites Verification
**Duration**: ~30 min | **Risk**: BLOCKER if Neo4j < 5.18.1

### Tasks
1. **Verify Neo4j version** supports vector indexes (≥5.18.1)
   - Run: `CALL dbms.components() YIELD name, versions RETURN name, versions`
   - If version is too old, must upgrade Neo4j before proceeding
2. **Install neo4j-graphrag library** and verify imports
   - `pip install neo4j-graphrag[all] sentence-transformers`
   - Verify: `python -c "from neo4j_graphrag.retrievers import VectorRetriever, Text2CypherRetriever, VectorCypherRetriever; print('OK')"`
3. **Audit node property text content** — determine which properties have meaningful text worth embedding
   - Run sampling queries: `MATCH (c:Crime) RETURN c LIMIT 5`, `MATCH (p:Person) RETURN p LIMIT 5`, etc.
   - Identify which properties have actual text (vs empty/numeric/IDs)

### Acceptance Criteria
- [ ] Neo4j version confirmed ≥5.18.1
- [ ] `neo4j-graphrag` imports successfully
- [ ] Node property audit complete — embedding targets identified

### Files Changed
- `backend/requirements.txt` — add `neo4j-graphrag[all]`, `sentence-transformers`
- `backend/.env.example` — no changes yet

---

## Phase 1: LLM Abstraction Layer
**Duration**: ~2 hours | **Risk**: Low

### Context
Current `app/llm.py` has a `GroqClient` wrapping the `groq` SDK directly. The `neo4j-graphrag` library requires LLMs to implement its `LLMInterface` ABC (with `invoke()` and `ainvoke()` methods returning `LLMResponse`). We must build a wrapper.

### Tasks
1. **Create `GroqLLM(LLMInterface)` wrapper** in `backend/app/llm.py`
   - Subclass `neo4j_graphrag.llm.LLMInterface`
   - Implement `invoke(input: str) -> LLMResponse` using existing Groq SDK
   - Implement `ainvoke(input: str) -> LLMResponse` (async version)
   - Accept `model_params` dict (temperature, max_tokens, etc.)
   - Keep existing `GroqClient` temporarily for backward compatibility during migration
2. **Create embedder singleton** in `backend/app/embedder.py`
   - Use `neo4j_graphrag.embeddings.SentenceTransformerEmbeddings`
   - Model: `all-MiniLM-L6-v2` (384 dimensions)
   - Singleton pattern matching codebase style (`get_embedder()`)
3. **Extend `config.py`** with new settings
   - `EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"`
   - `VECTOR_INDEX_NAME: str = "pole_vector_index"`
   - `VECTOR_DIMENSIONS: int = 384`
4. **Unit test** the GroqLLM wrapper
   - Mock Groq client, verify `invoke()` returns `LLMResponse` with correct `.content`

### Acceptance Criteria
- [ ] `GroqLLM` instantiates and `invoke("test")` returns `LLMResponse` (mocked)
- [ ] `SentenceTransformerEmbeddings` instantiates and produces 384-dim vectors
- [ ] Config loads new settings without breaking existing settings

### Files Changed
- `backend/app/llm.py` — add `GroqLLM(LLMInterface)` class + `get_graphrag_llm()` accessor
- `backend/app/embedder.py` — NEW file: embedder singleton
- `backend/app/config.py` — add new settings fields
- `backend/tests/test_llm.py` — add GroqLLM wrapper tests
- `backend/.env.example` — add new config vars

### MUST NOT
- Remove existing `GroqClient` class (still used by old pipeline during migration)
- Import LangChain for LLM abstraction
- Add more than one embedding model

---

## Phase 2: Vector Infrastructure
**Duration**: ~3 hours | **Risk**: Medium (embedding quality depends on property selection)

### Context
Need to add vector embeddings to existing POLE nodes in Neo4j and create a vector index. This enables semantic search via `VectorRetriever`.

### Tasks
1. **Create embedding migration script** `backend/scripts/create_embeddings.py`
   - Standalone script (not part of app startup) — idempotent, can be re-run
   - For each target node type, concatenate selected text properties into a single string
   - Generate embeddings via SentenceTransformerEmbeddings
   - Store as `embedding` property on each node
   - Batch processing (100 nodes at a time) with progress logging
   - **Target nodes and properties** (based on Phase 0 audit, preliminary):
     - `Crime`: `type` + `last_outcome` + `note` + `charge` → concatenated text
     - `Person`: `name` + `surname` → concatenated text  
     - `Location`: `address` + `postcode` → concatenated text
     - `Officer`: `name` + `surname` + `rank` → concatenated text
     - `Vehicle`: `make` + `model` + `reg` → concatenated text
     - Skip: `PhoneCall` (only timestamps), `Phone` (only number), `Email` (only address), `PostCode` (only code), `AREA` (only code)
2. **Create vector index in Neo4j**
   - Index name: `pole_vector_index`
   - Dimensions: 384 (matching SentenceTransformers output)
   - Similarity function: cosine
   - Either via script or as part of embedding migration
   - NOTE: Neo4j vector indexes are per-label. May need one index per label, or use a single `__Entity__` label approach. Decision: Create a `Chunk` label with `text` and `embedding` properties that references source nodes, OR embed directly on nodes. **Recommended: Embed directly on nodes** — simpler, nodes already exist.
   - If Neo4j requires one vector index per label, create indexes for Crime, Person, Location, Officer, Vehicle.
3. **Verify vector search** works with `VectorRetriever`
   - Test query: "drug crimes" should return Crime nodes with drug-related types

### Acceptance Criteria
- [ ] Embedding script runs without errors on all target nodes
- [ ] Vector index(es) created and visible: `SHOW INDEXES` returns the new index(es)
- [ ] `VectorRetriever.search(query_text="drug crimes", top_k=5)` returns relevant results
- [ ] Embeddings are stored on nodes: `MATCH (c:Crime) WHERE c.embedding IS NOT NULL RETURN count(c)` > 0

### Files Changed
- `backend/scripts/create_embeddings.py` — NEW: standalone embedding migration script
- `backend/scripts/__init__.py` — NEW: package init

### MUST NOT
- Run embedding as part of app startup (too slow for 28K nodes)
- Embed node properties that are primarily null/empty (Person.age, Crime.note mostly empty)
- Use more than one embedding model across node types

---

## Phase 3: Retriever Assembly
**Duration**: ~4 hours | **Risk**: Medium (Text2CypherRetriever prompt quality)

### Context
Build three retrievers that will be assembled into the ToolsRetriever. The Text2CypherRetriever replaces the current CypherGenerator + QueryExecutor combo. The VectorRetriever enables semantic search. The VectorCypherRetriever adds graph traversal enrichment.

### Tasks
1. **Build `Text2CypherRetriever` configuration** in `backend/core/retrievers.py`
   - Pass neo4j_schema from existing `SchemaIntrospector.introspect()`
   - Pass all 24 few-shot examples from `few_shot_examples.yaml`
   - Extract domain-specific prompt rules from `cypher_generator.py:_build_system_prompt()` into a custom prompt template
   - **CRITICAL**: Wrap with retry logic — catch `Text2CypherRetrievalError`, build error context, retry up to 3 times (preserving current self-healing behavior)
2. **Build `VectorRetriever` configuration**
   - Use the vector index from Phase 2
   - Configure `return_properties` for each node type
   - Set default `top_k=5`
3. **Build `VectorCypherRetriever` configuration**
   - Vector search + graph traversal query
   - Retrieval query traverses 1-2 hops from matched nodes to get related entities
   - Example: Find crime node by vector → traverse to Person, Location, Officer
4. **Build result formatter** for each retriever
   - Format `RetrieverResultItem` content for clean LLM prompt injection
5. **Test each retriever independently**

### Acceptance Criteria
- [ ] `Text2CypherRetriever.search("How many crimes are recorded?")` returns count result
- [ ] `Text2CypherRetriever` retry fires on intentionally bad Cypher and self-heals
- [ ] `VectorRetriever.search("drug crimes in WN area")` returns relevant Crime nodes
- [ ] `VectorCypherRetriever.search("people involved in robberies")` returns nodes + related graph context

### Files Changed
- `backend/core/retrievers.py` — NEW: all retriever configurations + retry wrapper
- `backend/core/prompts.py` — NEW: extracted prompt templates (system prompts, RAG templates)
- `backend/tests/test_retrievers.py` — NEW: retriever tests

### MUST NOT
- Build a custom retriever router — ToolsRetriever handles this
- Drop the few-shot examples — they're the single biggest driver of Cypher quality
- Lose the retry/self-healing behavior

---

## Phase 4: GraphRAG Orchestration + New API
**Duration**: ~4 hours | **Risk**: Medium (ToolsRetriever tool description quality)

### Context
Assemble all retrievers into a `ToolsRetriever` that uses the LLM to select the best retriever per query. Wire into `GraphRAG` class for answer generation. Build new API endpoint with enriched response.

### Tasks
1. **Build `ToolsRetriever`** in `backend/core/graphrag_pipeline.py`
   - Convert each retriever to a tool with clear descriptions:
     - `text2cypher_tool`: "Use for structured queries: counts, aggregations, specific filters, relationship traversals. Best when the question maps to a database query pattern."
     - `vector_tool`: "Use for semantic/fuzzy questions: finding similar concepts, understanding context, exploratory questions that don't map to exact filters."
     - `vector_cypher_tool`: "Use for questions needing both semantic understanding and relationship context: 'people involved in crimes similar to X', 'what connects these entities'."
   - **Tool descriptions are critical** — they drive LLM routing quality
2. **Build `GraphRAG` instance**
   - Use `ToolsRetriever` + `GroqLLM` + custom `RagTemplate`
   - Custom `RagTemplate` should include investigation-focused instructions (carry over from answer_generator.py)
3. **Build new pipeline class** `GraphRAGPipeline` in `backend/core/graphrag_pipeline.py`
   - Wraps `GraphRAG.search()` call
   - Extracts graph visualization data from retriever results (equivalent to current `_extract_graph_data`)
   - Builds enriched response including: which retriever was selected, retriever confidence, source context
   - Measures execution time
4. **Create new Pydantic models** for enriched response
   - Extend `QueryResponse` with: `retriever_used: str`, `retriever_context: list[str]`, `confidence_score: Optional[float]`
   - Keep backward-compatible fields: `question`, `answer`, `cypher` (nullable for vector-only), `results`, `graph_data`, `attempts`, `execution_time_ms`
5. **Create new API endpoint** `POST /api/query` (replace existing)
   - Use new `GraphRAGPipeline` 
   - Return enriched response

### Acceptance Criteria
- [ ] `ToolsRetriever` selects `text2cypher` for "How many crimes are recorded?"
- [ ] `ToolsRetriever` selects `vector` for "Tell me about drug-related activities"
- [ ] Full pipeline returns valid response for 5+ diverse test queries
- [ ] Response includes `retriever_used` field
- [ ] `graph_data` still populated with nodes and edges for visualization
- [ ] `POST /api/query` endpoint works end-to-end

### Files Changed
- `backend/core/graphrag_pipeline.py` — NEW: GraphRAG pipeline orchestration
- `backend/app/models.py` — extend QueryResponse with new fields
- `backend/app/main.py` — update `/api/query` to use new pipeline
- `backend/tests/test_graphrag_pipeline.py` — NEW: pipeline integration tests

### MUST NOT
- Build a custom router for retriever selection
- Remove the old pipeline.py until new pipeline is verified
- Change the frontend URL paths (/api/query stays the same)

---

## Phase 5: Integration, Cutover & Testing
**Duration**: ~3 hours | **Risk**: Low (if Phases 1-4 verified)

### Tasks
1. **Remove old pipeline code**
   - Delete or deprecate: `core/pipeline.py`, `core/cypher_generator.py`, `core/query_executor.py`, `core/answer_generator.py`
   - Keep: `core/schema_introspector.py` (still used by Text2CypherRetriever), `core/few_shot_loader.py` (still used)
   - Keep: `app/llm.py` old `GroqClient` can be removed once all references gone
2. **Update startup lifecycle** in `main.py`
   - Initialize new `GraphRAGPipeline` instead of old `Pipeline`
   - Schema introspection still needed (for Text2CypherRetriever)
   - Embedder initialization (model download on first run)
3. **Update all tests**
   - Remove tests for deleted components
   - Ensure new component tests pass
   - Full integration test via API
4. **Frontend updates** (minimal)
   - Update TypeScript types in `api.ts` for new response fields
   - Display `retriever_used` in UI (optional but nice)
   - `cypher` field may be null for vector-only queries — handle gracefully
5. **End-to-end verification**
   - Test all 24 few-shot example questions
   - Test 5+ novel semantic questions that the OLD system couldn't answer
   - Test edge cases: nonsensical input, empty results, very long questions
   - Verify graph visualization still works

### Acceptance Criteria
- [ ] `pytest backend/tests/ -v` — all tests pass
- [ ] Old pipeline files removed, no import errors
- [ ] 24 few-shot questions return valid results
- [ ] "Tell me about drug-related activities" (semantic query) returns meaningful answer (OLD system couldn't do this)
- [ ] "asdfghjkl random noise" returns graceful error (not 500)
- [ ] Frontend displays results with graph visualization
- [ ] `/health` endpoint still works

### Files Changed
- `backend/core/pipeline.py` — DELETED
- `backend/core/cypher_generator.py` — DELETED
- `backend/core/query_executor.py` — DELETED  
- `backend/core/answer_generator.py` — DELETED
- `backend/app/main.py` — update lifecycle
- `backend/app/llm.py` — remove old GroqClient (keep GroqLLM)
- `backend/tests/*` — update tests
- `frontend/src/services/api.ts` — update types
- `frontend/src/components/ResponsePanel.tsx` — show retriever info

### MUST NOT
- Delete schema_introspector.py or few_shot_loader.py (still needed)
- Delete case_study_loader.py (still used by /api/case-studies)

---

## Phase 6: Documentation Overhaul
**Duration**: ~3 hours | **Risk**: Low

### Context
User needs updated docs for PPT and reports. Only write docs that describe the implemented, tested system.

### Tasks
1. **Rewrite `README.md`** — new architecture overview, setup steps including embedding migration
2. **Rewrite `docs/ARCHITECTURE.md`** — new Mermaid diagrams showing GraphRAG pipeline flow
3. **Rewrite `docs/METHODOLOGY.md`** — new 4-module methodology reflecting GraphRAG
4. **Update `docs/MERMAID_DIAGRAMS.md`** — new architecture diagrams
5. **Update `docs/PROJECT_OVERVIEW.md`** — new executive summary
6. **Update `docs/PRESENTATION_GUIDE.md`** — new talking points reflecting GraphRAG
7. **Update `docs/DATASET.md`** — add vector embedding section
8. **Update `backend/README.md`** — new setup instructions, new component descriptions
9. **Update `backend/.env.example`** — new environment variables
10. **Update `DEPLOYMENT.md`** — add embedding migration step to deployment
11. **Update `implementation_plan.md`** — reflect the new architecture or replace entirely

### Acceptance Criteria
- [ ] All docs accurately describe the implemented system
- [ ] Mermaid diagrams render correctly
- [ ] Setup instructions in README work from scratch
- [ ] No references to old NL-to-Cypher-only architecture remain (except as "previous version" context)

### Files Changed
- All `docs/*.md` files
- `README.md`
- `backend/README.md`
- `backend/.env.example`
- `DEPLOYMENT.md`
- `implementation_plan.md`

### MUST NOT
- Describe aspirational features not yet implemented
- Remove all mention of Cypher generation (Text2CypherRetriever still generates Cypher)

---

## Risk Register

| Risk | Severity | Mitigation |
|---|---|---|
| Neo4j version < 5.18.1 | BLOCKER | Verify in Phase 0 before any work |
| Groq/Llama poor tool-calling for ToolsRetriever | HIGH | Test early in Phase 4; fallback to hardcoded routing if needed |
| Embedding sparse/empty properties yields poor search | MEDIUM | Audit in Phase 0; only embed non-empty text fields |
| Losing self-healing retry | HIGH | Explicit retry wrapper around Text2CypherRetriever |
| Neo4j vector index per-label limitation | MEDIUM | Create separate indexes per label, or use a unified Chunk approach |
| GroqLLM wrapper doesn't match LLMInterface exactly | HIGH | Reference exact ABC from neo4j-graphrag source code |

## Total Estimated Duration
~15-18 working hours across 7 phases (Phase 0-6)
