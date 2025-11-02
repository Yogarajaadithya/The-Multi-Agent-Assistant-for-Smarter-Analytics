# Multi-Agent System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                    (Frontend / API Client)                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP Request
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND                               │
│                     (app/main.py + routes.py)                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
           POST /api/analyze    POST /api/analyze/what
                    │             POST /api/analyze/why
                    │                 │
                    ↓                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     MULTI-AGENT SYSTEM                               │
│                  (app/services/multi_agent_system.py)                │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    PLANNER AGENT                              │  │
│  │            (app/services/planner_agent.py)                    │  │
│  │                                                               │  │
│  │  Analyzes question → Classifies as WHAT or WHY               │  │
│  │  Returns: {question_type, reasoning, agents_to_call}         │  │
│  └─────────────────────┬────────────────────────────────────────┘  │
│                        │                                            │
│          ┌─────────────┴──────────────┐                            │
│          │                            │                            │
│    WHAT Question?              WHY Question?                       │
│          │                            │                            │
│          ↓                            ↓                            │
│  ┌───────────────┐           ┌───────────────────┐                │
│  │  TEXT-TO-SQL  │           │  HYPOTHESIS       │                │
│  │     AGENT     │           │    AGENT          │                │
│  │               │           │                   │                │
│  │ • Parse NL    │           │ • Generate 3-5    │                │
│  │ • Generate    │           │   testable        │                │
│  │   SQL         │           │   hypotheses      │                │
│  │ • Execute     │           │ • Identify vars   │                │
│  │   query       │           │ • Recommend tests │                │
│  │ • Return DF   │           │                   │                │
│  └───────┬───────┘           └────────┬──────────┘                │
│          │                            │                            │
│          ↓                            ↓                            │
│  ┌───────────────┐           ┌───────────────────┐                │
│  │ VISUALIZATION │           │  STATISTICAL      │                │
│  │    AGENT      │           │  TESTING AGENT    │                │
│  │               │           │                   │                │
│  │ • Analyze DF  │           │ • Chi-square test │                │
│  │ • Generate    │           │ • T-test          │                │
│  │   Plotly code │           │ • ANOVA           │                │
│  │ • Create      │           │ • Correlation     │                │
│  │   interactive │           │ • Effect sizes    │                │
│  │   chart       │           │                   │                │
│  └───────────────┘           └───────────────────┘                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                               │
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │  LM STUDIO   │    │  PostgreSQL  │    │    Plotly    │         │
│  │   (Local)    │    │   Database   │    │  Rendering   │         │
│  │              │    │              │    │              │         │
│  │ • IBM Granite│    │ • HR Data    │    │ • Interactive│         │
│  │   3.2 8B     │    │ • 1,470 rows │    │   Charts     │         │
│  │ • Port: 1234 │    │ • 35 columns │    │ • JSON export│         │
│  └──────────────┘    └──────────────┘    └──────────────┘         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Agent Interaction Flow

### WHAT Question Flow

```
User: "What is the attrition rate by department?"
  │
  ↓
[Planner Agent]
  │ Classification: WHAT (descriptive)
  │ Reasoning: "Asking for facts and distribution"
  │ Agents: ["text_to_sql", "visualization"]
  ↓
[Text-to-SQL Agent]
  │ Parse: "attrition rate" + "by department"
  │ Generate SQL:
  │   SELECT department,
  │          COUNT(*) as total,
  │          ROUND((COUNT(CASE WHEN attrition='Yes' THEN 1 END)::numeric 
  │                / COUNT(*)::numeric) * 100, 2) as attrition_rate
  │   FROM employee_attrition
  │   GROUP BY department
  │   ORDER BY attrition_rate DESC
  │ Execute → DataFrame (3 rows × 3 columns)
  ↓
[Visualization Agent]
  │ Analyze DataFrame:
  │   - 1 categorical column (department)
  │   - 1 numerical column (attrition_rate)
  │   - 3 rows (small dataset)
  │ Select: Bar Chart
  │ Generate Plotly code:
  │   fig = px.bar(df, x='department', y='attrition_rate',
  │                title='Attrition Rate by Department')
  │ Execute → Interactive Plotly Chart
  ↓
Response:
{
  "success": true,
  "question_type": "WHAT",
  "sql": "SELECT department...",
  "data": [...],
  "rows": 3,
  "visualization": { "plotly_json": {...} }
}
```

---

### WHY Question Flow

