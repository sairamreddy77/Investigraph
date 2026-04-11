# Investigraph - Mermaid Diagrams Collection

> **All architecture diagrams in Mermaid format for easy rendering**
> Copy these into your presentation tool or use [Mermaid Live Editor](https://mermaid.live/)

---

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "User Layer"
        User[Investigator]
        Browser[Web Browser]
    end

    subgraph "Frontend Layer - React + TypeScript"
        UI[User Interface]
        QueryInput[Query Input Component]
        GraphViz[Graph Visualization]
        Results[Results Display]
        ChatSidebar[Investigation Workflows]
    end

    subgraph "Backend Layer - FastAPI + Python"
        API[REST API Endpoints]
        
        subgraph "GraphRAG Pipeline"
            Classifier[Question Classifier]
            T2C[Text2Cypher Retriever]
            VR[Vector Retriever]
            VCR[VectorCypher Retriever]
            Generator[GraphRAG Answer Generator]
        end

        subgraph "Core Components"
            LLM_W[Groq Llama-3.3-70b]
            Embedder[SentenceTransformer Embedder]
            SchemaIntrospector[Schema Introspector]
        end

        subgraph "Data Components"
            Examples[40 Curated Examples YAML]
            CaseStudies[Investigation Case Studies]
        end
    end

    subgraph "Data Layer"
        Neo4j[(Neo4j Graph Database)]
        VectorIndex[Crime Vector Index]
        POLE[POLE Knowledge Graph]
    end

    subgraph "External Services"
        LLM[LLM Providers]
        Groq[Groq LLaMA 3.3]
        OpenAI[OpenAI GPT-4o]
        Anthropic[Anthropic Claude]
        Google[Google Gemini]
    end

    User --> Browser
    Browser --> UI
    UI --> QueryInput
    UI --> GraphViz
    UI --> Results
    UI --> ChatSidebar

    QueryInput --> API
    API --> Classifier
    
    Classifier --> T2C
    Classifier --> VR
    Classifier --> VCR

    T2C --> LLM_W
    T2C --> Neo4j
    
    VR --> Embedder
    Embedder --> Neo4j
    
    VCR --> Embedder
    Embedder --> Neo4j
    
    Generator --> LLM_W
    
    Neo4j --> VectorIndex
    Neo4j --> POLE

    T2C -.-> LLM
    Generator -.-> LLM
    LLM --> Groq
    LLM --> OpenAI
    LLM --> Anthropic
    LLM --> Google

    ChatSidebar --> CaseStudies

    Results --> GraphViz
    T2C --> Results
    VR --> Results
    VCR --> Results

    style User fill:#e1f5ff
    style Browser fill:#e1f5ff
    style UI fill:#bbdefb
    style Classifier fill:#fff9c4
    style T2C fill:#c8e6c9
    style VR fill:#c8e6c9
    style VCR fill:#c8e6c9
    style Generator fill:#fff9c4
    style Neo4j fill:#ffccbc
    style LLM fill:#f8bbd0
```

---

## 2. GraphRAG Pipeline Sequence

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Classifier
    participant Retriever as Retriever (Selected)
    participant Neo4j
    participant LLM

    User->>Frontend: "Find drug crimes in area WN"
    Frontend->>API: POST /api/query

    API->>Classifier: classify(question)
    Classifier-->>API: returns strategy (text2cypher/vector/vector_cypher)

    API->>Retriever: search(question)
    
    loop Max 3 Attempts (for Text2Cypher)
        Retriever->>Neo4j: Execute Search/Query
        
        alt Results Found
            Neo4j-->>Retriever: Context items + Metadata
        else Syntax Error or Empty
            alt Attempt < 3
                Retriever->>Retriever: Self-heal retry / Regenerate
            else Attempt = 3
                Retriever-->>API: Empty results
            end
        end
    end

    alt Empty and Fallback exists
        API->>Retriever: try fallback retriever
        Retriever->>Neo4j: Execute fallback search
    end

    Retriever-->>API: Context + Graph Data
    API->>LLM: generate answer(question, context)
    LLM-->>API: natural language answer
    
    API-->>Frontend: JSON response
    Frontend->>Frontend: Render graph + answer
    Frontend-->>User: Visual results
```

---

## 3. Self-Healing Query Execution State Machine

```mermaid
stateDiagram-v2
    [*] --> GenerateCypher: User Question

    GenerateCypher --> ExecuteQuery: Initial Cypher

    ExecuteQuery --> CheckResult: Run on Neo4j

    CheckResult --> Success: Results Found
    CheckResult --> SyntaxError: Cypher Syntax Error
    CheckResult --> EmptyResults: Zero Results

    Success --> GenerateAnswer: Extract Graph Data

    SyntaxError --> CheckAttempts1: Attempt Count
    EmptyResults --> CheckAttempts2: Attempt Count

    CheckAttempts1 --> RegenerateSyntax: Attempt < 3
    CheckAttempts1 --> FailGracefully: Attempt = 3

    CheckAttempts2 --> RegenerateEmpty: Attempt < 3
    CheckAttempts2 --> FailGracefully: Attempt = 3

    RegenerateSyntax --> ExecuteQuery: Corrected Cypher\n+ Error Context
    RegenerateEmpty --> ExecuteQuery: Relaxed Filters\n+ Empty Context

    FailGracefully --> ReturnError: Error Message

    GenerateAnswer --> ReturnSuccess: Natural Language

    ReturnSuccess --> [*]
    ReturnError --> [*]
```

---

## 4. POLE Data Model

```mermaid
graph TB
    subgraph "POLE Framework"
        P[PERSON<br/>Individuals]
        O[OBJECT<br/>Physical Items]
        L[LOCATION<br/>Places]
        E[EVENT<br/>Incidents]
    end

    P ---|Involved In| E
    P ---|Located At| L
    P ---|Possesses| O
    O ---|Found At| L
    O ---|Used In| E
    E ---|Occurred At| L

    style P fill:#4fc3f7
    style O fill:#ffa726
    style L fill:#66bb6a
    style E fill:#ef5350
```

---

## 5. Neo4j POLE Schema

```mermaid
graph TB
    subgraph "Neo4j POLE Schema"
        subgraph "Node Types - 11"
            Person[Person]
            Crime[Crime]
            Location[Location]
            Vehicle[Vehicle]
            Object[Object]
            Officer[Officer]
            Phone[Phone]
            PhoneCall[PhoneCall]
            Email[Email]
            PostCode[PostCode]
            Area[Area]
        end

        subgraph "Relationships - 17"
            PARTY_TO[PARTY_TO]
            CURRENT_ADDRESS[CURRENT_ADDRESS]
            HAS_PHONE[HAS_PHONE]
            HAS_EMAIL[HAS_EMAIL]
            KNOWS[KNOWS]
            KNOWS_LW[KNOWS_LW]
            KNOWS_PHONE[KNOWS_PHONE]
            FAMILY_REL[FAMILY_REL]
            OCCURRED_AT[OCCURRED_AT]
            INVESTIGATED_BY[INVESTIGATED_BY]
            INVOLVED_IN[INVOLVED_IN]
            CALLER[CALLER]
            CALLED[CALLED]
            HAS_POSTCODE[HAS_POSTCODE]
            LOCATION_IN_AREA[LOCATION_IN_AREA]
            POSTCODE_IN_AREA[POSTCODE_IN_AREA]
            OFFICER_IN_AREA[OFFICER_IN_AREA]
        end
    end

    Person -->|PARTY_TO| Crime
    Person -->|CURRENT_ADDRESS| Location
    Person -->|HAS_PHONE| Phone
    Person -->|HAS_EMAIL| Email
    Person -->|KNOWS| Person
    Person -->|KNOWS_LW| Person
    Person -->|KNOWS_PHONE| Person
    Person -->|FAMILY_REL| Person

    Crime -->|OCCURRED_AT| Location
    Crime -->|INVESTIGATED_BY| Officer

    Vehicle -->|INVOLVED_IN| Crime
    Object -->|INVOLVED_IN| Crime

    Phone -->|CALLER| PhoneCall
    Phone -->|CALLED| PhoneCall

    Location -->|HAS_POSTCODE| PostCode
    Location -->|LOCATION_IN_AREA| Area
    PostCode -->|POSTCODE_IN_AREA| Area
    Officer -->|OFFICER_IN_AREA| Area

    style Person fill:#4fc3f7
    style Crime fill:#ef5350
    style Location fill:#66bb6a
    style Officer fill:#ffa726
```

---

## 6. Data Flow Architecture

```mermaid
flowchart TD
    Start([User Asks Question]) --> Input[Frontend: Query Input]
    Input --> Validate[Validate Question Length]
    Validate --> APICall[HTTP POST /api/query]

    APICall --> PipelineRun[GraphRAGPipeline.run]
    
    subgraph "Intelligent Retrieval"
        PipelineRun --> Classify[_classify_question]
        Classify --> Routes{Selected Retriever?}
        Routes -->|Text2Cypher| T2C[Execute Text2Cypher]
        Routes -->|Vector| VR[Execute Vector Search]
        Routes -->|VectorCypher| VCR[Execute VectorCypher]
        
        T2C --> CheckResults{Check results?}
        VR --> CheckResults
        VCR --> CheckResults
        
        CheckResults -->|Empty| Fallback[Try Fallback Retriever]
        Fallback --> ResultContext
        CheckResults -->|Data| ResultContext[Gather Context + Metadata]
    end

    ResultContext --> Generate[Generate Answer]
    Generate --> BuildResponse[Build response with retriever_used, cypher, context, graph_data]

    BuildResponse --> ReturnJSON[Return JSON to Frontend]

    ReturnJSON --> RenderUI[Render UI Components]
    RenderUI --> DisplayAnswer[Display Answer]
    RenderUI --> DisplayGraph[Display Graph]
    RenderUI --> DisplayCypher[Display Cypher]
    RenderUI --> DisplayMetadata[Display Metadata]

    DisplayAnswer --> End([User Sees Results])
    DisplayGraph --> End
    DisplayCypher --> End
    DisplayMetadata --> End

    style Start fill:#e1f5ff
    style Classify fill:#fff9c4
    style Routes fill:#fff9c4
    style Generate fill:#fff9c4
    style End fill:#c8e6c9
```

---

## 7. Module 1: Question Classification Flow

```mermaid
flowchart TD
    Question[User Question] --> Heuristic[Heuristic Classifier]

    subgraph "Classification Logic"
        Heuristic --> Structured{Structured Patterns?}
        Structured -->|Yes| T2C[Route to Text2Cypher]
        Structured -->|No| Area{Area/Filter Scoring?}
        
        Area -->|High Score| T2C
        Area -->|Low Score| Person{Person Patterns?}
        
        Person -->|Match| VCR[Route to VectorCypher]
        Person -->|No Match| Semantic{Semantic Patterns?}
        
        Semantic -->|Match| VR[Route to Vector]
        Semantic -->|No Match| StartsWith{Starts-with Check?}
        
        StartsWith -->|Match| T2C
        StartsWith -->|Default| VCR
    end

    subgraph "Context Sources"
        Schema[Graph Schema]
        Examples[40 Curated Examples]
    end

    T2C --> Search[Execute Retrieval Strategy]
    VR --> Search
    VCR --> Search

    style Question fill:#e1f5ff
    style Heuristic fill:#fff9c4
    style T2C fill:#c8e6c9
    style VR fill:#c8e6c9
    style VCR fill:#c8e6c9
```

---

## 8. Module 3: Answer Generation Flow

```mermaid
flowchart TD
    Input[Query Results] --> Analyze[Analyze Data]

    Analyze --> ResultType{Result Type?}

    ResultType --> Count[Count/Number]
    ResultType --> List[List of Items]
    ResultType --> Graph[Graph/Network]
    ResultType --> Empty[No Results]

    Count --> Format1[Format: '42 crimes found']
    List --> Format2[Format: 'John Smith, Sarah Jones, ...']
    Graph --> Format3[Format: 'Network of 5 people connected through...']
    Empty --> Format4[Format: 'No matching records found']

    Format1 --> Contextualize[Add Context]
    Format2 --> Contextualize
    Format3 --> Contextualize
    Format4 --> Contextualize

    Contextualize --> LLM[Generate Answer]
    LLM --> NaturalAnswer[Natural Language Answer]

    style Input fill:#e1f5ff
    style LLM fill:#fff9c4
    style NaturalAnswer fill:#c8e6c9
```

---

## 9. Module 4: Visualization Interface

```mermaid
flowchart TB
    subgraph "User Interface Layer"
        Input[Query Input Box]
        Examples[Example Questions]
        Workflows[Investigation Workflows]
    end

    subgraph "Results Display Layer"
        Answer[Natural Language Answer]
        Cypher[Generated Query]
        GraphViz[Graph Visualization]
        RawData[Raw Results Table]
    end

    subgraph "Interaction Layer"
        NodeClick[Click Node]
        Zoom[Zoom/Pan]
        Filter[Filter Results]
        Export[Export Graph]
    end

    Input --> Submit[Submit Question]
    Examples --> Input
    Workflows --> Input

    Submit --> Backend[API Call]
    Backend --> Parse[Parse Response]

    Parse --> Answer
    Parse --> Cypher
    Parse --> GraphViz
    Parse --> RawData

    GraphViz --> NodeClick
    GraphViz --> Zoom
    GraphViz --> Filter
    GraphViz --> Export

    style Input fill:#e1f5ff
    style Answer fill:#c8e6c9
    style GraphViz fill:#fff9c4
```

---

## 10. Technology Stack Overview

```mermaid
graph TB
    subgraph "Frontend Stack"
        React[React 18.2.0]
        TS[TypeScript 5.2.2]
        Vite[Vite 5.0.8]
        VisNetwork[vis-network 9.1.9]
        CSS[Modern CSS]
    end

    subgraph "Features"
        TypeSafety[Type Safety]
        HMR[Hot Module Reload]
        GraphRender[Graph Rendering]
        DarkMode[Dark/Light Mode]
        Responsive[Responsive Design]
    end

    React --> TypeSafety
    TS --> TypeSafety
    Vite --> HMR
    VisNetwork --> GraphRender
    CSS --> DarkMode
    CSS --> Responsive

    style React fill:#61dafb
    style TS fill:#3178c6
    style Vite fill:#646cff
```

---

## 11. Backend Architecture

```mermaid
graph TB
    subgraph "Backend Stack"
        FastAPI[FastAPI - Web Framework]
        Pydantic[Pydantic - Data Validation]
        NeoGraphRAG[neo4j-graphrag - RAG Orchestration]
        Neo4jDriver[Neo4j Python Driver]
        Python[Python 3.10+]
    end

    subgraph "Core Features"
        AsyncIO[Async/Await Support]
        AutoDocs[Auto-generated API Docs]
        DataValidation[Request/Response Validation]
        LLMAbstraction[Multi-provider LLM Support]
        GraphAccess[Graph Database Access]
    end

    FastAPI --> AsyncIO
    FastAPI --> AutoDocs
    Pydantic --> DataValidation
    NeoGraphRAG --> LLMAbstraction
    Neo4jDriver --> GraphAccess

    style FastAPI fill:#009688
    style NeoGraphRAG fill:#1c3c3c
    style Neo4jDriver fill:#008cc1
```

---

## 12. Docker Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Environment"
        subgraph "Frontend Container"
            NginxContainer[Nginx Server]
            ReactBuild[React Production Build]
        end

        subgraph "Backend Container"
            UvicornContainer[Uvicorn ASGI Server]
            FastAPIApp[FastAPI Application]
            PythonEnv[Python 3.10 Environment]
        end

        subgraph "Database"
            Neo4jContainer[Neo4j Container/Cloud]
        end

        subgraph "External"
            LLMServices[LLM Provider APIs]
        end
    end

    NginxContainer --> ReactBuild
    NginxContainer -->|Proxy /api| UvicornContainer
    UvicornContainer --> FastAPIApp
    FastAPIApp --> PythonEnv
    FastAPIApp --> Neo4jContainer
    FastAPIApp --> LLMServices

    style NginxContainer fill:#009688
    style UvicornContainer fill:#ff9800
    style Neo4jContainer fill:#008cc1
    style LLMServices fill:#e91e63
```

---

## 13. Complete Module Integration Flow

```mermaid
sequenceDiagram
    actor Investigator
    participant UI as Frontend UI
    participant M1 as Module 1: Classification
    participant M2 as Module 2: Retrieval
    participant M3 as Module 3: Generation
    participant M4 as Module 4: Visualization
    participant DB as Neo4j + Vector Index

    Investigator->>UI: "Find drug crimes in WN"

    UI->>M1: question
    Note over M1: Heuristic classification
    M1->>M1: Check keywords, filters, patterns
    M1-->>UI: Route to Text2Cypher (area filter detected)

    UI->>M2: Text2Cypher.search(question)
    M2->>DB: Generate Cypher + Execute
    
    alt Syntax Error
        DB-->>M2: Error message
        M2->>M2: Self-heal retry
        M2->>DB: Execute corrected query
    end

    DB-->>M2: Context items + metadata
    M2-->>UI: Retrieval results

    UI->>M3: Generate answer from context
    Note over M3: Groq Llama-3.3-70b
    M3->>M3: Build grounded prompt
    M3-->>UI: Grounded NL answer

    UI->>M4: Extract graph data
    M4->>M4: Parse entities & relationships
    M4-->>UI: Interactive graph

    UI-->>Investigator: Answer + Graph + Cypher + Metadata
```

---

## 14. Caching Strategy

```mermaid
graph LR
    subgraph "Cached Components"
        SchemaCache[Schema Cache]
        ExamplesCache[Examples Cache]
        Neo4jPool[Connection Pool]
    end

    subgraph "Runtime"
        FirstRequest[First Request]
        SubsequentRequests[Subsequent Requests]
    end

    FirstRequest --> LoadSchema[Load Schema from Neo4j]
    FirstRequest --> LoadExamples[Load Examples from YAML]
    FirstRequest --> CreatePool[Create Connection Pool]

    LoadSchema --> SchemaCache
    LoadExamples --> ExamplesCache
    CreatePool --> Neo4jPool

    SubsequentRequests --> SchemaCache
    SubsequentRequests --> ExamplesCache
    SubsequentRequests --> Neo4jPool

    style SchemaCache fill:#4caf50
    style ExamplesCache fill:#4caf50
    style Neo4jPool fill:#4caf50
```

---

## How to Use These Diagrams

### Option 1: Mermaid Live Editor
1. Go to [https://mermaid.live/](https://mermaid.live/)
2. Copy any diagram code above
3. Paste into the editor
4. Export as PNG/SVG for your presentation

### Option 2: VS Code Extension
1. Install "Markdown Preview Mermaid Support" extension
2. Open this file in VS Code
3. Preview renders diagrams automatically
4. Right-click diagram → Copy or Export

### Option 3: Direct Integration
Many presentation tools now support Mermaid:
- Notion
- Obsidian
- GitLab/GitHub README
- Slidev
- Reveal.js

### Option 4: Online Rendering
Use services like:
- [Mermaid Chart](https://www.mermaidchart.com/)
- [Kroki](https://kroki.io/)
- [Excalidraw](https://excalidraw.com/) (for hand-drawn style)

---

## Diagram Color Scheme

For consistency across all diagrams:

| Color | Hex Code | Usage |
|-------|----------|-------|
| Light Blue | `#e1f5ff` | User inputs, starting points |
| Yellow | `#fff9c4` | AI/LLM operations, processing |
| Light Green | `#c8e6c9` | Success states, outputs |
| Light Red | `#ffccbc` | Database operations |
| Pink | `#f8bbd0` | External services |
| Blue (Person) | `#4fc3f7` | Person nodes in POLE |
| Red (Crime) | `#ef5350` | Crime/Event nodes |
| Green (Location) | `#66bb6a` | Location nodes |
| Orange (Officer) | `#ffa726` | Officer/Object nodes |

---

## Tips for Presentation

1. **Start Simple**: Show POLE model first, then build complexity
2. **Interactive Flow**: Use sequence diagrams to show user journey
3. **Technical Deep-Dive**: State machines for error handling details
4. **Context Matters**: Always explain what each diagram shows before displaying it
5. **Zoom In**: For complex diagrams, show sections individually first

Good luck with your presentation! 🎯
