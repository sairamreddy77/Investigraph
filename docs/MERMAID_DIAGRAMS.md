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
        Pipeline[Query Pipeline Orchestrator]

        subgraph "AI Components"
            CypherGen[Cypher Generator LLM]
            AnswerGen[Answer Generator LLM]
        end

        subgraph "Core Components"
            SchemaIntrospector[Schema Introspector]
            FewShotLoader[Few-Shot Example Loader]
            QueryExecutor[Query Executor with Retry]
        end

        subgraph "Data Components"
            Examples[24 Curated Examples YAML]
            CaseStudies[Investigation Case Studies]
        end
    end

    subgraph "Data Layer"
        Neo4j[(Neo4j Graph Database)]
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
    API --> Pipeline

    Pipeline --> CypherGen
    Pipeline --> QueryExecutor
    Pipeline --> AnswerGen

    CypherGen --> SchemaIntrospector
    CypherGen --> FewShotLoader
    FewShotLoader --> Examples

    QueryExecutor --> Neo4j
    Neo4j --> POLE

    CypherGen -.-> LLM
    AnswerGen -.-> LLM
    LLM --> Groq
    LLM --> OpenAI
    LLM --> Anthropic
    LLM --> Google

    ChatSidebar --> CaseStudies

    Results --> GraphViz
    QueryExecutor --> Results

    style User fill:#e1f5ff
    style Browser fill:#e1f5ff
    style UI fill:#bbdefb
    style Pipeline fill:#fff9c4
    style CypherGen fill:#c8e6c9
    style AnswerGen fill:#c8e6c9
    style Neo4j fill:#ffccbc
    style LLM fill:#f8bbd0
```

---

## 2. 3-Step Query Pipeline Sequence

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Pipeline
    participant CypherGen
    participant Executor
    participant Neo4j
    participant AnswerGen

    User->>Frontend: "Find drug crimes in area WN"
    Frontend->>API: POST /api/query

    API->>Pipeline: run(question)

    Note over Pipeline: Step 1: Generate Cypher
    Pipeline->>CypherGen: generate(question)
    CypherGen->>CypherGen: Load schema context
    CypherGen->>CypherGen: Load 24 examples
    CypherGen->>CypherGen: Call LLM
    CypherGen-->>Pipeline: Cypher query

    Note over Pipeline: Step 2: Execute with Retry
    Pipeline->>Executor: execute(cypher, question)

    loop Max 3 Attempts
        Executor->>Neo4j: Run Cypher query

        alt Success with results
            Neo4j-->>Executor: Results + Graph data
        else Syntax Error
            Neo4j-->>Executor: Error message
            Executor->>CypherGen: Regenerate with error context
            CypherGen-->>Executor: Corrected query
        else Empty Results
            Neo4j-->>Executor: []
            Executor->>CypherGen: Regenerate with relaxed filters
            CypherGen-->>Executor: Modified query
        end
    end

    Executor-->>Pipeline: Results + metadata

    Note over Pipeline: Step 3: Generate Answer
    Pipeline->>AnswerGen: generate(question, cypher, results)
    AnswerGen->>AnswerGen: Call LLM
    AnswerGen-->>Pipeline: Natural language answer

    Pipeline-->>API: Complete response
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
            AREA[AREA]
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
    Location -->|LOCATION_IN_AREA| AREA
    PostCode -->|POSTCODE_IN_AREA| AREA
    Officer -->|OFFICER_IN_AREA| AREA

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

    APICall --> Middleware[Backend Middleware - Logging]
    Middleware --> PipelineInit[Initialize Pipeline]

    PipelineInit --> Step1{Step 1: Generate Cypher}
    Step1 --> LoadSchema[Load Cached Schema]
    Step1 --> LoadExamples[Load 24 Examples]
    Step1 --> CallLLM1[Call LLM with Context]
    CallLLM1 --> Cypher[Generated Cypher Query]

    Cypher --> Step2{Step 2: Execute Query}
    Step2 --> Try[Attempt 1]

    Try --> Neo4jCall[Execute on Neo4j]
    Neo4jCall --> CheckResult{Check Result}

    CheckResult -->|Success with Data| ExtractGraph[Extract Graph Data]
    CheckResult -->|Syntax Error| ErrorContext1[Build Error Context]
    CheckResult -->|Empty Results| ErrorContext2[Build Empty Context]

    ErrorContext1 --> Retry1{Attempt < 3?}
    ErrorContext2 --> Retry1

    Retry1 -->|Yes| Regenerate[Regenerate Cypher]
    Regenerate --> Try

    Retry1 -->|No| FailGracefully[Return Error Message]

    ExtractGraph --> Step3{Step 3: Generate Answer}
    FailGracefully --> Step3

    Step3 --> CallLLM2[Call LLM with Results]
    CallLLM2 --> NLAnswer[Natural Language Answer]

    NLAnswer --> BuildResponse[Build Response Object]
    BuildResponse --> ReturnJSON[Return JSON to Frontend]

    ReturnJSON --> RenderUI[Render UI Components]
    RenderUI --> DisplayAnswer[Display Answer]
    RenderUI --> DisplayGraph[Display Graph]
    RenderUI --> DisplayCypher[Display Cypher]

    DisplayAnswer --> End([User Sees Results])
    DisplayGraph --> End
    DisplayCypher --> End

    style Start fill:#e1f5ff
    style Step1 fill:#fff9c4
    style Step2 fill:#fff9c4
    style Step3 fill:#fff9c4
    style End fill:#c8e6c9
```

---

## 7. Module 1: Query Generation Flow

```mermaid
flowchart LR
    Question[User Question] --> Context[Build Context]

    Context --> Schema[Graph Schema]
    Context --> Examples[24 Training Examples]
    Context --> Properties[Known Property Values]

    Schema --> Prompt[LLM Prompt]
    Examples --> Prompt
    Properties --> Prompt
    Question --> Prompt

    Prompt --> LLM[Large Language Model]
    LLM --> Cypher[Cypher Query]

    style Question fill:#e1f5ff
    style LLM fill:#fff9c4
    style Cypher fill:#c8e6c9
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
        LangChain[LangChain - LLM Orchestration]
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
    LangChain --> LLMAbstraction
    Neo4jDriver --> GraphAccess

    style FastAPI fill:#009688
    style LangChain fill:#1c3c3c
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
    participant M1 as Module 1: Query Gen
    participant M2 as Module 2: Execution
    participant M3 as Module 3: Answer Gen
    participant M4 as Module 4: Visualization
    participant DB as Neo4j Database

    Investigator->>UI: "Find drug crimes in WN"

    UI->>M1: question
    Note over M1: Load schema + examples
    M1->>M1: Build LLM context
    M1->>M1: Generate Cypher
    M1-->>UI: Cypher query

    UI->>M2: Execute query
    M2->>DB: Run Cypher

    alt Syntax Error
        DB-->>M2: Error message
        M2->>M1: Regenerate with error
        M1-->>M2: Corrected query
        M2->>DB: Retry
    end

    DB-->>M2: Results + Graph data
    M2-->>UI: Execution results

    UI->>M3: Generate answer
    Note over M3: Summarize results
    M3->>M3: Call LLM
    M3-->>UI: Natural language answer

    UI->>M4: Render visualization
    M4->>M4: Parse nodes & edges
    M4->>M4: Apply graph layout
    M4-->>UI: Interactive graph

    UI-->>Investigator: Display answer + graph

    Investigator->>M4: Click node to inspect
    M4-->>Investigator: Show node details
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