```
User: "Why do employees leave the company?"
  │
  ↓
[Planner Agent]
  │ Classification: WHY (causal)
  │ Reasoning: "Asking for causes and explanations"
  │ Agents: ["hypothesis", "statistical_testing"]
  ↓
[Hypothesis Agent]
  │ Context: HR attrition dataset
  │ Generate 3 hypotheses:
  │
  │ Hypothesis 1:
  │   H0: No relationship between overtime and attrition
  │   H1: Overtime is associated with higher attrition
  │   Variables: overtime (cat) vs attrition (cat)
  │   Test: Chi-square
  │
  │ Hypothesis 2:
  │   H0: Job satisfaction has no effect on attrition
  │   H1: Lower satisfaction leads to higher attrition
  │   Variables: jobsatisfaction (num) vs attrition (cat)
  │   Test: T-test or ANOVA
  │
  │ Hypothesis 3:
  │   H0: Years at company not correlated with attrition
  │   H1: Fewer years at company = higher attrition
  │   Variables: yearsatcompany (num) vs attrition (cat)
  │   Test: T-test
  ↓
[Statistical Testing Agent]
  │ Load data: 1,470 employees
  │
  │ Test Hypothesis 1: Chi-square test
  │   Contingency Table:
  │            Yes    No
  │   Overtime 127   289
  │   No OT    110  1,054
  │   Chi² = 25.43, p < 0.001
  │   Cramér's V = 0.132 (weak association)
  │   → Reject H0: Overtime IS associated with attrition
  │
  │ Test Hypothesis 2: ANOVA (4 satisfaction levels)
  │   Group 1 (Low):  Mean attrition = 23.1%
  │   Group 2:        Mean attrition = 18.4%
  │   Group 3:        Mean attrition = 15.2%
  │   Group 4 (High): Mean attrition = 11.3%
  │   F = 8.45, p = 0.0002
  │   η² = 0.067 (medium effect)
  │   → Reject H0: Job satisfaction DOES affect attrition
  │
  │ Test Hypothesis 3: T-test
  │   Left company:    Mean = 5.1 years
  │   Stayed:          Mean = 7.4 years
  │   t = -6.32, p < 0.001
  │   Cohen's d = 0.54 (medium effect)
  │   → Reject H0: Years at company IS related to attrition
  ↓
Response:
{
  "success": true,
  "question_type": "WHY",
  "hypotheses": { ... },
  "statistical_results": {
    "summary": { "total_hypotheses": 3 },
    "hypothesis_results": [
      {
        "statistical_results": {
          "test_name": "Chi-Square Test",
          "p_value": 0.0001,
          "interpretation": "Highly significant..."
        }
      },
      ...
    ]
  }
}
```

---

## Data Flow Diagram

```
┌──────────┐
│  User Q  │
└────┬─────┘
     │
     ↓
┌─────────────────┐
│  Planner Agent  │ ←── Classify WHAT/WHY
└────┬────────────┘
     │
     ├──→ WHAT Path:
     │   ┌──────────────────┐
     │   │ Text-to-SQL      │
     │   │   ↓ SQL Query    │
     │   │ PostgreSQL DB    │
     │   │   ↓ DataFrame    │
     │   │ Visualization    │
     │   │   ↓ Plotly Chart │
     │   └──────────────────┘
     │
     └──→ WHY Path:
         ┌──────────────────┐
         │ Hypothesis Gen   │
         │   ↓ 3 Hypotheses │
         │ Stats Testing    │
         │   ↓ Chi²/t/ANOVA │
         │ Results + Effect │
         └──────────────────┘
         ↓
    Response JSON
```

---

## Component Details

### 1. Planner Agent
**File:** `app/services/planner_agent.py`

**Inputs:**
- User question (string)

**Outputs:**
```json
{
  "question_type": "WHAT" | "WHY",
  "reasoning": "Why this classification",
  "agents_to_call": ["agent1", "agent2"],
  "analysis_approach": "Description"
}
```

**Logic:**
- Uses LLM to analyze question semantics
- Keywords: "what", "how many" → WHAT
- Keywords: "why", "cause", "affect" → WHY
- Defaults to WHAT if ambiguous

---

### 2. Text-to-SQL Agent
**File:** `app/services/TTS_vis.py` (TextToSQLAgent class)

**Inputs:**
- Natural language question

**Outputs:**
```json
{
  "success": true,
  "sql": "SELECT...",
  "data": pandas.DataFrame,
  "rows": 150,
  "columns": ["col1", "col2"]
}
```

**Features:**
- Schema-aware SQL generation
- Safety validation (SELECT only)
- Handles percentage calculations correctly
- Automatic column name normalization

---

### 3. Visualization Agent
**File:** `app/services/TTS_vis.py` (VisualizationAgent class)

**Inputs:**
- pandas DataFrame
- Original question (for context)

**Outputs:**
```json
{
  "success": true,
  "code": "Python code",
  "figure": plotly.graph_objects.Figure
}
```

**Features:**
- Automatic chart type selection
- Handles single-value results (gauge charts)
- Fallback mechanism if generation fails
- Exports to PNG/HTML/SVG

---

### 4. Hypothesis Agent
**File:** `app/services/hypothesis_stats_agent.py` (HypothesisAgent class)

**Inputs:**
- Research question
- Number of hypotheses to generate

**Outputs:**
```json
{
  "hypotheses": [
    {
      "hypothesis_id": 1,
      "null_hypothesis": "H0: ...",
      "alternative_hypothesis": "H1: ...",
      "variable_1": "var1",
      "variable_2": "var2",
      "recommended_test": "chi-square"
    }
  ]
}
```

**Logic:**
- Uses LLM with HR domain context
- Ensures bivariate hypotheses (2 variables)
- Recommends appropriate statistical test
- Validates variables exist in dataset

