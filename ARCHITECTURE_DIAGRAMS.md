# Architecture Diagrams for Portfolio

## 1. Complete System Architecture

```mermaid
graph TB
    subgraph Frontend["🖥️ Frontend Layer - React + TypeScript"]
        UI[User Interface]
        ChatInput[Chat Input Component]
        MessageList[Message Display]
        Charts[Interactive Plotly Charts]
        AgentMonitor[Real-time Agent Monitor]
    end
    
    subgraph Backend["⚙️ Backend Layer - FastAPI + Python"]
        API[REST API Routes]
        DatasetMgr[Dataset Manager]
        
        subgraph Orchestration["🤖 Multi-Agent Orchestration"]
            Planner[🧭 Planner Agent<br/>Question Classifier]
            
            subgraph DescriptivePath["📊 Descriptive Analytics Path"]
                SQL1[💾 Text-to-SQL Agent<br/>Query Generator]
                Viz1[📊 Visualization Agent<br/>Chart Generator]
            end
            
            subgraph CausalPath["🔬 Causal Analytics Path"]
                Hypo[🔬 Hypothesis Agent<br/>Hypothesis Generator]
                SQL2[💾 Text-to-SQL Agent<br/>Per Hypothesis]
                Viz2[📊 Visualization Agent<br/>Per Hypothesis]
                Stats[📈 Statistical Agent<br/>Chi-Square, t-test, ANOVA]
            end
        end
    end
    
    subgraph Data["💾 Data Layer"]
        DB[(PostgreSQL<br/>Multi-Schema)]
        HRSchema[HR Dataset Schema]
        SalesSchema[Sales Dataset Schema]
    end
    
    subgraph AI["🤖 AI/LLM Layer"]
        Azure[Azure OpenAI<br/>GPT-4]
    end
    
    UI --> ChatInput
    ChatInput --> API
    API --> DatasetMgr
    DatasetMgr --> Planner
    
    Planner -->|WHAT Questions| SQL1
    Planner -->|WHY Questions| Hypo
    
    SQL1 --> DB
    DB --> SQL1
    SQL1 --> Viz1
    Viz1 --> MessageList
    
    Hypo --> SQL2
    SQL2 --> DB
    DB --> SQL2
    SQL2 --> Viz2
    Viz2 --> Stats
    Stats --> MessageList
    
    DB --> HRSchema
    DB --> SalesSchema
    
    Planner -.->|LLM Calls| Azure
    SQL1 -.->|LLM Calls| Azure
    SQL2 -.->|LLM Calls| Azure
    Viz1 -.->|LLM Calls| Azure
    Viz2 -.->|LLM Calls| Azure
    Hypo -.->|LLM Calls| Azure
    Stats -.->|LLM Calls| Azure
    
    MessageList --> Charts
    API --> AgentMonitor
    
    style Frontend fill:#e3f2fd
    style Backend fill:#f3e5f5
    style Orchestration fill:#fff3e0
    style Data fill:#e8f5e9
    style AI fill:#fce4ec
    style DescriptivePath fill:#e1f5fe
    style CausalPath fill:#fff9c4
```

---

## 2. Simplified Agent Flow

```mermaid
flowchart TD
    User[👤 User Question] --> Planner[🧭 Planner Agent]
    
    Planner -->|Descriptive<br/>WHAT| DescPath[Descriptive Path]
    Planner -->|Causal<br/>WHY| CausalPath[Causal Path]
    
    DescPath --> SQL1[💾 Text-to-SQL]
    SQL1 --> Viz1[📊 Visualization]
    Viz1 --> Result1[📋 Results]
    
    CausalPath --> Hypo[🔬 Hypothesis Gen]
    Hypo --> SQL2[💾 Text-to-SQL<br/>per hypothesis]
    SQL2 --> Viz2[📊 Visualization<br/>per hypothesis]
    Viz2 --> Stats[📈 Statistical Tests]
    Stats --> AI[💡 AI Interpretation]
    AI --> Result2[📋 Comprehensive Report]
    
    style Planner fill:#90caf9
    style DescPath fill:#a5d6a7
    style CausalPath fill:#ffcc80
    style Result1 fill:#ce93d8
    style Result2 fill:#ce93d8
```

---

## 3. Technology Stack Layers

```mermaid
graph LR
    subgraph Layer1["Frontend"]
        React[React]
        TS[TypeScript]
        Vite[Vite]
        Tailwind[TailwindCSS]
    end
    
    subgraph Layer2["Backend"]
        FastAPI[FastAPI]
        Python[Python 3.10+]
        LangChain[LangChain]
        Pydantic[Pydantic]
    end
    
    subgraph Layer3["Agents"]
        Multi[Multi-Agent<br/>Orchestration]
        Async[Async/Await<br/>Patterns]
    end
    
    subgraph Layer4["AI/ML"]
        AzureAI[Azure OpenAI]
        GPT4[GPT-4]
        Pandas[Pandas]
        SciPy[SciPy]
    end
    
    subgraph Layer5["Data & Viz"]
        Postgres[(PostgreSQL)]
        Plotly[Plotly]
        Stats[Statistical<br/>Computing]
    end
    
    Layer1 --> Layer2
    Layer2 --> Layer3
    Layer3 --> Layer4
    Layer3 --> Layer5
    
    style Layer1 fill:#e3f2fd
    style Layer2 fill:#f3e5f5
    style Layer3 fill:#fff3e0
    style Layer4 fill:#fce4ec
    style Layer5 fill:#e8f5e9
```

