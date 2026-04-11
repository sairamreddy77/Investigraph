# Investigraph: System Architecture and Implementation

This document provides a comprehensive, in-depth overview of the Investigraph system. It explains how the application transforms natural language questions into precise, actionable insights for crime investigators. It covers the core data models, the vector embedding infrastructure, the query classification logic, and the multi-strategy retrieval architecture.

## 1. What is Investigraph?

Investigraph is a specialized natural language question-answering system designed specifically for crime investigation data. It interfaces with a Neo4j graph database that utilizes the POLE data model.

### The POLE Data Model
The database is structured around four primary entities, which are essential for investigative work:
- **Person**: This includes suspects, victims, witnesses, and any other parties involved in an investigation.
- **Object**: This covers evidence, vehicles, weapons, and phones.
- **Location**: Addresses, specific landmarks, and coordinates where incidents occur.
- **Event**: Specific criminal incidents, investigations, or interactions between other entities.

By modeling data as a graph rather than isolated tables, Investigraph allows investigators to uncover hidden links between seemingly unrelated crimes or individuals. A crime at one location might be linked to a person who was a witness at another event, and the graph structure makes these connections explicit and searchable.

## 2. How Do Vectors and Embeddings Work Here?

Vector embeddings are the cornerstone of the system's semantic search capabilities. They allow the system to understand the "meaning" of a query rather than just looking for exact keyword matches. This is a critical feature because investigators may not always use the exact terminology found in official reports.

### What are Embeddings?
An embedding is a mathematical representation of text. It converts a string of words into a fixed-length list of numbers, known as a "vector." The critical property of these vectors is that text with similar meanings will have vectors that are numerically "close" to each other in a multi-dimensional space. For instance, the vector for "theft" will be closer to the vector for "stealing" than it will be to the vector for "assault."

### The Embedding Model: all-MiniLM-L6-v2
Investigraph uses the `all-MiniLM-L6-v2` model from the SentenceTransformers library. 
- **Dimensions**: It converts any input text into a 384-dimensional vector. This means every piece of text is represented as a list of 384 numbers.
- **Efficiency**: It is a lightweight, high-performance model that runs locally on the application server. This ensures data privacy, as sensitive investigation data is not sent to external APIs for embedding.
- **Cost**: It is open-source and entirely free to use, making the system highly scalable without incurring per-token costs for embeddings.

### Implementation on Crime Nodes
The system focuses its semantic search on the `Crime` nodes within the Neo4j database. 
- **The Input String**: For every crime, the system concatenates the `type`, `charge`, `note`, and `last_outcome` properties into a single text block. This ensures that the context of the crime is captured in the vector.
- **Storage**: This text block is processed by the model, and the resulting 384-number vector is stored directly on the Crime node in a property named `embedding`.
- **Indexing**: Neo4j maintains a native vector index called `crime_vector_index`. This index is optimized for fast similarity searches across the ~28,000 crime nodes in the database.

### How Vector Search Operates
When a user asks a question like "Tell me about theft incidents," the following steps occur:
1. The question is converted into a 384-dimensional vector using the same `all-MiniLM-L6-v2` model.
2. The system performs a "similarity search" against the Neo4j vector index.
3. It calculates the cosine similarity between the question vector and all stored crime vectors.
4. The nodes with the highest similarity scores are retrieved.

### Semantic Search Example
If a user searches for "theft," the vector search can successfully find nodes with types like "Shoplifting" or "Burglary," even if the word "theft" never appears in their description. This is because the embedding model understands that these concepts are semantically related in the vector space.

The embedding process is managed by a migration script (`scripts/create_embeddings.py`), which is typically run once during the initial data ingestion to populate the vectors and initialize the index.

## 3. The Question Classifier (The Brain)

Before any data is retrieved, the system must decide which tool or strategy is best suited to answer the specific question. This is handled by a heuristic classifier that analyzes the query against seven prioritized sections. The classifier is designed to route queries to the most efficient retriever for the task at hand.

