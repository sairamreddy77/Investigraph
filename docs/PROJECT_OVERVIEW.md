# Investigraph - Project Overview

## Executive Summary

**Investigraph** is an advanced GraphRAG (Retrieval-Augmented Generation) system tailored for law enforcement and crime investigation. By combining the structured power of Neo4j graph databases with the semantic reasoning of Large Language Models (LLMs), Investigraph allows investigators to query complex POLE (Person, Object, Location, Event) knowledge graphs using plain English.

The system has been recently migrated from a legacy NL-to-Cypher pipeline to a modern **GraphRAG architecture** using the `neo4j-graphrag` framework, significantly improving retrieval accuracy and answer quality through multi-strategy search.

### The Problem
- **Technical Barrier**: Investigators need deep graph insights but lack Cypher expertise.
- **Context Gap**: Traditional search often misses the "neighborhood" of a criminal incident.
- **Hallucinations**: Standard LLMs may invent facts not present in the evidence database.

### The Solution: GraphRAG
Investigraph addresses these challenges by grounding AI responses in a verified Neo4j knowledge graph. The system intelligently routes questions to different retrieval strategies, ensuring that every answer is contextually rich and factually accurate.

---

## Core Pillars of the New Architecture

### 1. Multi-Strategy Retrieval
Unlike the previous system which relied solely on Cypher generation, the new architecture employs three distinct retrievers:
- **Text2Cypher**: Precision-focused structured queries for counts and complex hops.
- **Vector Search**: Semantic lookup for keyword-based or similar-incident searches.
- **VectorCypher**: Hybrid search that retrieves semantic matches and their immediate graph neighborhood for maximum context.

### 2. Intelligent Query Routing
A heuristic-based classification engine analyzes incoming questions to select the most appropriate retriever, ensuring optimal performance and response relevance.

### 3. Context-Grounded Answer Generation
Powered by **Groq Llama-3.3-70b**, the system synthesizes answers based strictly on retrieved graph context. This approach provides "grounded truth" and eliminates AI hallucinations.

---

## Technical Specifications

- **AI Engine**: Groq Llama-3.3-70b-versatile (State-of-the-art reasoning and speed).
- **Embeddings**: SentenceTransformers `all-MiniLM-L6-v2` (384-dimensional vector space).
- **Database**: Neo4j 5.23+ with native vector index support.
- **Orchestration**: `neo4j-graphrag` Python framework.
- **Frontend**: React 18 + TypeScript + vis-network for interactive graph exploration.

---

## Comparison: Legacy vs. GraphRAG

| Feature | Legacy System | New GraphRAG System |
|---|---|---|
| **Pipeline** | NL → Cypher → Results | NL → Routing → Multi-Strategy Retrieval → RAG |
| **Search Mode** | Structured only | Structured, Semantic, and Hybrid |
| **Answer Quality** | Template-based or simple LLM | Grounded GraphRAG synthesis |
| **Context Window** | Limited to query results | Enriched graph neighborhoods |
| **Error Handling** | Basic retry on syntax | Self-healing + Automatic strategy fallback |

---

## Key Benefits for Investigators

- **Speed**: Get complex multi-hop answers in 1-3 seconds.
- **Accuracy**: Answers are directly linked to database records with visible metadata.
- **Exploration**: Interactive graph visualization allows for manual relationship tracing.
- **Ease of Use**: No need to know Cypher, SQL, or database schemas.

---

## Future Roadmap

- **Voice Integration**: Hands-free investigation querying.
- **Advanced Analytics**: Community detection and centrality analysis for criminal hierarchies.
- **Reporting**: One-click PDF export for investigation summaries and case files.
- **Collaboration**: Shared investigation spaces for multi-agency task forces.