---

## 4. Data Flow Sequence

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Planner
    participant SQL as Text-to-SQL
    participant DB as PostgreSQL
    participant Viz as Visualization
    participant Hypo as Hypothesis
    participant Stats as Statistical
    participant LLM as Azure OpenAI
    
    User->>Frontend: Ask question
    Frontend->>API: POST /api/analyze
    API->>Planner: Route question
    Planner->>LLM: Classify question type
    LLM-->>Planner: WHAT/WHY classification
    
    alt Descriptive (WHAT)
        Planner->>SQL: Generate query
        SQL->>LLM: Create SQL
        LLM-->>SQL: PostgreSQL query
        SQL->>DB: Execute query
        DB-->>SQL: Return data
        SQL->>Viz: Generate chart
        Viz->>LLM: Determine chart type
        LLM-->>Viz: Chart config
        Viz-->>Frontend: Display results
    else Causal (WHY)
        Planner->>Hypo: Generate hypotheses
        Hypo->>LLM: Create testable hypotheses
        LLM-->>Hypo: 3-5 hypotheses
        loop For each hypothesis
            Hypo->>SQL: Generate query
            SQL->>DB: Execute query
            DB-->>SQL: Return data
            SQL->>Viz: Create chart
            Viz->>Stats: Perform test
            Stats->>Stats: Chi-Square/t-test/ANOVA
        end
        Stats->>LLM: Interpret results
        LLM-->>Stats: Business insights
        Stats-->>Frontend: Comprehensive report
    end
    
    Frontend-->>User: Display analysis
```

---

## 5. Agent Responsibilities

```mermaid
mindmap
  root((Multi-Agent<br/>Analytics<br/>System))
    🧭 Planner
      Question Classification
      Route Selection
      Context Management
    💾 Text-to-SQL
      Natural Language Understanding
      SQL Generation
      Query Validation
      Injection Prevention
    📊 Visualization
      Chart Type Selection
      Plotly Configuration
      Data Formatting
      Interactive Features
    🔬 Hypothesis
      Hypothesis Generation
      Test Selection
      Null/Alternative Formulation
    📈 Statistical
      Chi-Square Test
      t-Test
      ANOVA
      Correlation Analysis
      Effect Size Calculation
      AI Interpretation
```

---

## 6. Security & Quality Layers

```mermaid
graph TD
    Input[User Input] --> Validation[Input Validation<br/>Pydantic Models]
    Validation --> Auth[Authentication<br/>CORS Configuration]
    Auth --> Routing[API Routing<br/>FastAPI]
    
    Routing --> SQLValidation[SQL Validation<br/>Injection Prevention]
    SQLValidation --> QueryExec[Query Execution<br/>Parameterized Queries]
    
    Routing --> ErrorHandling[Error Handling<br/>Try-Catch Blocks]
    ErrorHandling --> Logging[Logging<br/>Activity Tracking]
    Logging --> Monitoring[Real-time Monitoring<br/>Agent Activity]
    
    QueryExec --> Results[Results]
    Monitoring --> Results
    
    style Validation fill:#c8e6c9
    style Auth fill:#c8e6c9
    style SQLValidation fill:#fff9c4
    style ErrorHandling fill:#ffccbc
    style Logging fill:#b3e5fc
    style Monitoring fill:#b3e5fc
```

---

## How to Use These Diagrams

### For GitHub/Documentation
- These Mermaid diagrams render automatically on GitHub
- Copy the diagram code blocks to your README.md or documentation

### For Presentations/Portfolio
1. **Render to Image**: Use [Mermaid Live Editor](https://mermaid.live) to convert to PNG/SVG
2. **Copy the image** to your portfolio website
3. **Or use a Mermaid renderer** in your React app with `react-mermaid`

### Recommended Uses
- **Diagram 1**: Complete overview for technical documentation
- **Diagram 2**: Simplified flow for portfolio/presentations
- **Diagram 3**: Technology stack visualization
- **Diagram 4**: Sequence diagram for detailed workflow
- **Diagram 5**: Agent responsibilities mindmap
- **Diagram 6**: Security architecture for interviews

---

## Converting to Images

### Online Tools
1. [Mermaid Live Editor](https://mermaid.live) - Copy diagram, export as PNG/SVG
2. [Excalidraw](https://excalidraw.com) - Redraw for hand-drawn style

### CLI Tools
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Convert diagram to image
mmdc -i diagram.mmd -o diagram.png -t dark -b transparent
```

### In React App
```bash
npm install react-mermaid2

# Or use recharts/d3 for custom interactive diagrams
```
