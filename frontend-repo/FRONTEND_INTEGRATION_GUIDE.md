# Frontend Integration Guide
## Multi-Agent System with Planner Agent Routing

---

## 🎯 Overview

Your frontend is now **fully synchronized** with the backend's Multi-Agent System. All user questions are automatically routed through the **Planner Agent** which intelligently determines whether to:

- **WHAT questions** → Text-to-SQL + Visualization Agents
- **WHY questions** → Hypothesis + Statistical Testing Agents

---

## 📋 What Changed

### 1. **API Client** (`src/api/client.js`)

#### Before:
```javascript
// Directly called /api/query endpoint
export async function sendAnalyticsQuery(question) {
  const res = await fetch(`${BACKEND_BASE_URL}/query`, {...});
}
```

#### After:
```javascript
// Now calls /api/analyze (routes through Planner Agent)
export async function sendAnalyticsQuery(question, includeVisualization = true) {
  const res = await fetch(`${BACKEND_BASE_URL}/analyze`, {
    body: JSON.stringify({ 
      question,
      include_visualization: includeVisualization 
    }),
  });
}
```

**Benefits:**
- ✅ Automatic question classification (WHAT vs WHY)
- ✅ Intelligent agent routing
- ✅ Supports both descriptive and causal analytics
- ✅ Backward compatible (legacy `sendDirectSQLQuery` still available)

---

### 2. **Example Prompts** (`src/lib/api.ts`)

#### Before:
```typescript
export const EXAMPLE_PROMPTS = [
  "What is the most effective machine learning model for predicting customer churn?",
  // Generic ML questions
] as const;
```

#### After:
```typescript
export const EXAMPLE_PROMPTS = [
  "What is the attrition rate by department?",              // WHAT question
  "Why do employees leave the company?",                     // WHY question
  "What is the average monthly income by job role?",        // WHAT question
  "Why is attrition higher in Sales department?",           // WHY question
  "What is the distribution of years at company..."         // WHAT question
] as const;
```

**Benefits:**
- ✅ HR-specific examples
- ✅ Mix of WHAT and WHY questions
- ✅ Demonstrates both analytics types

---

### 3. **Response Handling** (`src/pages/AnalyticsAssistant.tsx`)

#### Enhanced Response Processing:

```typescript
const response = await sendAnalyticsQuery(query);

if (response.question_type === 'WHAT') {
  // Descriptive analytics - show SQL + data + visualization
  responseText = `✅ Found ${response.data.length} result(s)
                  📊 Question Type: WHAT (Descriptive Analytics)
                  🔍 Agents Used: Text-to-SQL + Visualization`;
} else if (response.question_type === 'WHY') {
  // Causal analytics - show hypotheses + statistical tests
  responseText = `✅ Generated ${numHypotheses} hypotheses
                  📊 Question Type: WHY (Causal Analytics)
                  🔬 Agents Used: Hypothesis + Statistical Testing`;
}
```

**New UI Components:**

1. **Hypothesis Cards** (for WHY questions)
   ```tsx
   🔬 Generated Hypotheses
   ┌─────────────────────────────────────┐
   │ Hypothesis 1                        │
   │ H₀: No relationship between...      │
   │ H₁: Overtime is associated with...  │
   │ Variables: overtime vs attrition    │
   │ Test: Chi-square                    │
   └─────────────────────────────────────┘
   ```

2. **Statistical Results** (for WHY questions)
   ```tsx
   📊 Statistical Test Results
   ┌─────────────────────────────────────┐
   │ Hypothesis 1 Results    ✓ Significant│
   │ Test: Chi-Square Test               │
   │ p-value: 0.0001                     │
   │ χ² = 25.43, Cramér's V = 0.132      │
   │ 💡 Highly significant relationship  │
   └─────────────────────────────────────┘
   ```

3. **Enhanced SQL Display** (for WHAT questions)
   ```tsx
   📝 SQL Query
   [Syntax-highlighted SQL code block]
   ```

4. **Data Tables** (for WHAT questions)
   - Shows first 10 rows
   - Formatted numbers (2 decimal places)
   - Row count indicator

5. **Visualizations** (for WHAT questions)
   - Interactive Plotly charts
   - Dark theme optimized
   - Responsive layout

---

## 🔄 Request/Response Flow

### WHAT Question Example

```mermaid
User Input: "What is the attrition rate by department?"
    ↓
Frontend (sendAnalyticsQuery)
    ↓
POST /api/analyze
{
  "question": "What is the attrition rate by department?",
  "include_visualization": true
}
    ↓
Backend (Planner Agent)
    ↓ Classifies as "WHAT"
    ↓ Routes to Text-to-SQL + Visualization
    ↓
Response
{
  "success": true,
  "question_type": "WHAT",
  "sql": "SELECT department, ...",
  "data": [...],
  "visualization": {
    "plotly_json": {...}
  }
}
    ↓
Frontend Renders:
✅ Message
📝 SQL Query (CodeBlock)
📊 Data Table (first 10 rows)
📈 Interactive Plotly Chart
```

---

### WHY Question Example