---

### 5. Statistical Testing Agent
**File:** `app/services/hypothesis_stats_agent.py` (StatsAgent class)

**Inputs:**
- List of hypotheses
- HR employee DataFrame

**Outputs:**
```json
{
  "summary": {
    "total_hypotheses": 3
  },
  "hypothesis_results": [
    {
      "statistical_results": {
        "test_name": "Chi-Square Test",
        "p_value": 0.0001,
        "chi2_statistic": 25.43,
        "cramers_v": 0.132,
        "interpretation": "Highly significant..."
      }
    }
  ]
}
```

**Tests Supported:**
| Variable 1 | Variable 2 | Test | Effect Size |
|-----------|-----------|------|-------------|
| Cat (2)   | Num       | T-test | Cohen's d |
| Cat (3+)  | Num       | ANOVA | Eta² |
| Cat       | Cat       | Chi² | Cramér's V |
| Num       | Num       | Pearson/Spearman | R² |

---

## Technology Stack

### Backend Framework
- **FastAPI** - Modern async Python web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation

### AI/ML
- **LangChain** - LLM orchestration
- **LM Studio** - Local LLM (IBM Granite 3.2 8B)
- **OpenAI SDK** - LLM client

### Data & Analytics
- **pandas** - Data manipulation
- **SQLAlchemy** - Database ORM
- **psycopg2** - PostgreSQL driver
- **scipy** - Statistical tests
- **Plotly** - Interactive visualizations

### Database
- **PostgreSQL** - Relational database
- **HR Employee Attrition dataset** (1,470 records, 35 columns)

---

## API Endpoint Summary

| Endpoint | Method | Purpose | Question Type |
|----------|--------|---------|---------------|
| `/health` | GET | Health check | - |
| `/api/chat` | POST | Direct LLM chat | Any |
| `/api/analyze` | POST | **Smart routing** ⭐ | Auto-detect |
| `/api/analyze/what` | POST | Direct WHAT analysis | WHAT only |
| `/api/analyze/why` | POST | Direct WHY analysis | WHY only |
| `/api/query` | POST | Legacy SQL+viz | WHAT only |
| `/api/sql-only` | POST | SQL without viz | WHAT only |

**Recommended:** Use `/api/analyze` for all user questions.

---

## Performance Characteristics

### Response Times (Approximate)

| Operation | Time | Notes |
|-----------|------|-------|
| Planner routing | ~1-2s | LLM classification |
| Text-to-SQL | ~2-3s | SQL generation + execution |
| Visualization | ~1-2s | Chart generation |
| Hypothesis gen | ~3-5s | Generates 3-5 hypotheses |
| Statistical test | ~0.5s | Per hypothesis |
| **Total (WHAT)** | **~3-5s** | SQL + Viz |
| **Total (WHY)** | **~5-8s** | 3 hypotheses + tests |

### Optimization Tips

1. **Skip planner** - Use direct endpoints (`/analyze/what`, `/analyze/why`)
2. **Reduce hypotheses** - Set `num_hypotheses=2` for faster WHY questions
3. **Disable viz** - Set `include_visualization=false` for WHAT questions
4. **Use faster LLM** - Switch to Groq API (Llama 3.3 70B) for 2-3x speedup

---

## Error Handling

### Graceful Degradation

1. **SQL Generation Fails**
   - Returns error message
   - User can retry with rephrased question

2. **Visualization Fails**
   - Falls back to simple bar/table chart
   - Still returns data

3. **Hypothesis Generation Fails**
   - Returns error with guidance
   - Suggests rephrasing question

4. **Statistical Test Fails**
   - Returns error for specific test
   - Other tests still execute

### Validation Layers

1. **Input Validation** (Pydantic)
2. **SQL Safety** (SELECT-only, no DROP/DELETE)
3. **Variable Existence** (Check column names)
4. **Sample Size** (Warn if n < 30)

---

## Security Considerations

✅ **SQL Injection Protection**
- Only SELECT queries allowed
- Parameterized queries
- No user-defined table names

✅ **Input Validation**
- Type checking on all inputs
- Length limits on strings
- Range limits on numeric params

✅ **Error Messages**
- No sensitive info in errors
- Generic error messages for security failures

✅ **CORS**
- Configured allowed origins
- Credentials handling

---

## Monitoring & Logging

### Startup Logs
```
🔄 Initializing Multi-Agent System...
   - Planner Agent (Question Router)
   - Text-to-SQL + Visualization Agents
   - Hypothesis + Statistical Testing Agents
✅ Multi-Agent System initialized successfully!
```

### Request Logs
```
📝 User Question: What is the attrition rate?
🎯 Type: WHAT
🔄 Routing to TEXT-TO-SQL + VISUALIZATION AGENTS
✅ Query executed successfully. Returned 3 rows.
```

### Error Logs
```
❌ Error: SQL generation failed: Invalid column name
❌ Error: Statistical test failed: Insufficient sample size
```

---

This architecture provides a **production-ready, scalable, and maintainable** multi-agent system for comprehensive HR analytics!
