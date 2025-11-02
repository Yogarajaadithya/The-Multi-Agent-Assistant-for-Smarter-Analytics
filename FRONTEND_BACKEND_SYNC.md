# Frontend-Backend Synchronization
## Complete Integration Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React + Vite)                         │
│                         http://localhost:5174                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
            ┌───────▼────────┐            ┌────────▼─────────┐
            │  User Question │            │  Example Prompts │
            │  Input Field   │            │   (5 examples)   │
            └───────┬────────┘            └────────┬─────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                        ┌───────────▼──────────────┐
                        │  sendAnalyticsQuery()    │
                        │  src/api/client.js       │
                        │                          │
                        │  POST /api/analyze       │
                        │  {                       │
                        │    question: "...",      │
                        │    include_viz: true     │
                        │  }                       │
                        └───────────┬──────────────┘
                                    │
                                    │ HTTP Request
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                          BACKEND (FastAPI)                               │
│                         http://localhost:8000                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                      POST /api/analyze                                   │
│                      app/api/routes.py                                   │
│                               │                                          │
│                               ↓                                          │
│                   ┌───────────────────────┐                             │
│                   │  MultiAgentSystem     │                             │
│                   │  process_question()   │                             │
│                   └───────────┬───────────┘                             │
│                               │                                          │
│                               ↓                                          │
│                   ┌───────────────────────┐                             │
│                   │   PLANNER AGENT       │                             │
│                   │   analyze_question()  │                             │
│                   │                       │                             │
│                   │ • Classifies question │                             │
│                   │ • Returns WHAT or WHY │                             │
│                   └───────────┬───────────┘                             │
│                               │                                          │
│                ┌──────────────┴──────────────┐                          │
│                │                             │                          │
│          WHAT Question?               WHY Question?                     │
│                │                             │                          │
│                ↓                             ↓                          │
│    ┌────────────────────┐        ┌──────────────────────┐              │
│    │  Text-to-SQL Agent │        │  Hypothesis Agent    │              │
│    │                    │        │                      │              │
│    │ • Generate SQL     │        │ • Generate 3-5       │              │
│    │ • Execute query    │        │   hypotheses         │              │
│    │ • Return DataFrame │        │ • Identify variables │              │
│    └─────────┬──────────┘        └──────────┬───────────┘              │
│              │                              │                          │
│              ↓                              ↓                          │
│    ┌────────────────────┐        ┌──────────────────────┐              │
│    │ Visualization Agent│        │ Stats Testing Agent  │              │
│    │                    │        │                      │              │
│    │ • Analyze data     │        │ • Chi-square test    │              │
│    │ • Create Plotly    │        │ • T-test             │              │
│    │   chart            │        │ • ANOVA              │              │
│    │ • Return JSON      │        │ • Correlation        │              │
│    └─────────┬──────────┘        └──────────┬───────────┘              │
│              │                              │                          │
│              └──────────────┬───────────────┘                          │
│                             │                                          │
│                             ↓                                          │
│                    ┌─────────────────┐                                 │
│                    │  JSON Response  │                                 │
│                    └────────┬────────┘                                 │
│                             │                                          │
└─────────────────────────────┼─────────────────────────────────────────┘
                              │
                              │ HTTP Response
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                   FRONTEND RENDERING                                     │
│                   src/pages/AnalyticsAssistant.tsx                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  IF question_type === "WHAT":                                           │
│  ┌────────────────────────────────────────────────────────────┐        │
│  │  ✅ Response Message                                        │        │
│  │  📊 Question Type: WHAT (Descriptive Analytics)             │        │
│  │  🔍 Agents Used: Text-to-SQL + Visualization                │        │
│  │                                                              │        │
│  │  📝 SQL Query                                                │        │
│  │  [Syntax-highlighted SQL code block]                        │        │
│  │                                                              │        │
│  │  📊 Data Table                                               │        │
│  │  [First 10 rows with formatted numbers]                     │        │
│  │                                                              │        │
│  │  📈 Interactive Plotly Chart                                 │        │
│  │  [Bar chart / Line chart / Scatter plot]                    │        │
│  └────────────────────────────────────────────────────────────┘        │
│                                                                          │
│  IF question_type === "WHY":                                            │
│  ┌────────────────────────────────────────────────────────────┐        │
│  │  ✅ Response Message                                        │        │
│  │  📊 Question Type: WHY (Causal Analytics)                   │        │
│  │  🔬 Agents Used: Hypothesis + Statistical Testing           │        │
│  │  🎯 Significant Findings: 2 out of 3 (p < 0.05)             │        │
│  │                                                              │        │
│  │  🔬 Generated Hypotheses                                     │        │
│  │  ┌──────────────────────────────────────────┐               │        │
│  │  │ Hypothesis 1                             │               │        │
│  │  │ H₀: No relationship between...           │               │        │
│  │  │ H₁: Overtime is associated with...       │               │        │
│  │  │ Variables: overtime vs attrition         │               │        │
│  │  │ Test: Chi-square                         │               │        │
│  │  └──────────────────────────────────────────┘               │        │
│  │                                                              │        │
│  │  📊 Statistical Test Results                                 │        │
│  │  ┌──────────────────────────────────────────┐               │        │
│  │  │ Hypothesis 1 Results    ✓ Significant   │ ← Green badge │        │
│  │  │ Test: Chi-Square Test                   │               │        │
│  │  │ p-value: 0.0001                         │               │        │
│  │  │ χ² = 25.43, Cramér's V = 0.132          │               │        │
│  │  │ 💡 Highly significant relationship...   │               │        │
│  │  └──────────────────────────────────────────┘               │        │
│  └────────────────────────────────────────────────────────────┘        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Summary