### Section 1: Explicit Structured Keywords
If the query contains terms suggesting a need for aggregation, counting, or specific graph traversals, it is routed to the **text2cypher** retriever.
- **Keywords**: "how many", "count", "total", "which area", "which officer", "top", "most", "least", "network", "linked", "party to".
- **Example**: "How many crimes happened in area WN?"

### Section 2: Filter-Heavy Scoring
The classifier looks for specific entities or constraints. Each match adds one point to a score. If the score is 2 or higher, it uses **text2cypher**.
- **Area Codes**: Detected via regex (e.g., BL6, WN3, M23).
- **Outcome Keywords**: "under investigation", "charged", "cautioned", "closed".
- **Multi-Entity Requests**: Queries involving 2 or more of: people, officers, evidence, vehicles.
- **Prefixes**: "find all", "list all", "show all".
- **Example**: "Find all drug-related crimes in BL6 area that are under investigation" (Scores 3 points: area code + outcome + crime type filter).

### Section 3: Person/Entity-Specific Queries
Patterns indicating a focus on a specific individual or their relationships are routed to **text2cypher**.
- **Patterns**: "involved in", "connected to", "associated with", "crimes is", "family of".
- **Example**: "What crimes is Raymond Walker involved in?"

### Section 4: Semantic and Exploratory Patterns
General or broad requests for information are routed to the **vector_cypher** hybrid retriever.
- **Patterns**: "tell me about", "describe", "explain", "what do you know", "what happened".
- **Example**: "Tell me about incidents involving theft."

### Section 5: Question Words
Queries starting with "who", "what", "where", or "when" often require specific attribute lookups and are sent to **text2cypher**.
- **Example**: "Who investigated the most crimes?"

### Section 6: Short Queries
Queries consisting of 4 words or fewer are treated as keyword lookups and sent to the **vector** retriever.
- **Example**: "drug crimes"

### Section 7: Default Strategy
If a query does not trigger any of the above specific rules, the system defaults to **vector_cypher**. This is considered the most robust all-around strategy as it combines semantic search with graph context.

## 4. The Three Retriever Strategies

Once the classifier selects a strategy, one of three specialized retrievers executes the task. These retrievers act as the "hands" of the system, interacting directly with the data.

### 1. Text2Cypher Retriever
This retriever uses a Large Language Model (LLM) to generate a database query from the natural language question.
- **Mechanism**: The question, the full Neo4j schema, and 40 "few-shot" examples are sent to the Groq Llama-3.3-70b model. The few-shot examples help the model understand the specific quirks of the POLE schema.
- **Execution**: The LLM produces a Cypher query which is then executed against the Neo4j database.
- **Self-Healing**: If the generated Cypher has a syntax error or returns no results, the system feeds the error back to the LLM and asks for a correction, allowing for up to 3 retry attempts. This dramatically improves the success rate for complex queries.
- **Best Use**: Precise counts, complex filters, and multi-hop relationship queries.

### 2. Vector Retriever
This is a pure semantic search strategy focused exclusively on the similarity of Crime nodes.
- **Mechanism**: It converts the question to a vector and retrieves the top-K most similar Crime nodes from the vector index.
- **Output**: It returns basic properties of the crimes (ID, type, date, outcome, charge, and notes).
- **Limitation**: It does not traverse the graph. It won't see which people or officers are connected to the crime unless that information was baked into the note.
- **Best Use**: Quick keyword lookups and very general queries where relationship context is not required.

### 3. VectorCypher Retriever (Hybrid)
This is the most powerful retriever in the system, combining the benefits of vector search with the structural depth of the graph. It represents the "best of both worlds."
- **Mechanism**: 
  1. It first performs a vector search to find relevant Crime nodes based on meaning.
  2. For every crime found, it automatically executes a Cypher "expansion" query.
  3. This expansion follows relationships to gather context: Persons (connected via PARTY_TO), Officers (who INVESTIGATED_BY), and Locations/Areas (where it OCCURRED_AT).
- **Result**: The LLM receives the crime details plus all its surrounding neighborhood in the graph. This provides the AI with a complete picture of the incident.
- **Best Use**: Exploratory questions like "tell me about..." or "describe the situation regarding..." where the user needs to know who was involved and where it happened.

