# Multi-Agent HR Analytics System - Backend Integration

## Overview

This backend integrates **5 intelligent agents** into a unified API for comprehensive HR analytics:

### 🤖 Agents

1. **Planner Agent** - Routes questions to appropriate agents
2. **Text-to-SQL Agent** - Converts natural language to SQL queries
3. **Visualization Agent** - Generates interactive Plotly charts
4. **Hypothesis Agent** - Generates testable statistical hypotheses
5. **Stats Agent** - Performs statistical tests (t-test, ANOVA, chi-square, correlation)

---

## 🎯 How It Works

### Intelligent Routing

The **Planner Agent** analyzes questions and routes them:

- **WHAT Questions** (Descriptive Analytics)
  - "What is the attrition rate?"
  - "How many employees are in each department?"
  - "Show me salary distribution by gender"
  - → Routes to: **Text-to-SQL + Visualization**

- **WHY Questions** (Causal Analytics)
  - "Why do employees leave?"
  - "Does overtime affect attrition?"
  - "What causes low job satisfaction?"
  - → Routes to: **Hypothesis + Statistical Testing**

---

## 📡 API Endpoints

### 1. **Smart Analysis** (Recommended)
```http
POST /api/analyze
```

**Auto-routes** based on question type.

**Request:**
```json
{
  "question": "Why do employees in Sales have higher attrition?",
  "num_hypotheses": 3,
  "include_visualization": true
}
```

**Response for WHAT questions:**
```json
{
  "success": true,
  "question": "What is the attrition rate by department?",
  "question_type": "WHAT",
  "analysis_type": "descriptive_analytics",
  "planner_decision": {
    "question_type": "WHAT",
    "reasoning": "...",
    "agents_to_call": ["text_to_sql", "visualization"]
  },
  "sql": "SELECT department, ...",
  "data": [...],
  "rows": 3,
  "columns": ["department", "attrition_rate"],
  "visualization": {
    "success": true,
    "plotly_json": {...}
  }
}
```

**Response for WHY questions:**
```json
{
  "success": true,
  "question": "Why do employees leave?",
  "question_type": "WHY",
  "analysis_type": "causal_analytics",
  "planner_decision": {
    "question_type": "WHY",
    "reasoning": "...",
    "agents_to_call": ["hypothesis", "statistical_testing"]
  },
  "hypotheses": {
    "hypotheses": [
      {
        "hypothesis_id": 1,
        "null_hypothesis": "H0: ...",
        "alternative_hypothesis": "H1: ...",
        "variable_1": "overtime",
        "variable_2": "attrition",
        "recommended_test": "chi-square"
      }
    ]
  },
  "statistical_results": {
    "summary": {
      "total_hypotheses": 3
    },
    "hypothesis_results": [
      {
        "statistical_results": {
          "test_name": "Chi-Square Test",
          "p_value": 0.0001,
          "chi2_statistic": 25.43,
          "interpretation": "Highly significant..."
        }
      }
    ]
  }
}
```

### 2. **Direct WHAT Analysis**
```http
POST /api/analyze/what
```

Bypass planner, go straight to Text-to-SQL + Visualization.

**Request:**
```json
{
  "question": "Show average salary by department",
  "include_visualization": true
}
```

### 3. **Direct WHY Analysis**
```http
POST /api/analyze/why
```

Bypass planner, go straight to Hypothesis + Stats.

**Request:**
```json
{
  "question": "What factors cause attrition?",
  "num_hypotheses": 5
}
```

### 4. **Legacy Endpoints** (Backward Compatible)

```http
POST /api/query          # Text-to-SQL + Viz (WHAT questions only)
POST /api/sql-only       # SQL + Data only (no viz)
POST /api/chat           # Direct LLM chat
```

---

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
cd backend-repo
pip install -r requirements.txt
```

**Additional packages for multi-agent system:**
```bash
pip install scipy pydantic
```

### 2. Environment Variables

Create/update `.env` file:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hr_analytics
DB_USER=your_user
DB_PASSWORD=your_password
DB_SCHEMA=public

# LLM Configuration (Local LM Studio)
OPENAI_BASE_URL=http://127.0.0.1:1234/v1
OPENAI_API_KEY=lm-studio
OPENAI_MODEL=ibm/granite-3.2-8b

# Or use external APIs
# GROQ_API_KEY=your_groq_key
# OPENAI_API_KEY=your_openai_key
```

### 3. Run the Server

```bash
# From backend-repo directory
cd app
python -m uvicorn main:app --reload --port 8000
```

Or:

```bash
# From backend-repo directory
uvicorn app.main:app --reload --port 8000
```

### 4. Test the System

Visit: `http://localhost:8000/api/docs`

**Test WHAT question:**
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the attrition rate by department?",
    "include_visualization": true
  }'
```

**Test WHY question:**
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Why do employees leave the company?",
    "num_hypotheses": 3
  }'
```

---

## 📂 Project Structure

```
backend-repo/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI app + Multi-Agent startup
│   ├── config.py                        # Settings
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                    # API endpoints
│   └── services/
│       ├── llm.py                       # LLM client
│       ├── TTS_vis.py                   # Text-to-SQL + Visualization (Combined)
│       ├── planner_agent.py             # 🆕 Planner Agent
│       ├── hypothesis_stats_agent.py    # 🆕 Hypothesis + Stats Agents
│       └── multi_agent_system.py        # 🆕 Multi-Agent Orchestrator
├── requirements.txt
└── README.md                            # This file
```

---

## 🔧 How Agents Are Connected

### Architecture Diagram