### WHAT Question Flow
```
User: "What is the attrition rate by department?"
  ↓
Frontend: sendAnalyticsQuery(question)
  ↓
Backend: POST /api/analyze
  ↓
Planner Agent: Classifies as "WHAT"
  ↓
Text-to-SQL Agent: Generates SQL
  ↓
Visualization Agent: Creates Plotly chart
  ↓
Response: { question_type: "WHAT", sql, data, visualization }
  ↓
Frontend: Renders SQL + Table + Chart
```

### WHY Question Flow
```
User: "Why do employees leave the company?"
  ↓
Frontend: sendAnalyticsQuery(question)
  ↓
Backend: POST /api/analyze
  ↓
Planner Agent: Classifies as "WHY"
  ↓
Hypothesis Agent: Generates 3 hypotheses
  ↓
Stats Testing Agent: Runs chi-square, t-test, ANOVA
  ↓
Response: { question_type: "WHY", hypotheses, statistical_results }
  ↓
Frontend: Renders Hypotheses + Test Results
```

---

## Key Integration Points

### 1. API Endpoint Change
**Old:** `POST /api/query` (direct to Text-to-SQL)
**New:** `POST /api/analyze` (routes through Planner Agent)

### 2. Request Payload
```javascript
{
  "question": "What is the attrition rate by department?",
  "include_visualization": true
}
```

### 3. Response Structure
```javascript
{
  "success": true,
  "question_type": "WHAT" | "WHY",
  
  // For WHAT questions:
  "sql": "SELECT...",
  "data": [...],
  "visualization": { plotly_json: {...} },
  
  // For WHY questions:
  "hypotheses": { hypotheses: [...] },
  "statistical_results": { hypothesis_results: [...] }
}
```

### 4. Frontend Components Updated
- ✅ `src/api/client.js` - API call to `/analyze`
- ✅ `src/lib/api.ts` - HR-specific example prompts
- ✅ `src/pages/AnalyticsAssistant.tsx` - Response rendering

---

## Agent Routing Logic

```javascript
// In backend/app/services/planner_agent.py

function analyze_question(question) {
  // Use LLM to classify
  if (contains("what", "how many", "show me", "list")) {
    return { question_type: "WHAT" }
  }
  
  if (contains("why", "cause", "reason", "explain")) {
    return { question_type: "WHY" }
  }
  
  // Default to WHAT
  return { question_type: "WHAT" }
}
```

```javascript
// In frontend/src/api/client.js

export async function sendAnalyticsQuery(question) {
  // Always routes through Planner Agent
  const response = await fetch('/api/analyze', {
    body: JSON.stringify({ question })
  });
  
  // Response includes question_type
  console.log('Question type:', response.question_type);
  return response;
}
```

---

## Testing Checklist

### Backend Tests
- [ ] Health check returns `{"status": "healthy"}`
- [ ] POST /api/analyze with WHAT question returns SQL + viz
- [ ] POST /api/analyze with WHY question returns hypotheses + stats
- [ ] Planner Agent classifies questions correctly
- [ ] All agents initialize without errors

### Frontend Tests
- [ ] Example prompts populate input field
- [ ] Sending WHAT question shows SQL + chart
- [ ] Sending WHY question shows hypotheses + results
- [ ] Statistical significance badges appear correctly
- [ ] History sidebar saves queries
- [ ] Error messages are informative

### Integration Tests
- [ ] WHAT question end-to-end works
- [ ] WHY question end-to-end works
- [ ] Browser console shows correct question_type
- [ ] No CORS errors
- [ ] Visualizations render correctly
- [ ] Statistical test results display properly

---

**✅ Integration Status: COMPLETE**

Your frontend now intelligently routes all questions through the Planner Agent for optimal multi-agent processing!