## 5. Fallback Mechanism

Investigraph is designed to be resilient. If the primary retriever chosen by the classifier fails to find results, the system automatically tries an alternative strategy. This ensures that the user almost always gets an answer, even if the query was ambiguous.
- If **text2cypher** fails, it falls back to **vector_cypher**.
- If **vector** fails, it falls back to **vector_cypher**.
- If **vector_cypher** fails, it falls back to **text2cypher**.

This circular fallback logic ensures that the system exhausts its different modes of thinking before giving up.

## 6. How the Answer is Generated

The final output is generated by the Llama-3.3-70b-versatile model hosted on Groq. The system uses two different paths for this:

- **For Text2Cypher**: The pipeline receives raw data from Neo4j. It then constructs a prompt containing the original question and the retrieved data, asking the LLM to summarize it into a human-readable format.
- **For Vector and VectorCypher**: The `neo4j-graphrag` library handles the retrieval and answer generation in a single integrated flow. It retrieves the context, passes it to the LLM with a RAG template, and returns the final response.

### The RAG Answer Template
The RAG (Retrieval-Augmented Generation) prompt used by the system enforces several strict rules to ensure accuracy:
- **Accuracy**: Answer only using the provided context. If the information is not present in the database, the system is instructed to state that clearly rather than hallucinating.
- **Format**: Use bullet points for lists of incidents, people, or objects to improve readability.
- **Tone**: Professional and concise. Investigators need quick, clear answers without unnecessary fluff.
- **Insights**: Highlight any recurring patterns, such as multiple crimes of the same type in a specific area, or the same individual appearing in multiple incidents.

## 7. What the User Sees (Frontend)

The Investigraph interface is designed for transparency and trust. It provides the following components:
- **Natural Language Answer**: The primary response from the LLM, formatted for clarity.
- **Generated Cypher**: The exact code used to query the database. This allows technical users or database admins to verify the logic.
- **Retriever Context**: A collapsible section showing the raw data chunks (Crime properties or Graph traversals) that were fed to the LLM.
- **Strategy Trace**: An indicator showing which retriever was used (e.g., "text2cypher" or "vector_cypher -> text2cypher" if a fallback occurred).
- **Graph Visualization**: An interactive map of the nodes and relationships involved in the answer, allowing users to visually explore the connections.
- **Performance Metrics**: The time taken to classify, retrieve, and generate the answer, providing feedback on system efficiency.

## 8. Quick Architecture Summary

The following diagram illustrates the data flow from the moment a user submits a question to the final display. It highlights the central role of the classifier in directing the search.

```
Question → [Classifier] → selects retriever
                ↓
    ┌───────────┼───────────┐
    ↓           ↓           ↓
Text2Cypher   Vector    VectorCypher
    ↓           ↓           ↓
  Cypher      Vector     Vector+Graph
  Query       Search      Traversal
    ↓           ↓           ↓
  Neo4j       Neo4j       Neo4j
    ↓           ↓           ↓
    └───────────┼───────────┘
                ↓
        [LLM Answer Generation]
                ↓
        [Frontend Display]
```

## 9. Key Technical Facts

- **Large Language Model**: Groq Llama-3.3-70b-versatile (high speed and accuracy).
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions, local execution for privacy).
- **Vector Search**: Neo4j `crime_vector_index` using cosine similarity for semantic matching.
- **Database Engine**: Neo4j 5.23.
- **Database Name**: "pole" (Person, Object, Location, Event).
- **Schema Complexity**: 11 node labels, 17 relationship types.
- **Data Volume**: Approximately 28,000 Crime nodes.
- **Optimization**: 40 few-shot examples for high-accuracy Cypher generation.
- **Resilience**: 3-attempt self-healing retry logic for database queries.
- **Hybrid Approach**: Integration of semantic search with traditional graph traversals via VectorCypher.
- **Fallback Chain**: Automatic strategy switching to maximize answer rates.

This architecture ensures that Investigraph remains both precise enough for specific data lookups and flexible enough for broad investigative exploration.