```mermaid
User Input: "Why do employees leave the company?"
    ↓
Frontend (sendAnalyticsQuery)
    ↓
POST /api/analyze
{
  "question": "Why do employees leave the company?",
  "include_visualization": true
}
    ↓
Backend (Planner Agent)
    ↓ Classifies as "WHY"
    ↓ Routes to Hypothesis + Statistical Testing
    ↓
Response
{
  "success": true,
  "question_type": "WHY",
  "hypotheses": {
    "hypotheses": [
      {
        "hypothesis_id": 1,
        "null_hypothesis": "...",
        "alternative_hypothesis": "...",
        "variable_1": "overtime",
        "variable_2": "attrition",
        "recommended_test": "chi-square"
      },
      ...
    ]
  },
  "statistical_results": {
    "hypothesis_results": [
      {
        "hypothesis_id": 1,
        "statistical_results": {
          "test_name": "Chi-Square Test",
          "p_value": 0.0001,
          "chi2_statistic": 25.43,
          "cramers_v": 0.132,
          "interpretation": "Highly significant..."
        }
      },
      ...
    ]
  }
}
    ↓
Frontend Renders:
✅ Message with summary
🔬 Hypothesis Cards (3-5 hypotheses)
📊 Statistical Test Results (with significance indicators)
💡 Interpretations
```

---

## 🚀 Running the Integrated System

### Prerequisites

1. **Backend Running:**
   ```bash
   cd backend-repo
   uvicorn app.main:app --reload --port 8000
   ```
   
   ✅ Verify: http://localhost:8000/health should return `{"status": "healthy"}`

2. **LM Studio Running:**
   - Start LM Studio
   - Load IBM Granite 3.2 8B model
   - Ensure API server is running on port 1234

3. **PostgreSQL Running:**
   - Ensure `hr_data` schema exists
   - Verify `employee_attrition` table has 1,470 records

---

### Start the Frontend

```bash
cd frontend-repo
npm install
npm run dev
```

Expected output:
```
VITE v5.x.x  ready in X ms

➜  Local:   http://localhost:5174/
➜  Network: use --host to expose
```

---

### Test the Integration

1. **Open Browser:** http://localhost:5174

2. **Try WHAT Questions:**
   - Click: "What is the attrition rate by department?"
   - Expected: SQL query + data table + bar chart

3. **Try WHY Questions:**
   - Click: "Why do employees leave the company?"
   - Expected: Hypotheses cards + statistical test results

4. **Check Console Logs:**
   ```
   Sending analytics query to: http://127.0.0.1:8000/api/analyze
   Query: What is the attrition rate by department?
   Response status: 200
   Question type detected: WHAT
   ```

---

## 🎨 UI Features

### Response Message Format

**WHAT Questions:**
```
✅ Found 3 result(s) for your query.

📊 Question Type: WHAT (Descriptive Analytics)
🔍 Agents Used: Text-to-SQL + Visualization
```

**WHY Questions:**
```
✅ Generated 3 hypotheses and conducted 3 statistical test(s).

📊 Question Type: WHY (Causal Analytics)
🔬 Agents Used: Hypothesis Generation + Statistical Testing

🎯 Significant Findings: 2 out of 3 hypotheses showed statistically 
   significant results (p < 0.05)
```

---

### Statistical Significance Indicators

- **Green badge:** p < 0.05 (Significant)
- **No badge:** p ≥ 0.05 (Not significant)

Example:
```tsx
┌─────────────────────────────────────┐
│ Hypothesis 1 Results    ✓ Significant│  ← Green badge
│ p-value: 0.0001                     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Hypothesis 2 Results                │  ← No badge
│ p-value: 0.1234                     │
└─────────────────────────────────────┘
```

---

### Effect Size Display

Different tests show different metrics:

| Test Type | Metrics Displayed |
|-----------|-------------------|
| Chi-Square | χ², Cramér's V |
| T-test | t, Cohen's d |
| ANOVA | F, η² (eta squared) |
| Correlation | r, R² |

Example:
```
Chi-Square Test
χ² = 25.43, Cramér's V = 0.132

T-test
t = -6.32, Cohen's d = 0.54

ANOVA
F = 8.45, η² = 0.067

Correlation
r = -0.45, R² = 0.203
```

---

## 🛠️ Configuration

### Environment Variables

Create `.env` file in `frontend-repo/`:

```env
# Backend API URL
VITE_BACKEND_URL=http://127.0.0.1:8000/api
```

**Production:**
```env
VITE_BACKEND_URL=https://your-backend-domain.com/api
```

---

### Customize Visualization Settings

In `src/pages/AnalyticsAssistant.tsx`:

```tsx
<Plot
  data={message.data.visualization.plotly_json?.data ?? []}
  layout={{
    ...message.data.visualization.plotly_json?.layout,
    autosize: true,
    paper_bgcolor: 'rgba(0,0,0,0)',  // Transparent background
    plot_bgcolor: 'rgba(0,0,0,0)',   // Transparent plot area
    font: { color: '#e5e7eb', size: 11 }, // Light gray text
    margin: { l: 120, r: 80, t: 60, b: 100 }, // Custom margins
    height: 500,                      // Chart height
  }}
  config={{ 
    responsive: true,                 // Responsive to window resize
    displayModeBar: true              // Show Plotly controls
  }}
/>
```

---

## 📊 Sample Interactions

### Interaction 1: Department Analysis (WHAT)

**User Input:**
```
What is the attrition rate by department?
```

**Frontend Display:**
```
You: What is the attrition rate by department?