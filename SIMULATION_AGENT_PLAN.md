# 🔮 Simulation Agent - Detailed Implementation Plan

**Project**: Multi-Agent Analytics Assistant  
**New Agent**: Simulation Agent (ML Model Integration & What-If Analysis)  
**Date**: February 2026  
**Author**: Yogarajaadithya

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Agent Overview](#agent-overview)
3. [Architecture & Design](#architecture--design)
4. [Core Features](#core-features)
5. [Technical Components](#technical-components)
6. [Integration with Existing System](#integration-with-existing-system)
7. [ML Model Management](#ml-model-management)
8. [Use Cases & Scenarios](#use-cases--scenarios)
9. [API Design](#api-design)
10. [Frontend Integration](#frontend-integration)
11. [Workflow & Orchestration](#workflow--orchestration)
12. [Implementation Phases](#implementation-phases)
13. [Technical Stack](#technical-stack)
14. [Testing Strategy](#testing-strategy)
15. [Deployment & MLOps](#deployment--mlops)
16. [Future Enhancements](#future-enhancements)

---

## 1. Executive Summary

The **Simulation Agent** bridges LLMs and ML models to enable what-if analysis and scenario forecasting. It democratizes advanced machine learning by allowing business users to run simulations through natural language queries, combining LLM-driven orchestration with ML-driven predictions.

### Key Capabilities
- 🔮 **Predictive Modeling**: Run ML model predictions via natural language
- 📊 **What-If Analysis**: Test scenarios and compare outcomes
- 📈 **Scenario Forecasting**: Generate multi-period forecasts
- 🎯 **Sensitivity Analysis**: Analyze impact of parameter changes
- 🧠 **Model Registry**: Manage and version ML models
- 💬 **Natural Language Interface**: Business-friendly interaction

---

## 2. Agent Overview

### 2.1 Purpose
Enable business users to:
- Run ML model predictions without technical knowledge
- Perform what-if analysis through conversational queries
- Compare multiple scenarios side-by-side
- Understand model predictions with LLM explanations
- Optimize decision variables to achieve targets

### 2.2 Question Types Handled

**SIMULATE Questions** (New category)
- "What if we increase marketing spend by 20%?"
- "Predict sales for next quarter if we reduce price by 10%"
- "What would be the attrition rate if we increase salaries by 15%?"
- "Simulate the impact of 4-day work week on productivity"
- "Forecast revenue for next 6 months"
- "What salary should we offer to reduce attrition to 10%?"
- "Compare scenario A (price +5%) vs scenario B (volume +10%)"

### 2.3 Value Proposition
- **For Business Users**: Run complex ML predictions without coding
- **For Data Scientists**: Deploy models that are actually used
- **For Decision Makers**: Test strategies before implementation
- **For Analysts**: Rapid scenario exploration and sensitivity analysis

---

## 3. Architecture & Design

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              USER QUERY                                          │
│                   "What if we increase salaries by 15%?"                        │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            PLANNER AGENT                                         │
│  • Classifies: WHAT / WHY / SIMULATE                                            │
│  • Routes to: Simulation Agent                                                  │
│  • Extracts: Model type, parameters, scenario details                          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         SIMULATION AGENT                                         │
│  ┌─────────────────────────────────────────────────────────────────┐           │
│  │  1. QUERY PARSER                                                │           │
│  │     • Extract: model type, input variables, scenario params     │           │
│  │     • Validate: inputs match model schema                       │           │
│  │     • Identify: baseline vs what-if scenarios                   │           │
│  └─────────────────────────────────────────────────────────────────┘           │
│                             ▼                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐           │
│  │  2. DATA PREPARATION                                            │           │
│  │     • Fetch baseline data (via Text-to-SQL Agent)              │           │
│  │     • Apply scenario modifications                              │           │
│  │     • Feature engineering & preprocessing                       │           │
│  │     • Validate feature ranges                                   │           │
│  └─────────────────────────────────────────────────────────────────┘           │
│                             ▼                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐           │
│  │  3. MODEL REGISTRY                                              │           │
│  │     • Load appropriate model                                    │           │
│  │     • Retrieve model metadata (features, target, version)       │           │
│  │     • Get preprocessing pipelines                               │           │
│  └─────────────────────────────────────────────────────────────────┘           │
│                             ▼                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐           │
│  │  4. PREDICTION ENGINE                                           │           │
│  │     • Run ML model inference                                    │           │
│  │     • Apply post-processing                                     │           │
│  │     • Generate prediction intervals (if available)              │           │
│  │     • Calculate scenario comparison deltas                      │           │
│  └─────────────────────────────────────────────────────────────────┘           │
│                             ▼                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐           │
│  │  5. INSIGHT GENERATOR (LLM)                                     │           │
│  │     • Explain predictions in business terms                     │           │
│  │     • Highlight key drivers and impacts                         │           │
│  │     • Generate recommendations                                  │           │
│  │     • Identify risks and caveats                                │           │
│  └─────────────────────────────────────────────────────────────────┘           │
│                             ▼                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐           │
│  │  6. VISUALIZATION GENERATOR                                     │           │
│  │     • Scenario comparison charts                                │           │
│  │     • Time series forecasts                                     │           │
│  │     • Sensitivity analysis plots                                │           │
│  │     • Feature importance charts                                 │           │
│  └─────────────────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RESPONSE TO USER                                    │
│  • Prediction results                                                           │
│  • Baseline vs What-If comparison                                              │
│  • Visualizations (charts)                                                     │
│  • LLM-generated insights                                                      │
│  • Confidence intervals                                                        │
│  • Recommendations                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Agent Workflow Types

#### 3.2.1 Single Prediction
```
User → "Predict attrition for employee ID 123"
→ Load employee data
→ Run model
→ Return prediction + explanation
```

#### 3.2.2 What-If Analysis
```
User → "What if we increase salary by 15%?"
→ Get baseline prediction
→ Modify salary parameter
→ Get what-if prediction
→ Compare and visualize delta
```

#### 3.2.3 Multi-Scenario Comparison
```
User → "Compare 3 scenarios: 10% raise, 20% raise, 30% raise"
→ Run model for each scenario
→ Generate comparison table + chart
→ Recommend optimal scenario
```

#### 3.2.4 Time Series Forecast
```
User → "Forecast sales for next 6 months"
→ Load historical data
→ Run forecasting model
→ Generate prediction intervals
→ Visualize forecast with confidence bounds
```

#### 3.2.5 Optimization
```
User → "What salary increase would reduce attrition to 10%?"
→ Define objective (attrition = 10%)
→ Iteratively adjust salary parameter
→ Find optimal value
→ Return recommendation
```

---

## 4. Core Features

### 4.1 Model Types to Support

#### Phase 1 (MVP):
1. **Classification Models**
   - Employee Attrition Prediction
   - Customer Churn Prediction
   - Lead Scoring

2. **Regression Models**
   - Sales Forecasting
   - Revenue Prediction
   - Demand Forecasting

#### Phase 2:
3. **Time Series Models**
   - ARIMA, Prophet, or LSTM for forecasting
   - Seasonal decomposition

4. **Clustering Models**
   - Customer Segmentation
   - Employee Profiling

5. **Recommender Systems**
   - Product Recommendations
   - Next Best Action

### 4.2 Simulation Capabilities

#### 4.2.1 Parameter Modification
- Change any input feature (salary, price, marketing spend, etc.)
- Support absolute values or percentage changes
- Handle multiple parameter changes simultaneously

#### 4.2.2 Scenario Engine
```python
# Example scenarios
scenarios = [
    {
        "name": "Conservative",
        "monthly_income": "+10%",
        "training_hours": "+20%"
    },
    {
        "name": "Aggressive",
        "monthly_income": "+25%",
        "training_hours": "+50%"
    },
    {
        "name": "Balanced",
        "monthly_income": "+15%",
        "training_hours": "+30%"
    }
]
```

#### 4.2.3 Sensitivity Analysis
- Vary one parameter while keeping others constant
- Identify which features have largest impact
- Generate tornado charts

#### 4.2.4 Batch Predictions
- Run predictions for multiple entities
- "Predict attrition for all Sales employees"
- Aggregate and summarize results

### 4.3 LLM Enhancement Features

#### 4.3.1 Natural Language to Parameters
```
User: "What if we give everyone a 20% raise?"
LLM extracts: {
    "parameter": "monthly_income",
    "modification": "multiply by 1.20",
    "scope": "all employees"
}
```

#### 4.3.2 Result Interpretation
```
Model Output: Attrition probability = 0.23 → 0.15
LLM Generates: "By increasing salaries by 20%, we can reduce 
               attrition from 23% to 15%, preventing ~35 
               employees from leaving. This investment of 
               $420K annually could save $1.2M in replacement costs."
```

#### 4.3.3 Recommendation Generation
- Optimal parameter values
- Trade-off analysis
- Risk assessment
- Business justification

---

## 5. Technical Components

### 5.1 Core Files to Create

```
backend-repo/app/services/
├── simulation_agent.py          # Main simulation agent
├── model_registry.py            # ML model management
├── scenario_engine.py           # What-if scenario handler
├── prediction_service.py        # Model inference
└── simulation_viz_agent.py      # Specialized visualizations

backend-repo/app/utils/
├── model_loader.py              # Load ML models from storage
├── feature_engineering.py       # Preprocessing pipelines
├── simulation_utils.py          # Helper functions
└── optimization_utils.py        # Parameter optimization

backend-repo/app/models/          # NEW: ML models directory
├── attrition_predictor/
│   ├── model.pkl                # Scikit-learn model
│   ├── scaler.pkl               # Feature scaler
│   ├── config.json              # Model metadata
│   └── feature_names.json       # Required features
├── sales_forecaster/
│   ├── model.pkl
│   ├── config.json
│   └── feature_names.json
└── model_registry.json          # Central registry

backend-repo/app/prompts/
└── simulation_prompts.py        # Simulation-specific prompts

backend-repo/app/api/
└── simulation_routes.py         # NEW: Simulation endpoints
```

### 5.2 Database Extensions

```sql
-- New table: ML Model Metadata
CREATE TABLE ml_models (
    model_id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,  -- 'classification', 'regression', 'timeseries'
    version VARCHAR(20) NOT NULL,
    dataset VARCHAR(50) NOT NULL,      -- 'hr_data', 'sales_data'
    target_variable VARCHAR(100),
    feature_names JSON,
    file_path VARCHAR(255),
    model_performance JSON,            -- accuracy, RMSE, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT
);

-- New table: Simulation History
CREATE TABLE simulation_history (
    simulation_id SERIAL PRIMARY KEY,
    user_query TEXT NOT NULL,
    model_id INT REFERENCES ml_models(model_id),
    baseline_inputs JSON,
    scenario_inputs JSON,
    predictions JSON,
    created_at TIMESTAMP DEFAULT NOW(),
    execution_time_ms INT
);

-- New table: Scenario Presets
CREATE TABLE scenario_presets (
    preset_id SERIAL PRIMARY KEY,
    preset_name VARCHAR(100) NOT NULL,
    model_id INT REFERENCES ml_models(model_id),
    scenario_definition JSON,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5.3 Key Classes & Interfaces

#### 5.3.1 Model Registry Class
```python
class ModelRegistry:
    """Manages ML model lifecycle."""
    
    def register_model(self, model_config: ModelConfig) -> str:
        """Register a new ML model."""
        pass
    
    def load_model(self, model_name: str, version: str = "latest"):
        """Load model from storage."""
        pass
    
    def get_model_metadata(self, model_name: str) -> dict:
        """Get model features, schema, performance."""
        pass
    
    def list_models(self, model_type: str = None) -> List[dict]:
        """List available models."""
        pass
```

#### 5.3.2 Prediction Service
```python
class PredictionService:
    """Handles model inference."""
    
    def predict(self, model_name: str, input_data: pd.DataFrame) -> dict:
        """Run model prediction."""
        pass
    
    def predict_proba(self, model_name: str, input_data: pd.DataFrame):
        """Get prediction probabilities (for classification)."""
        pass
    
    def batch_predict(self, model_name: str, input_data: pd.DataFrame):
        """Batch predictions for multiple records."""
        pass
```

#### 5.3.3 Scenario Engine
```python
class ScenarioEngine:
    """Manages what-if scenarios."""
    
    def create_scenario(self, baseline: dict, modifications: dict) -> dict:
        """Apply modifications to baseline."""
        pass
    
    def compare_scenarios(self, scenarios: List[dict]) -> pd.DataFrame:
        """Run and compare multiple scenarios."""
        pass
    
    def sensitivity_analysis(self, parameter: str, range_values: List) -> dict:
        """Analyze sensitivity to parameter changes."""
        pass
    
    def optimize_parameter(self, target_metric: str, target_value: float):
        """Find optimal parameter value to achieve target."""
        pass
```

#### 5.3.4 Simulation Agent
```python
async def simulation_agent(
    question: str,
    llm: AzureChatOpenAI,
    dataset: str = "hr_data",
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Main simulation agent function.
    
    Routes to:
    - Single prediction
    - What-if analysis
    - Multi-scenario comparison
    - Time series forecast
    - Parameter optimization
    """
    pass
```

---

## 6. Integration with Existing System

### 6.1 Planner Agent Updates

#### Update planner_agent.py to recognize SIMULATE questions:

```python
# Current: "WHAT" or "WHY"
# New: "WHAT", "WHY", or "SIMULATE"

question_types = ["WHAT", "WHY", "SIMULATE"]

# SIMULATE triggers:
simulate_keywords = [
    "what if", "simulate", "predict", "forecast", 
    "what would happen", "scenario", "impact of",
    "optimize", "what should", "compare scenarios"
]
```

#### Update planner prompt:

```python
planner_agent_prompt = """
You are a planning agent that routes analytics questions.

Question Types:
1. WHAT - Descriptive (e.g., "What is the attrition rate?")
   → Route to: text_to_sql, visualization
   
2. WHY - Causal (e.g., "Why do employees leave?")
   → Route to: text_to_sql, hypothesis, stats, visualization
   
3. SIMULATE - Predictive/What-If (e.g., "What if we increase salaries by 15%?")
   → Route to: simulation, visualization

SIMULATE Questions:
- Start with "what if", "predict", "forecast", "simulate"
- Ask about future scenarios or hypothetical changes
- Request comparisons of different scenarios
- Seek optimization or target achievement
- Request sensitivity analysis

Examples of SIMULATE questions:
- "What if we increase marketing spend by 20%?"
- "Predict next quarter sales"
- "What would happen if we reduce overtime?"
- "Compare 3 pricing scenarios"
- "What salary increase would reduce attrition to 10%?"
...
"""
```

### 6.2 Multi-Agent System Updates

#### Update multi_agent_system.py:

```python
from app.services.simulation_agent import simulation_agent

async def process_question(...):
    # Existing: WHAT, WHY
    # Add: SIMULATE
    
    if question_type == 'SIMULATE':
        return await _handle_simulate_question(
            question, llm, dataset, include_viz, verbose
        )

async def _handle_simulate_question(
    question: str,
    llm: AzureChatOpenAI,
    dataset: str,
    include_viz: bool,
    verbose: bool,
    planner_decision: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle SIMULATE questions (Predictive Analytics)."""
    
    # Call simulation agent
    simulation_result = await simulation_agent(
        question=question,
        llm=llm,
        dataset=dataset,
        verbose=verbose
    )
    
    # Generate visualizations if needed
    if include_viz and simulation_result.get("predictions"):
        viz = await simulation_viz_agent(
            simulation_result,
            llm
        )
        simulation_result["visualizations"] = viz
    
    return {
        "success": True,
        "question_type": "SIMULATE",
        "analysis_type": "predictive_analytics",
        "simulation_results": simulation_result,
        ...
    }
```

### 6.3 API Routes Updates

#### Add simulation endpoints:

```python
# routes.py

class SimulationRequest(BaseModel):
    question: str
    dataset: str = "hr_data"
    model_name: Optional[str] = None  # Auto-detect if None
    scenario_modifications: Optional[Dict[str, Any]] = None
    include_visualization: bool = True

class SimulationResponse(BaseModel):
    success: bool
    question: str
    model_used: str
    baseline_prediction: Optional[Dict[str, Any]] = None
    whatif_prediction: Optional[Dict[str, Any]] = None
    comparison: Optional[Dict[str, Any]] = None
    visualizations: Optional[List[Dict[str, Any]]] = None
    insights: Optional[str] = None
    recommendations: Optional[List[str]] = None
    error: Optional[str] = None

@router.post("/simulate", response_model=SimulationResponse)
async def simulate_scenario(req: SimulationRequest):
    """Run ML model simulation."""
    pass

@router.get("/models")
async def list_available_models():
    """List available ML models."""
    pass

@router.post("/models/{model_name}/predict")
async def predict(model_name: str, input_data: Dict[str, Any]):
    """Direct model prediction (for advanced users)."""
    pass
```

### 6.4 Text-to-SQL Agent Collaboration

The Simulation Agent will call the Text-to-SQL Agent to fetch baseline data:

```python
async def get_baseline_data(employee_id: int):
    """Fetch employee data for baseline prediction."""
    
    # Call text-to-SQL agent
    question = f"Get all features for employee ID {employee_id}"
    result = await text_to_sql_agent(question, llm, dataset="hr_data")
    
    return result["data"][0]  # Single employee record
```

---

## 7. ML Model Management

### 7.1 Model Storage Strategy

#### Option 1: Local File System (MVP)
```
backend-repo/app/models/
├── attrition_predictor/
│   ├── model_v1.pkl
│   ├── scaler.pkl
│   └── config.json
```

**Pros**: Simple, fast, no external dependencies  
**Cons**: Not scalable, versioning challenges

#### Option 2: Cloud Storage (Production)
- **Azure Blob Storage** or **AWS S3**
- Benefits: Versioning, scalability, security
- Use: `azure-storage-blob` or `boto3`

#### Option 3: MLflow (Recommended for Production)
- **MLflow Model Registry**
- Benefits: Built-in versioning, metadata, lineage
- Features: Model staging (dev/prod), deployment tracking

### 7.2 Model Versioning

```json
// model_registry.json
{
  "models": [
    {
      "model_name": "employee_attrition_predictor",
      "versions": [
        {
          "version": "v1",
          "path": "app/models/attrition_predictor/model_v1.pkl",
          "created_at": "2026-01-15",
          "accuracy": 0.87,
          "features": ["age", "monthly_income", "years_at_company", ...],
          "is_production": false
        },
        {
          "version": "v2",
          "path": "app/models/attrition_predictor/model_v2.pkl",
          "created_at": "2026-02-10",
          "accuracy": 0.91,
          "features": ["age", "monthly_income", "years_at_company", ...],
          "is_production": true
        }
      ]
    }
  ]
}
```

### 7.3 Model Training Pipeline

#### For Demo/MVP: Train simple models in notebooks

```python
# notebooks/train_attrition_model.ipynb

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib

# Load data
df = pd.read_sql("SELECT * FROM hr_data", conn)

# Prepare features
features = ['age', 'monthly_income', 'years_at_company', 
            'overtime', 'job_satisfaction', ...]
X = df[features]
y = df['attrition']

# Train model
model = RandomForestClassifier(n_estimators=100)
model.fit(X, y)

# Save model
joblib.dump(model, 'app/models/attrition_predictor/model.pkl')
joblib.dump(scaler, 'app/models/attrition_predictor/scaler.pkl')

# Save metadata
metadata = {
    "model_name": "employee_attrition_predictor",
    "version": "v1",
    "features": features,
    "target": "attrition",
    "accuracy": 0.87,
    "feature_importances": dict(zip(features, model.feature_importances_))
}
json.dump(metadata, open('app/models/attrition_predictor/config.json', 'w'))
```

#### For Production: Automated retraining

```python
# scripts/retrain_models.py
# - Scheduled retraining (weekly/monthly)
# - Automated model evaluation
# - A/B testing of new models
# - Automatic deployment if performance improves
```

### 7.4 Model Requirements

Each model must include:
1. **Model file**: `model.pkl` (joblib or pickle)
2. **Preprocessor**: `scaler.pkl` or `preprocessor.pkl`
3. **Config**: `config.json` with metadata
4. **Feature names**: List of required input features
5. **Documentation**: Model card with description, use cases, limitations

---

## 8. Use Cases & Scenarios

### 8.1 HR Dataset - Employee Attrition

#### Use Case 1: Individual Attrition Prediction
```
User: "Will employee ID 456 leave the company?"

Agent:
1. Fetch employee data from DB
2. Load attrition model
3. Run prediction
4. Return: "Attrition probability: 73%"
5. Explain: "High risk due to: low salary, long commute, no recent promotion"
```

#### Use Case 2: Salary Impact Analysis
```
User: "What if we give employee 456 a 20% raise?"

Agent:
1. Get baseline prediction (73% attrition)
2. Modify monthly_income by +20%
3. Get new prediction (45% attrition)
4. Visualize: Before-after comparison
5. Insight: "A 20% raise could reduce attrition risk by 28 percentage points"
```

#### Use Case 3: Department-Wide Simulation
```
User: "What would happen if we reduce overtime in Sales department?"

Agent:
1. Fetch all Sales employees
2. Set overtime = 'No' for all
3. Run batch prediction
4. Aggregate: "Predicted attrition would drop from 31% to 19%"
5. Recommend: "This could save 24 employees from leaving"
```

#### Use Case 4: Multi-Scenario Comparison
```
User: "Compare 3 scenarios: 10% raise, 15% raise, 20% raise"

Agent:
1. Run 3 simulations
2. Generate comparison table:
   - Scenario A (10%): Attrition = 26%
   - Scenario B (15%): Attrition = 22%
   - Scenario C (20%): Attrition = 18%
3. Visualize: Bar chart
4. Recommend: "Scenario B offers best ROI"
```

#### Use Case 5: Optimization
```
User: "What salary increase would reduce attrition to 10%?"

Agent:
1. Set target: attrition_probability = 0.10
2. Iteratively adjust monthly_income
3. Find optimal: +27%
4. Return: "A 27% salary increase would achieve 10% attrition target"
```

### 8.2 Sales Dataset - Revenue Forecasting

#### Use Case 6: Sales Forecast
```
User: "Predict sales for next quarter"

Agent:
1. Load historical sales data
2. Load time series forecasting model
3. Generate forecast with confidence intervals
4. Visualize: Line chart with prediction bands
5. Insight: "Expected sales: €2.3M (±€0.4M)"
```

#### Use Case 7: Pricing Impact
```
User: "What if we reduce prices by 10%?"

Agent:
1. Get baseline forecast
2. Apply price modifier: -10%
3. Run model (considering price elasticity)
4. Compare: Revenue impact
5. Insight: "10% price cut → +18% volume → +6% revenue"
```

#### Use Case 8: Marketing ROI
```
User: "What's the impact of doubling marketing spend?"

Agent:
1. Current: marketing_spend = €50K → sales = €1.2M
2. What-if: marketing_spend = €100K → sales = €1.5M
3. ROI calculation: +€300K revenue / €50K spend = 6x ROI
4. Recommend: "Strong positive ROI, consider increase"
```

### 8.3 Cross-Dataset Scenarios

#### Use Case 9: Integrated Business Planning
```
User: "If sales drop 20%, how many employees should we reduce?"

Agent:
1. Run sales forecast model: -20% revenue
2. Calculate cost reduction needed
3. Run attrition model: Identify high-risk employees
4. Recommend: "Natural attrition of 15 employees + selective 
             layoff of 10 would align with revenue projection"
```

---

## 9. API Design

### 9.1 Endpoint Structure

```
POST /api/analyze          # Existing: Routes to all agents
POST /api/simulate         # New: Direct simulation
GET  /api/models           # List available models
POST /api/models/predict   # Direct model prediction
POST /api/scenarios        # Run multi-scenario comparison
POST /api/optimize         # Parameter optimization
GET  /api/simulation-history  # Past simulations
```

### 9.2 Request/Response Examples

#### 9.2.1 Simple What-If Analysis

**Request:**
```json
{
  "question": "What if we increase salaries by 15%?",
  "dataset": "hr_data",
  "include_visualization": true
}
```

**Response:**
```json
{
  "success": true,
  "question_type": "SIMULATE",
  "model_used": "employee_attrition_predictor_v2",
  "baseline": {
    "attrition_rate": 0.16,
    "employees_at_risk": 24
  },
  "whatif": {
    "scenario": "monthly_income +15%",
    "attrition_rate": 0.11,
    "employees_at_risk": 16
  },
  "comparison": {
    "absolute_change": -0.05,
    "percentage_change": -31.25,
    "employees_saved": 8,
    "cost_impact": "$156,000 annual salary increase",
    "savings": "$280,000 replacement cost avoided"
  },
  "visualizations": [
    {
      "type": "bar",
      "data": {...},
      "title": "Attrition Rate: Baseline vs What-If"
    }
  ],
  "insights": "By increasing salaries by 15%, we can reduce attrition...",
  "recommendations": [
    "Prioritize raises for high-performers",
    "Focus on departments with highest attrition",
    "Consider non-monetary benefits as well"
  ]
}
```

#### 9.2.2 Multi-Scenario Comparison

**Request:**
```json
{
  "question": "Compare impact of salary increases: 10%, 15%, 20%",
  "dataset": "hr_data",
  "scenarios": [
    {"name": "Conservative", "monthly_income": "*1.10"},
    {"name": "Moderate", "monthly_income": "*1.15"},
    {"name": "Aggressive", "monthly_income": "*1.20"}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "scenarios": [
    {
      "name": "Baseline",
      "attrition_rate": 0.16,
      "cost": "$0"
    },
    {
      "name": "Conservative",
      "attrition_rate": 0.13,
      "cost": "$104K",
      "roi": "2.1x"
    },
    {
      "name": "Moderate",
      "attrition_rate": 0.11,
      "cost": "$156K",
      "roi": "1.8x"
    },
    {
      "name": "Aggressive",
      "attrition_rate": 0.09,
      "cost": "$208K",
      "roi": "1.5x"
    }
  ],
  "recommendation": "Moderate scenario offers best balance of impact and cost",
  "visualization": {...}
}
```

#### 9.2.3 Time Series Forecast

**Request:**
```json
{
  "question": "Forecast sales for next 6 months",
  "dataset": "sales_data",
  "forecast_periods": 6,
  "confidence_level": 0.95
}
```

**Response:**
```json
{
  "success": true,
  "model_used": "sales_forecaster_arima",
  "forecast": [
    {"month": "Mar 2026", "prediction": 2300000, "lower": 2100000, "upper": 2500000},
    {"month": "Apr 2026", "prediction": 2450000, "lower": 2200000, "upper": 2700000},
    ...
  ],
  "trends": {
    "overall": "increasing",
    "seasonality": "Q2 peak expected",
    "volatility": "moderate"
  },
  "visualization": {
    "type": "line",
    "data": {...}
  }
}
```

---

## 10. Frontend Integration

### 10.1 UI Components to Add

#### 10.1.1 Simulation Input Panel
```tsx
// components/SimulationPanel.tsx

interface SimulationPanelProps {
  dataset: string;
  availableModels: Model[];
}

const SimulationPanel: React.FC<SimulationPanelProps> = ({dataset, availableModels}) => {
  return (
    <div className="simulation-panel">
      <h3>🔮 Run Simulation</h3>
      
      {/* Model Selector */}
      <Select label="Model" options={availableModels} />
      
      {/* Scenario Builder */}
      <div className="scenario-builder">
        <h4>Modify Parameters</h4>
        <ParameterInput name="monthly_income" label="Monthly Income" type="percentage" />
        <ParameterInput name="overtime" label="Overtime" type="boolean" />
        <ParameterInput name="training_hours" label="Training Hours" type="number" />
      </div>
      
      {/* Quick Scenarios */}
      <div className="quick-scenarios">
        <button>Conservative (+10%)</button>
        <button>Moderate (+15%)</button>
        <button>Aggressive (+20%)</button>
      </div>
      
      <button className="run-simulation">Run Simulation</button>
    </div>
  );
};
```

#### 10.1.2 Comparison Visualization
```tsx
// components/ScenarioComparison.tsx

const ScenarioComparison: React.FC<{scenarios: Scenario[]}> = ({scenarios}) => {
  return (
    <div className="scenario-comparison">
      <h3>Scenario Comparison</h3>
      
      {/* Table View */}
      <table>
        <thead>
          <tr>
            <th>Scenario</th>
            <th>Prediction</th>
            <th>Change</th>
            <th>Cost</th>
            <th>ROI</th>
          </tr>
        </thead>
        <tbody>
          {scenarios.map(s => <tr>...</tr>)}
        </tbody>
      </table>
      
      {/* Chart View */}
      <Plot data={chartData} layout={layout} />
      
      {/* Recommendation */}
      <div className="recommendation">
        <strong>💡 Recommended:</strong> {recommendation}
      </div>
    </div>
  );
};
```

#### 10.1.3 Forecast Chart
```tsx
// components/ForecastChart.tsx

const ForecastChart: React.FC<{forecast: ForecastData}> = ({forecast}) => {
  return (
    <div className="forecast-chart">
      <Plot
        data={[
          {
            // Historical data
            x: historical.dates,
            y: historical.values,
            type: 'scatter',
            mode: 'lines',
            name: 'Historical'
          },
          {
            // Forecast
            x: forecast.dates,
            y: forecast.predictions,
            type: 'scatter',
            mode: 'lines',
            name: 'Forecast',
            line: {dash: 'dash'}
          },
          {
            // Confidence interval
            x: forecast.dates,
            y: forecast.upper,
            fill: 'tonexty',
            fillcolor: 'rgba(0,100,200,0.2)',
            type: 'scatter',
            mode: 'lines',
            name: 'Upper Bound'
          }
        ]}
        layout={{
          title: 'Sales Forecast - Next 6 Months',
          xaxis: {title: 'Month'},
          yaxis: {title: 'Sales (€)'}
        }}
      />
    </div>
  );
};
```

### 10.2 Chat Interface Updates

#### Add "Simulation" suggestion chips:
```tsx
<div className="suggestion-chips">
  <button>📊 What Questions</button>
  <button>❓ Why Questions</button>
  <button>🔮 Simulations</button>  {/* NEW */}
</div>
```

#### Example simulation prompts:
```tsx
const simulationExamples = [
  "What if we increase salaries by 15%?",
  "Predict sales for next quarter",
  "Compare 3 pricing scenarios",
  "What salary would reduce attrition to 10%?",
  "Simulate impact of 4-day work week"
];
```

### 10.3 Model Explorer Page

```tsx
// pages/ModelExplorer.tsx

const ModelExplorer = () => {
  return (
    <div className="model-explorer">
      <h2>🤖 Available ML Models</h2>
      
      {models.map(model => (
        <div className="model-card">
          <h3>{model.name}</h3>
          <p>{model.description}</p>
          <div className="model-stats">
            <span>Accuracy: {model.accuracy}</span>
            <span>Version: {model.version}</span>
            <span>Last Updated: {model.updated_at}</span>
          </div>
          <div className="model-actions">
            <button>Try Model</button>
            <button>View Details</button>
          </div>
        </div>
      ))}
    </div>
  );
};
```

---

## 11. Workflow & Orchestration

### 11.1 End-to-End Flow Example

```
┌──────────────────────────────────────────────────────────────────┐
│ USER INPUT                                                        │
│ "What if we increase salaries by 15% for Sales department?"     │
└──────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│ PLANNER AGENT                                                     │
│ • Classifies: SIMULATE question                                  │
│ • Extracts: department="Sales", parameter="monthly_income",     │
│             modification="+15%"                                   │
│ • Routes to: Simulation Agent                                    │
└──────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│ SIMULATION AGENT - Query Parser                                  │
│ • Parse: LLM extracts structured parameters                      │
│ • Identify: Model needed = "attrition_predictor"                │
│ • Scope: Filter employees where department="Sales"              │
└──────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│ DATA PREPARATION                                                  │
│ • Calls Text-to-SQL Agent:                                       │
│   "Get all Sales employees with features"                        │
│ • Receives: 125 employees × 20 features                         │
│ • Creates baseline scenario                                      │
│ • Creates what-if scenario (monthly_income * 1.15)              │
└──────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│ MODEL REGISTRY                                                    │
│ • Loads: attrition_predictor_v2.pkl                              │
│ • Loads: scaler.pkl                                              │
│ • Validates: All required features present                       │
└──────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│ PREDICTION ENGINE                                                 │
│ • Baseline prediction:                                           │
│   - 125 employees → 39 predicted to leave (31% attrition)       │
│ • What-If prediction:                                            │
│   - 125 employees → 24 predicted to leave (19% attrition)       │
│ • Delta: -12 percentage points, 15 employees saved              │
└──────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│ INSIGHT GENERATOR (LLM)                                          │
│ Prompt: "Interpret these results in business terms..."           │
│ Output:                                                           │
│ "By increasing salaries by 15% for the Sales department,        │
│  we can reduce attrition from 31% to 19%, preventing 15         │
│  employees from leaving. This represents:                        │
│  - Investment: $234,000 in annual salary increases              │
│  - Savings: $525,000 in replacement costs (avg $35K/hire)       │
│  - Net benefit: $291,000                                         │
│  - ROI: 2.2x                                                     │
│                                                                   │
│  Recommendation: Proceed with raise, prioritizing              │
│  high-performers and those with tenure > 2 years."              │
└──────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│ VISUALIZATION GENERATOR                                           │
│ • Chart 1: Bar chart (Baseline vs What-If attrition rate)       │
│ • Chart 2: Impact breakdown (employees saved, costs, ROI)       │
│ • Chart 3: Distribution of individual predictions                │
└──────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│ RESPONSE TO USER                                                  │
│ • Baseline results                                                │
│ • What-If results                                                 │
│ • Comparison metrics                                              │
│ • Visualizations (3 charts)                                       │
│ • LLM insights                                                    │
│ • Recommendations                                                 │
│ • Confidence: 91% model accuracy                                 │
└──────────────────────────────────────────────────────────────────┘
```

### 11.2 Agent Collaboration Matrix

| Agent | Calls → | Purpose |
|-------|---------|---------|
| Planner | Simulation | Route SIMULATE questions |
| Simulation | Text-to-SQL | Fetch baseline data |
| Simulation | Model Registry | Load ML models |
| Simulation | Scenario Engine | Create what-if scenarios |
| Simulation | Prediction Service | Run model inference |
| Simulation | LLM | Generate insights |
| Simulation | Visualization | Create charts |

---

## 12. Implementation Phases

### Phase 1: MVP (Weeks 1-3) ✅

**Goal**: Single model, basic what-if analysis

#### Week 1: Foundation
- [ ] Create database schema (ml_models, simulation_history)
- [ ] Build Model Registry class
- [ ] Build Prediction Service class
- [ ] Train simple attrition model (Random Forest)
- [ ] Save model with metadata

#### Week 2: Core Agent
- [ ] Implement simulation_agent.py (basic version)
- [ ] Implement scenario_engine.py
- [ ] Update planner to recognize SIMULATE questions
- [ ] Add simulation routes to API
- [ ] Test end-to-end with one model

#### Week 3: Integration & UI
- [ ] Integrate with multi_agent_system.py
- [ ] Build frontend SimulationPanel component
- [ ] Build ScenarioComparison component
- [ ] Add example prompts
- [ ] Test with HR dataset

**Deliverables**:
- Working simulation for employee attrition
- Basic what-if analysis (single parameter)
- API endpoints functional
- UI for running simulations

---

### Phase 2: Enhanced Features (Weeks 4-6)

**Goal**: Multi-scenario, optimization, better UX

#### Week 4: Advanced Scenarios
- [ ] Multi-scenario comparison (run 3-5 scenarios)
- [ ] Sensitivity analysis (vary one parameter)
- [ ] Batch predictions (department-wide)
- [ ] Parameter optimization (target achievement)

#### Week 5: Additional Models
- [ ] Train sales forecasting model
- [ ] Train time-series model (if applicable)
- [ ] Support multiple model types
- [ ] Model versioning system

#### Week 6: UX Enhancements
- [ ] Enhanced visualizations (comparison charts)
- [ ] Model Explorer page
- [ ] Simulation history view
- [ ] Preset scenarios
- [ ] Export results (PDF, CSV)

**Deliverables**:
- Multiple models deployed
- Advanced simulation features
- Polished UI
- Documentation

---

### Phase 3: Production-Ready (Weeks 7-9)

**Goal**: MLOps, monitoring, scalability

#### Week 7: MLOps
- [ ] MLflow integration
- [ ] Model versioning & staging
- [ ] A/B testing framework
- [ ] Automated retraining pipeline
- [ ] Model performance monitoring

#### Week 8: Performance & Scale
- [ ] Caching for predictions
- [ ] Async batch processing
- [ ] Query optimization
- [ ] Load testing
- [ ] Error handling & retries

#### Week 9: Production Deployment
- [ ] Comprehensive testing
- [ ] Performance benchmarks
- [ ] Security audit
- [ ] Documentation (user guide, API docs)
- [ ] Deployment to production

**Deliverables**:
- Production-ready system
- MLOps pipeline
- Monitoring & alerting
- Complete documentation

---

### Phase 4: Advanced Features (Weeks 10-12)

**Goal**: AI enhancements, advanced analytics

- [ ] Explainable AI (SHAP values for predictions)
- [ ] Automated scenario generation (AI suggests scenarios)
- [ ] Multi-objective optimization
- [ ] Ensemble modeling
- [ ] Real-time monitoring & drift detection
- [ ] Custom model upload (data scientists can deploy)

---

## 13. Technical Stack

### 13.1 Backend

```python
# Core ML Libraries
scikit-learn>=1.3.0        # ML models
xgboost>=2.0.0             # Gradient boosting
lightgbm>=4.0.0            # Gradient boosting
statsmodels>=0.14.0        # Time series (ARIMA)
prophet>=1.1.0             # Facebook's time series

# Model Management
mlflow>=2.9.0              # Model registry & tracking
joblib>=1.3.0              # Model serialization

# Optimization
scipy>=1.11.0              # Optimization algorithms
optuna>=3.5.0              # Hyperparameter tuning

# Explainability
shap>=0.43.0               # Model explanations

# Existing
fastapi>=0.100.0
langchain>=0.1.0
plotly>=5.18.0
pandas>=2.0.0
```

### 13.2 Frontend

```json
{
  "dependencies": {
    "react": "^18.0.0",
    "plotly.js": "^2.27.0",
    "react-plotly.js": "^2.6.0"
  }
}
```

### 13.3 Infrastructure

- **Database**: PostgreSQL (existing)
- **Model Storage**: Local files (MVP) → Azure Blob (Production)
- **Model Registry**: MLflow (Production)
- **Caching**: Redis (optional, for performance)
- **Queue**: Celery (optional, for async batch jobs)

---

## 14. Testing Strategy

### 14.1 Unit Tests

```python
# tests/test_simulation_agent.py

def test_parse_simulation_query():
    """Test query parsing extracts correct parameters."""
    query = "What if we increase salaries by 15%?"
    parsed = parse_simulation_query(query)
    assert parsed["parameter"] == "monthly_income"
    assert parsed["modification"] == "*1.15"

def test_scenario_engine():
    """Test scenario creation."""
    baseline = {"monthly_income": 5000}
    modification = {"monthly_income": "*1.15"}
    scenario = create_scenario(baseline, modification)
    assert scenario["monthly_income"] == 5750

def test_model_prediction():
    """Test model loads and predicts correctly."""
    model = load_model("attrition_predictor")
    input_data = {...}
    prediction = model.predict(input_data)
    assert 0 <= prediction <= 1  # Probability
```

### 14.2 Integration Tests

```python
def test_end_to_end_simulation():
    """Test full simulation workflow."""
    question = "What if we increase salaries by 15%?"
    result = await process_question(question, llm)
    
    assert result["success"] == True
    assert result["question_type"] == "SIMULATE"
    assert "baseline_prediction" in result
    assert "whatif_prediction" in result
    assert "visualizations" in result
```

### 14.3 Model Tests

```python
def test_model_accuracy():
    """Test model meets accuracy threshold."""
    X_test, y_test = load_test_data()
    model = load_model("attrition_predictor")
    accuracy = model.score(X_test, y_test)
    assert accuracy >= 0.85  # Minimum threshold

def test_model_inference_time():
    """Test prediction latency."""
    model = load_model("attrition_predictor")
    start = time.time()
    prediction = model.predict(test_input)
    duration = time.time() - start
    assert duration < 0.1  # Max 100ms
```

### 14.4 User Acceptance Tests

1. **Scenario**: Basic what-if analysis
   - User asks: "What if salaries increase 10%?"
   - Expected: Correct baseline, what-if, and comparison

2. **Scenario**: Multi-scenario comparison
   - User asks: "Compare 3 salary increase scenarios"
   - Expected: Table with all scenarios, recommendation

3. **Scenario**: Optimization
   - User asks: "What raise reduces attrition to 10%?"
   - Expected: Optimal parameter value

4. **Scenario**: Error handling
   - User asks simulation question but invalid parameter
   - Expected: Graceful error with suggestions

---

## 15. Deployment & MLOps

### 15.1 Model Deployment Workflow

```
┌───────────────────────────────────────────────────────────────┐
│                    DATA SCIENTIST                              │
│  1. Train model in notebook                                   │
│  2. Evaluate performance                                      │
│  3. Register in MLflow                                        │
└───────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│                    MODEL REGISTRY                              │
│  • Model stored with version                                  │
│  • Metadata: features, performance, date                      │
│  • Status: Development                                        │
└───────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│                    STAGING ENVIRONMENT                         │
│  • Automated tests run                                        │
│  • A/B test vs current production model                      │
│  • Performance validation                                     │
└───────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│                  PRODUCTION DEPLOYMENT                         │
│  • Gradual rollout (10% → 50% → 100%)                        │
│  • Monitor performance metrics                                │
│  • Rollback capability                                        │
└───────────────────────────────────────────────────────────────┘
```

### 15.2 Monitoring

#### Model Performance Monitoring
```python
# Track in database
CREATE TABLE model_performance_log (
    log_id SERIAL PRIMARY KEY,
    model_id INT REFERENCES ml_models(model_id),
    prediction_date DATE,
    num_predictions INT,
    avg_confidence FLOAT,
    actual_vs_predicted_accuracy FLOAT  -- When ground truth available
);
```

#### Prediction Monitoring
- Track prediction distribution (detect drift)
- Monitor inference latency
- Track error rates
- Alert if model performance degrades

#### Business Metrics
- Track adoption (simulation queries per day)
- Track user satisfaction
- Track action taken on recommendations

### 15.3 Retraining Strategy

```python
# Automated retraining trigger
if model_performance < threshold:
    trigger_retrain()

if days_since_training > 90:
    trigger_retrain()

if concept_drift_detected:
    trigger_retrain()
```

---

## 16. Future Enhancements

### 16.1 Advanced AI Features

1. **Automated Scenario Generation**
   ```
   User: "Suggest ways to reduce attrition"
   AI: Generates 5 intelligent scenarios based on feature importance
   ```

2. **Explainable AI (XAI)**
   - SHAP values for predictions
   - Feature importance explanations
   - Counterfactual explanations

3. **Multi-Objective Optimization**
   - Optimize for multiple goals (reduce cost AND improve retention)
   - Pareto frontier analysis

4. **Reinforcement Learning**
   - Sequential decision optimization
   - Learn optimal policy over time

### 16.2 Advanced Model Types

1. **Deep Learning Models**
   - Neural networks for complex patterns
   - LSTM for time series

2. **Causal Inference Models**
   - DoWhy, CausalML integration
   - True causal impact estimation

3. **Survival Analysis**
   - Time-to-event modeling (time until attrition)
   - Cox proportional hazards

### 16.3 Enterprise Features

1. **What-If Templates**
   - Pre-built scenarios for common business questions
   - Industry-specific templates

2. **Collaborative Simulations**
   - Share scenarios with team
   - Comment and discuss

3. **Scheduled Simulations**
   - Auto-run monthly forecasts
   - Email reports

4. **Custom Model Upload**
   - Data scientists upload their own models
   - Standardized interface

5. **Multi-Cloud Support**
   - AWS SageMaker integration
   - Google Vertex AI integration

---

## 17. Summary & Next Steps

### 17.1 Why This Agent is Valuable

1. **Democratizes ML**: Business users can leverage ML without technical skills
2. **Accelerates Decisions**: Test strategies quickly before implementation
3. **Bridges Data Science & Business**: Makes ML models actually useful
4. **Extends Your Platform**: Natural evolution from descriptive → causal → predictive
5. **Competitive Advantage**: Few analytics tools have true what-if simulation

### 17.2 Success Metrics

- **Adoption**: 50+ simulation queries per week
- **Accuracy**: Model predictions 85%+ accurate
- **Latency**: Predictions return in < 2 seconds
- **User Satisfaction**: 4.5/5 rating
- **Business Impact**: Users act on recommendations 60%+ of time

### 17.3 Immediate Next Steps

1. **Week 1 - Planning**
   - Review this plan with team
   - Prioritize use cases
   - Identify datasets for initial models

2. **Week 1-2 - Infrastructure**
   - Set up database tables
   - Create model storage structure
   - Build Model Registry class

3. **Week 2-3 - First Model**
   - Train employee attrition model
   - Implement basic simulation_agent
   - Test end-to-end

4. **Week 3-4 - Integration**
   - Update planner agent
   - Add API endpoints
   - Build frontend components

5. **Week 4+ - Iterate**
   - Add more models
   - Enhance features
   - Gather user feedback

---

## 📚 Resources & References

### ML Model Development
- Scikit-learn: https://scikit-learn.org/
- XGBoost: https://xgboost.readthedocs.io/
- MLflow: https://mlflow.org/

### Explainable AI
- SHAP: https://shap.readthedocs.io/
- LIME: https://github.com/marcotcr/lime

### Optimization
- SciPy Optimize: https://docs.scipy.org/doc/scipy/reference/optimize.html
- Optuna: https://optuna.org/

### Time Series
- Prophet: https://facebook.github.io/prophet/
- Statsmodels: https://www.statsmodels.org/

---

**Ready to build the future of analytics!** 🚀

This agent will transform your multi-agent assistant into a comprehensive analytics platform that handles:
- ✅ **WHAT** questions (descriptive)
- ✅ **WHY** questions (causal)
- ✅ **WHAT IF** questions (predictive) ← NEW!

Let's make it happen! 💪