```
User Question
     ↓
┌────────────────────┐
│  Planner Agent     │  ← Analyzes question type
└────────┬───────────┘
         │
    ┌────┴────┐
    ↓         ↓
┌───────┐  ┌───────┐
│ WHAT? │  │ WHY?  │
└───┬───┘  └───┬───┘
    │          │
    ↓          ↓
┌─────────┐  ┌──────────────┐
│Text-SQL │  │ Hypothesis   │
│    +    │  │      +       │
│  Viz    │  │    Stats     │
└─────────┘  └──────────────┘
    │              │
    ↓              ↓
  Charts     Test Results
```

### Flow Example

**WHAT Question:**
1. User: "What is the attrition rate?"
2. Planner: "This is a WHAT question"
3. Text-to-SQL: Generates SQL query
4. Executes query → DataFrame
5. Visualization: Creates Plotly chart
6. Returns: SQL + Data + Chart

**WHY Question:**
1. User: "Why do employees leave?"
2. Planner: "This is a WHY question"
3. Hypothesis Agent: Generates 3 testable hypotheses
4. Stats Agent: Runs chi-square, t-test, ANOVA, correlation
5. Returns: Hypotheses + Statistical Results

---

## 🧪 Testing

### Unit Tests (Future)
```bash
pytest tests/
```

### Integration Testing

Use Swagger UI: `http://localhost:8000/api/docs`

**Test Cases:**

1. **WHAT question with visualization**
   - Question: "Compare attrition rates between genders"
   - Expected: SQL + Data + Bar Chart

2. **WHY question with hypotheses**
   - Question: "What causes high attrition in Sales?"
   - Expected: 3 hypotheses + Statistical test results

3. **Edge case: Ambiguous question**
   - Question: "Tell me about attrition"
   - Expected: Defaults to WHAT (safer)

---

## 📊 Statistical Tests Performed

The Stats Agent automatically selects tests based on variable types:

| Variable 1 Type | Variable 2 Type | Test Performed |
|----------------|----------------|----------------|
| Categorical (2 groups) | Numerical | **Independent T-Test** |
| Categorical (3+ groups) | Numerical | **One-Way ANOVA** |
| Categorical | Categorical | **Chi-Square Test** |
| Numerical | Numerical | **Pearson + Spearman Correlation** |

**Effect sizes calculated:**
- Cohen's d (T-test)
- Eta-squared (ANOVA)
- Cramér's V (Chi-square)
- R-squared (Correlation)

---

## 🎓 Example Usage

### Python Client Example

```python
import requests

url = "http://localhost:8000/api/analyze"

# WHAT question
response = requests.post(url, json={
    "question": "What is the average salary by department?",
    "include_visualization": True
})
result = response.json()

if result["question_type"] == "WHAT":
    print(f"SQL: {result['sql']}")
    print(f"Rows: {result['rows']}")
    # Plotly chart in result['visualization']['plotly_json']

# WHY question
response = requests.post(url, json={
    "question": "Does overtime affect employee attrition?",
    "num_hypotheses": 3
})
result = response.json()

if result["question_type"] == "WHY":
    for hyp in result["hypotheses"]["hypotheses"]:
        print(f"H0: {hyp['null_hypothesis']}")
        print(f"H1: {hyp['alternative_hypothesis']}")
    
    for test_result in result["statistical_results"]["hypothesis_results"]:
        stats = test_result["statistical_results"]
        print(f"p-value: {stats['p_value']}")
        print(f"Interpretation: {stats['interpretation']}")
```

---

## 🔐 Security Features

✅ **SQL Injection Protection**
- Only SELECT queries allowed
- Blocks INSERT/UPDATE/DELETE/DROP
- Parameterized queries via SQLAlchemy

✅ **Input Validation**
- Pydantic models validate all requests
- Type checking on all parameters
- Error handling and logging

✅ **CORS Configuration**
- Configured in `app/config.py`
- Restrict origins in production

---

## 🚧 Known Limitations

1. **Local LLM Performance**
   - IBM Granite 3.2 8B works well but occasionally generates imperfect SQL
   - Consider using larger models (Llama 3.3 70B via Groq) for production

2. **Data Loading**
   - Stats agent loads full dataset into memory
   - For >100K rows, consider sampling or pagination

3. **Visualization Generation**
   - Fallback charts used if LLM-generated code fails
   - ~99% success rate with fallback mechanism

---

## 🛠️ Troubleshooting

### Issue: "Multi-Agent System not initialized"

**Solution:**
- Check LM Studio is running on `http://localhost:1234`
- Verify database connection in `.env`
- Check server startup logs for errors

### Issue: "No module named 'scipy'"

**Solution:**
```bash
pip install scipy pydantic
```

### Issue: Slow response times

**Solution:**
- Use `/api/analyze/what` for WHAT questions (skips planner)
- Use `/api/sql-only` if visualization not needed
- Consider caching frequently asked questions

---

## 📖 Documentation

- **API Docs:** `http://localhost:8000/api/docs` (Swagger UI)
- **Text-to-SQL Agent:** `TEXT_TO_SQL_AGENT_DOCUMENTATION.md`
- **Visualization Agent:** `VISUALIZATION_AGENT_DOCUMENTATION.md`
- **Data Dictionary:** `data/HR_Data_Dictionary.csv`

---

## 🎉 Quick Start Summary

```bash
# 1. Install dependencies
pip install -r requirements.txt scipy pydantic

# 2. Start LM Studio (http://localhost:1234)

# 3. Configure .env file

# 4. Run server
uvicorn app.main:app --reload --port 8000

# 5. Test
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the attrition rate?"}'
```

---

## 📝 License

[Your License Here]

## 👥 Contributors

Yogarajaadithya

## 📧 Contact

[Your Contact Information]

---

**Built with:** FastAPI, LangChain, SQLAlchemy, Plotly, SciPy, Pandas, PostgreSQL
