"""
Simulation Agent for Multi-Agent Analytics System
===================================================
Runs what-if, multi-scenario, optimization, and sensitivity simulations
using pre-trained scikit-learn pipelines stored in simulation_models/.

Supports:
  - employee_attrition_predictor  (RandomForest, classification)
  - sales_revenue_predictor       (GradientBoosting, regression)

Author: Yogarajaadithya
Date: February 2026
"""

import os
import re
import json
import warnings
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import quote_plus

import numpy as np
import pandas as pd
import joblib
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate

warnings.filterwarnings("ignore")
load_dotenv(override=True)

# ── Path resolution ────────────────────────────────────────────────────────
# backend-repo/app/services/simulation_agent.py → up 3 levels → project root
_SERVICE_DIR = Path(__file__).resolve().parent          # .../app/services/
_BACKEND_DIR = _SERVICE_DIR.parent.parent               # .../backend-repo/
_PROJECT_ROOT = _BACKEND_DIR.parent                     # workspace root
MODELS_DIR = _PROJECT_ROOT / "simulation_models"


# ══════════════════════════════════════════════════════════════════════════════
# PROMPTS
# ══════════════════════════════════════════════════════════════════════════════

SIMULATION_QUERY_PARSER_PROMPT = """\
You are an expert analytics AI that extracts structured parameters from natural language simulation questions.

Given the user's question below, extract the simulation parameters and return ONLY valid JSON.

Question: {question}

Available model: {model_name}
Available features: {feature_list}
Dataset: {dataset}

Return JSON with this exact structure:
{{
  "simulation_type": "whatif" | "multi_scenario" | "optimization" | "sensitivity",
  "scope_filter": {{"actual_column_name": "comparison_value"}} or null,
  "modifications": {{"feature_name": "modification_expression"}},
  "scenarios": [
    {{"name": "Scenario Name", "modifications": {{"feature_name": "expression"}}}}
  ],
  "optimization_target": {{"metric": "attrition_rate", "target_value": 0.10}} or null,
  "optimization_parameter": "feature_name" or null,
  "explanation": "Brief explanation of what was parsed"
}}

IMPORTANT scope_filter rules:
- Keys MUST be real column names from the feature list (e.g. "yearssincelastpromotion", "department")
- NEVER use keys named "column" or "value" — these are not column names
- Comparison values use operators: ">=3", "<=5", ">2", "<10", "=Sales"
- Categorical equality: {{"department": "Sales"}}, {{"overtime": "Yes"}}
- Numeric threshold: {{"yearssincelastpromotion": ">=3"}}, {{"monthlyincome": "<3000"}}
- If the question applies to ALL employees, set scope_filter to null

Modification expression format:
- Percentage increase (+15%): "*1.15"
- Percentage decrease (-10%): "*0.90"
- Add absolute value (+500): "+500"
- Set absolute value: "=5000"
- Set categorical: "Yes" or "No"
- Reset to zero (e.g. promotion reset): "=0"

Map user intent to actual feature names (HR):
- salary / income / pay / raise / bonus / performance bonus / incentive / compensation → monthlyincome
- overtime / overwork → overtime
- satisfaction → jobsatisfaction
- training → trainingtimeslastyear
- promotion → yearssincelastpromotion
- distance / commute → distancefromhome
- work life balance → worklifebalance
- environment → environmentsatisfaction
- stock options → stockoptionlevel
- performance rating / rating / performance score → performancerating (use as scope_filter with value "=4" for rating 4)

Bonus / incentive inference rules:
- "introduce a bonus" → increase monthlyincome by 10%: use "*1.10"
- "performance-based bonus" → increase monthlyincome by 10%: use "*1.10"
- "give a bonus" without a specific amount → default to "*1.10"
- If a specific bonus amount (e.g. 15%) is mentioned, use that percentage
- NEVER output a descriptive string like "performance-based bonus" as a modification value — always convert to a numeric expression like "*1.10"

Map user intent to actual feature names (Sales):
- price / pricing / unit price / prices → price
- discount / discounts → discount
- quantity / quantities / units → quantity
- revenue / sales → revenue
- shipping / shipping cost / delivery cost → shippingcost
- delivery / delivery time / delivery days → deliverydays
- rating / ratings → rating
- promo code / promo codes / promotional code → promocodeused
- review / reviews / review count → reviewcount
- channel / acquisition channel / marketing channel → acquisitionchannel
- customer type / customer segment / segment → customersegment
- device / device type → devicetype
- category / product category → category
- brand / brands → brand
- city / location / region → city
- age / age group → agegroup
- gender → gender

CRITICAL: Sales dataset valid categorical values — USE THESE EXACT STRINGS:
- category: "Clothing", "Shoes", "Accessories", "Beauty", "Sports"
  • "Women Clothing", "Women's Clothing", "women clothing", "clothing" → use "Clothing"
  • "Women Shoes", "Women's Shoes", "women shoes", "shoes", "footwear" → use "Shoes"
  • "accessories", "handbags", "bags" → use "Accessories"
  • "beauty", "cosmetics" → use "Beauty"
  • "sports", "sportswear" → use "Sports"
- customersegment: "New", "Returning", "VIP"
  • "loyal", "loyal customers", "regular" → use "Returning"
  • "vip", "premium", "high value" → use "VIP"
  • "new", "new customers", "first-time" → use "New"
- devicetype: "Desktop", "Mobile", "Tablet"
- acquisitionchannel: "Direct", "Email", "Organic Search", "Paid Advertising", "Referral", "Social Media"
  • "paid search", "paid ads", "ads" → use "Paid Advertising"
  • "organic", "organic search" → use "Organic Search"
  • "social", "social media" → use "Social Media"
- city valid values: "Berlin", "Cologne", "Hamburg", "Munich", "Frankfurt am Main",
  "Stuttgart", "Dortmund", "Dresden", "Dusseldorf", "Essen"
- orderstatus: "Delivered", "Returned", "Cancelled", "Processing"
- gender: "Male", "Female"
- agegroup: "18-24", "25-34", "35-44", "45-54", "55+"
- promocodeused: "Yes", "No"

Return ONLY the JSON, no markdown, no explanation.
"""

SIMULATION_INSIGHT_PROMPT = """\
You are a business analytics expert. Interpret these simulation results in clear, actionable business language.

Question asked: {question}
Dataset: {dataset}

Simulation Results:
{results_summary}

Model confidence: {model_accuracy}

Please provide:
1. **Key Finding Summary** — 2-3 sentences summarising the main result
2. **Business Impact Analysis** — ROI, cost-benefit if applicable, specific numbers
3. **Actionable Recommendations** — 2-3 specific, numbered recommendations
4. **Caveats and Risks** — important limitations or risks to flag

Keep the tone professional but accessible to business users who are not data scientists.
"""


# ══════════════════════════════════════════════════════════════════════════════
# CORE CLASSES
# ══════════════════════════════════════════════════════════════════════════════

class ModelRegistry:
    """
    Manages ML model lifecycle: registration, loading, versioning.
    Models are stored as joblib pipelines with JSON metadata.
    """

    def __init__(self, models_dir: Path = None):
        self.models_dir = models_dir or MODELS_DIR
        self.registry_path = self.models_dir / "model_registry.json"
        self._loaded_models: Dict[str, Any] = {}

    def _load_registry(self) -> dict:
        if self.registry_path.exists():
            with open(self.registry_path) as f:
                return json.load(f)
        return {"models": {}}

    def list_models(self) -> list:
        return list(self._load_registry().get("models", {}).keys())

    def get_model_metadata(self, model_name: str) -> dict:
        registry = self._load_registry()
        info = registry["models"].get(model_name)
        if not info:
            raise ValueError(
                f"Model '{model_name}' not in registry. Available: {self.list_models()}"
            )
        config_path = self.models_dir.parent / info["config_path"]
        with open(config_path) as f:
            return json.load(f)

    def get_feature_metadata(self, model_name: str) -> dict:
        meta = self.get_model_metadata(model_name)
        feat_path = self.models_dir.parent / meta["features_path"]
        with open(feat_path) as f:
            return json.load(f)

    def load_model(self, model_name: str):
        if model_name in self._loaded_models:
            return self._loaded_models[model_name]
        meta = self.get_model_metadata(model_name)
        pipeline_path = self.models_dir.parent / meta["pipeline_path"]
        pipe = joblib.load(pipeline_path)
        self._loaded_models[model_name] = pipe
        return pipe

    def detect_model_for_question(self, question: str, dataset: str) -> str:
        question_lower = question.lower()
        registry = self._load_registry()

        keyword_model_map = {
            # HR keywords → attrition model
            "attrition": "employee_attrition_predictor",
            "turnover": "employee_attrition_predictor",
            "resign": "employee_attrition_predictor",
            "quit": "employee_attrition_predictor",
            "retention": "employee_attrition_predictor",
            "salary": "employee_attrition_predictor",
            "salaries": "employee_attrition_predictor",
            "overtime": "employee_attrition_predictor",
            "employee": "employee_attrition_predictor",
            "employees": "employee_attrition_predictor",
            "hire": "employee_attrition_predictor",
            "pay raise": "employee_attrition_predictor",
            "job satisfaction": "employee_attrition_predictor",
            # Sales keywords → revenue model
            "revenue": "sales_revenue_predictor",
            "sales": "sales_revenue_predictor",
            "profit": "sales_revenue_predictor",
            "discount": "sales_revenue_predictor",
            "price": "sales_revenue_predictor",
            "prices": "sales_revenue_predictor",
            "pricing": "sales_revenue_predictor",
            "priced": "sales_revenue_predictor",
            "order": "sales_revenue_predictor",
            "orders": "sales_revenue_predictor",
            "channel": "sales_revenue_predictor",
            "marketing": "sales_revenue_predictor",
            "promotion": "sales_revenue_predictor",
            "promo": "sales_revenue_predictor",
            "product": "sales_revenue_predictor",
            "category": "sales_revenue_predictor",
            "shipping": "sales_revenue_predictor",
            "quantity": "sales_revenue_predictor",
            "loyal": "sales_revenue_predictor",
            "customer": "sales_revenue_predictor",
            "segment": "sales_revenue_predictor",
            "brand": "sales_revenue_predictor",
            "delivery": "sales_revenue_predictor",
            "mobile": "sales_revenue_predictor",
            "desktop": "sales_revenue_predictor",
            "zalando": "sales_revenue_predictor",
            "e-commerce": "sales_revenue_predictor",
            "ecommerce": "sales_revenue_predictor",
        }

        models_registry = registry.get("models", {})

        # First pass: keyword match that also respects the active dataset
        for keyword, model_name in keyword_model_map.items():
            if keyword in question_lower and model_name in models_registry:
                model_dataset = models_registry[model_name].get("dataset", "")
                if dataset and model_dataset and model_dataset != dataset:
                    # Skip: this keyword's model doesn't belong to the active dataset
                    continue
                return model_name

        # Fallback: first model matching the dataset
        for name, info in registry.get("models", {}).items():
            if info.get("dataset") == dataset:
                return name

        raise ValueError(
            f"No suitable model for dataset='{dataset}' and question: {question[:80]}"
        )


class ScenarioEngine:
    """
    Pure-static class that applies modifications to a DataFrame copy.

    Modification syntax:
      '*1.15'  → multiply by 1.15 (+15%)
      '+500'   → add 500
      '=5000'  → set to 5000
      '-500'   → subtract 500
      'Yes'    → set categorical value
    """

    @staticmethod
    def _apply_modification(original_value, modification):
        if isinstance(modification, str):
            mod = modification.strip()
            if mod.startswith("*"):
                try:
                    return round(float(original_value) * float(mod[1:]), 2)
                except (ValueError, TypeError):
                    return original_value
            elif mod.startswith("+") and not mod[1:].startswith("-"):
                try:
                    return round(float(original_value) + float(mod[1:]), 2)
                except (ValueError, TypeError):
                    return original_value
            elif mod.startswith("="):
                try:
                    return float(mod[1:])
                except ValueError:
                    return mod[1:]
            elif mod.startswith("-") and len(mod) > 1:
                try:
                    return round(float(original_value) - float(mod[1:]), 2)
                except (ValueError, TypeError):
                    return original_value
            else:
                # Check if this looks like a descriptive phrase (contains spaces or letters
                # that cannot form a numeric expression) — treat as no-op for numeric columns
                try:
                    return float(mod)
                except ValueError:
                    # If the original value is numeric and mod is a non-numeric phrase,
                    # default to a 10% increase (e.g. "introduce a bonus" fallback)
                    if isinstance(original_value, (int, float)):
                        import warnings
                        warnings.warn(
                            f"Non-numeric modification '{mod}' on numeric column; "
                            "defaulting to +10% increase."
                        )
                        return round(float(original_value) * 1.10, 2)
                    return mod
        return modification

    @classmethod
    def create_scenario(
        cls,
        baseline_df: pd.DataFrame,
        modifications: dict,
        scenario_name: str = "What-If",
    ) -> pd.DataFrame:
        whatif_df = baseline_df.copy()
        for col, mod in modifications.items():
            if col not in whatif_df.columns:
                continue
            whatif_df[col] = whatif_df[col].apply(
                lambda v: cls._apply_modification(v, mod)
            )
        return whatif_df

    @classmethod
    def sensitivity_analysis(
        cls,
        baseline_df: pd.DataFrame,
        parameter: str,
        range_modifications: list,
    ) -> list:
        scenarios = []
        for mod in range_modifications:
            df_mod = cls.create_scenario(baseline_df, {parameter: mod})
            df_mod = df_mod.copy()
            df_mod["_scenario_label"] = f"{parameter}: {mod}"
            df_mod["_modification"] = str(mod)
            scenarios.append(df_mod)
        return scenarios


class PredictionService:
    """Runs ML model inference for classification and regression pipelines."""

    def __init__(self, registry: ModelRegistry = None):
        self.registry = registry or ModelRegistry()

    def _prepare_input(
        self, input_df: pd.DataFrame, model_name: str
    ) -> pd.DataFrame:
        feat_meta = self.registry.get_feature_metadata(model_name)
        required = feat_meta["all_features"]
        missing = [f for f in required if f not in input_df.columns]
        if missing:
            raise ValueError(f"Missing required feature columns: {missing}")
        return input_df[required]

    def predict(self, model_name: str, input_df: pd.DataFrame) -> dict:
        meta = self.registry.get_model_metadata(model_name)
        pipe = self.registry.load_model(model_name)
        X = self._prepare_input(input_df, model_name)
        mtype = meta.get("model_type", "classification")

        if mtype == "classification":
            preds = pipe.predict(X)
            probas = pipe.predict_proba(X)[:, 1]
            high_risk = (probas >= 0.60).sum()
            medium_risk = ((probas >= 0.35) & (probas < 0.60)).sum()
            low_risk = (probas < 0.35).sum()
            aggregate = {
                "attrition_rate": round(float(probas.mean()), 4),
                "predicted_leavers": int(preds.sum()),
                "predicted_stayers": int((preds == 0).sum()),
                "high_risk_count": int(high_risk),
                "medium_risk_count": int(medium_risk),
                "low_risk_count": int(low_risk),
            }
            return {
                "model_name": model_name,
                "model_type": mtype,
                "n_records": len(preds),
                "predictions": preds.tolist(),
                "probabilities": probas.tolist(),
                "aggregate": aggregate,
            }
        else:
            preds = pipe.predict(X)
            aggregate = {
                "mean_revenue": round(float(preds.mean()), 2),
                "total_revenue": round(float(preds.sum()), 2),
                "median_revenue": round(float(np.median(preds)), 2),
                "min_revenue": round(float(preds.min()), 2),
                "max_revenue": round(float(preds.max()), 2),
                "n_transactions": int(len(preds)),
            }
            return {
                "model_name": model_name,
                "model_type": mtype,
                "n_records": len(preds),
                "predictions": preds.tolist(),
                "aggregate": aggregate,
            }

    def compare_scenarios(
        self, model_name: str, scenarios: list
    ) -> pd.DataFrame:
        meta = self.registry.get_model_metadata(model_name)
        mtype = meta.get("model_type", "classification")
        rows = []
        for name, df in scenarios:
            result = self.predict(model_name, df)
            agg = result["aggregate"]
            if mtype == "classification":
                rows.append(
                    {
                        "Scenario": name,
                        "Attrition Rate": f"{agg['attrition_rate'] * 100:.1f}%",
                        "Attrition Rate (raw)": agg["attrition_rate"],
                        "Predicted Leavers": agg["predicted_leavers"],
                        "High Risk": agg["high_risk_count"],
                        "Medium Risk": agg["medium_risk_count"],
                        "Low Risk": agg["low_risk_count"],
                    }
                )
            else:
                rows.append(
                    {
                        "Scenario": name,
                        "Mean Revenue (€)": agg["mean_revenue"],
                        "Total Revenue (€)": agg["total_revenue"],
                        "Median Revenue (€)": agg["median_revenue"],
                        "Transactions": agg["n_transactions"],
                    }
                )
        return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def _get_db_engine(schema: str = "hr_data"):
    """Build a SQLAlchemy engine using env-var credentials."""
    from urllib.parse import quote_plus

    encoded_pw = quote_plus(os.getenv("DB_PASSWORD", ""))
    url = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{encoded_pw}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    return create_engine(
        url, connect_args={"options": f"-csearch_path={schema}"}
    )


def _sanitize_scope_filter(scope_filter: dict, known_features: list = None) -> dict:
    """
    Sanitize malformed scope_filter produced by the LLM.
    Handles the case where the LLM returns {"column": "col_name", "value": ">=3"}
    instead of the correct format {"col_name": ">=3"}.
    """
    if not scope_filter:
        return scope_filter
    # Detect malformed pattern: keys are literally "column" and "value"
    if "column" in scope_filter and "value" in scope_filter:
        col = scope_filter["column"]
        val = scope_filter["value"]
        return {col: val}
    # Also drop any keys that are not real feature names if known_features provided
    if known_features:
        cleaned = {k: v for k, v in scope_filter.items() if k in known_features}
        if cleaned:
            return cleaned
    return scope_filter


# Maps common LLM-hallucinated or user-friendly values to actual DB values
_SCOPE_VALUE_ALIASES: Dict[str, Dict[str, str]] = {
    "category": {
        "women clothing": "Clothing",
        "women's clothing": "Clothing",
        "womens clothing": "Clothing",
        "clothing": "Clothing",
        "women shoes": "Shoes",
        "women's shoes": "Shoes",
        "womens shoes": "Shoes",
        "shoes": "Shoes",
        "footwear": "Shoes",
        "accessories": "Accessories",
        "handbags": "Accessories",
        "beauty": "Beauty",
        "cosmetics": "Beauty",
        "sports": "Sports",
        "sportswear": "Sports",
    },
    "customersegment": {
        "loyal": "Returning",
        "loyal customers": "Returning",
        "regular": "Returning",
        "returning": "Returning",
        "returning customers": "Returning",
        "vip": "VIP",
        "premium": "VIP",
        "high value": "VIP",
        "new": "New",
        "new customers": "New",
        "first-time": "New",
    },
    "devicetype": {
        "mobile": "Mobile",
        "mobile device": "Mobile",
        "smartphone": "Mobile",
        "desktop": "Desktop",
        "pc": "Desktop",
        "tablet": "Tablet",
    },
    "acquisitionchannel": {
        "paid search": "Paid Advertising",
        "paid ads": "Paid Advertising",
        "ads": "Paid Advertising",
        "paid advertising": "Paid Advertising",
        "organic": "Organic Search",
        "organic search": "Organic Search",
        "social": "Social Media",
        "social media": "Social Media",
        "email": "Email",
        "direct": "Direct",
        "referral": "Referral",
    },
    "orderstatus": {
        "delivered": "Delivered",
        "returned": "Returned",
        "cancelled": "Cancelled",
        "canceled": "Cancelled",
        "processing": "Processing",
    },
    "gender": {
        "male": "Male",
        "female": "Female",
        "m": "Male",
        "f": "Female",
    },
    "promocodeused": {
        "yes": "Yes",
        "no": "No",
        "true": "Yes",
        "false": "No",
    },
}


def _normalize_scope_values(scope_filter: dict) -> dict:
    """
    Normalize LLM-produced scope filter values to actual DB values using alias map.
    E.g. {"category": "Women Clothing"} → {"category": "Clothing"}
    """
    if not scope_filter:
        return scope_filter
    result = {}
    for col, val in scope_filter.items():
        val_str = str(val).strip()
        aliases = _SCOPE_VALUE_ALIASES.get(col, {})
        normalized = aliases.get(val_str.lower(), val_str)
        result[col] = normalized
    return result


def _rescue_scope_filter(scope_filter: dict, cat_features: list = None) -> tuple:
    """
    Detect scope_filter entries that are actually numeric absolute-value
    modifications (e.g. ``shippingcost: "=2"``) and split them out.

    The LLM sometimes classifies a modification like "reduce shipping cost to €2"
    as a scope_filter condition, which produces ``WHERE shippingcost = 2`` and
    returns 0 rows.  This function moves such entries to a separate
    ``rescued_mods`` dict so they can be applied as scenario modifications
    instead of SQL filters.

    Entries that are safe to keep as filters:
      - Categorical columns (listed in cat_features) with any equality
      - Numeric columns with comparison operators (>=, <=, >, <)

    Entries to rescue (move to modifications):
      - Numeric absolute-value assignments on numeric columns: "=<float>"
        where the target value is unlikely to match any existing row exactly.

    Returns:
        (safe_scope_filter, rescued_mods)
    """
    if not scope_filter:
        return scope_filter, {}

    safe: dict = {}
    rescued: dict = {}

    cat_cols = set(cat_features or [])

    for col, val in scope_filter.items():
        val_str = str(val).strip()
        # Keep categorical filters as-is
        if col in cat_cols:
            safe[col] = val
            continue
        # Numeric equality assignment like "=2" or "=5.99"
        if val_str.startswith("="):
            operand = val_str[1:].strip()
            try:
                float(operand)
                # Absolute numeric setter → move to modifications
                rescued[col] = val_str
                continue
            except ValueError:
                pass
        # Comparison operators on numeric cols are valid filters
        safe[col] = val

    return safe, rescued


def _build_where_condition(col: str, val: str) -> str:
    """
    Build a SQL WHERE condition fragment, supporting comparison operators.
    val can be: ">=3", "<=5", ">2", "<10", "!='Yes'", "=Sales", "Sales", "3"
    """
    val = str(val).strip()
    # Detect leading operator
    for op in ("!=", ">=", "<=", ">", "<", "="):
        if val.startswith(op):
            operand = val[len(op):].strip()
            # Numeric?
            try:
                float(operand)
                return f"{col} {op} {operand}"
            except ValueError:
                return f"{col} {op} '{operand}'"
    # No operator — plain equality
    try:
        float(val)
        return f"{col} = {val}"
    except ValueError:
        return f"{col} = '{val}'"


def fetch_baseline_data(
    dataset: str = "hr_data",
    table: str = "employee_attrition",
    features: list = None,
    scope_filter: dict = None,
) -> pd.DataFrame:
    """Fetch rows from PostgreSQL for baseline simulation."""
    engine = _get_db_engine(dataset)
    cols = ", ".join(features) if features else "*"
    query = f"SELECT {cols} FROM {dataset}.{table}"
    if scope_filter:
        scope_filter = _sanitize_scope_filter(scope_filter, features)
        scope_filter = _normalize_scope_values(scope_filter)
        if scope_filter:
            conditions = " AND ".join(
                [_build_where_condition(col, val) for col, val in scope_filter.items()]
            )
            query += f" WHERE {conditions}"
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    return df


def optimize_parameter(
    pred_service: PredictionService,
    model_name: str,
    baseline_df: pd.DataFrame,
    parameter: str,
    target_metric: str,
    target_value: float,
    search_range: tuple = (1.0, 2.0),
    steps: int = 20,
) -> dict:
    """Linear search for the minimum multiplier that hits target_value."""
    multipliers = np.linspace(search_range[0], search_range[1], steps)
    results = []
    for mult in multipliers:
        df_mod = ScenarioEngine.create_scenario(
            baseline_df, {parameter: f"*{mult:.3f}"}
        )
        res = pred_service.predict(model_name, df_mod)
        metric_val = res["aggregate"].get(target_metric)
        results.append({"multiplier": mult, target_metric: metric_val})

    results_df = pd.DataFrame(results)
    achieved = results_df[results_df[target_metric] <= target_value]
    if achieved.empty:
        best = results_df.iloc[results_df[target_metric].idxmin()]
        target_met = False
    else:
        best = achieved.iloc[0]
        target_met = True

    optimal_mult = float(best["multiplier"])
    achieved_value = float(best[target_metric])
    return {
        "parameter": parameter,
        "target_metric": target_metric,
        "target_value": target_value,
        "optimal_multiplier": round(optimal_mult, 3),
        "percent_change_needed": round((optimal_mult - 1.0) * 100, 1),
        "achieved_value": round(achieved_value, 4),
        "target_met": target_met,
        "search_curve": results_df,
    }


async def parse_simulation_query(
    question: str,
    model_name: str,
    feature_list: list,
    dataset: str,
    llm,
) -> dict:
    """Use LLM to extract structured simulation params from natural language."""
    prompt = PromptTemplate(
        input_variables=["question", "model_name", "feature_list", "dataset"],
        template=SIMULATION_QUERY_PARSER_PROMPT,
    )
    chain = prompt | llm
    response = await chain.ainvoke(
        {
            "question": question,
            "model_name": model_name,
            "feature_list": ", ".join(feature_list),
            "dataset": dataset,
        }
    )
    raw = response.content.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


async def generate_insights(
    question: str,
    results_summary: str,
    dataset: str,
    model_meta: dict,
    llm,
) -> str:
    """Use LLM to produce a plain-English business narrative."""
    perf = model_meta["performance"]
    mtype = model_meta.get("model_type", "classification")
    if mtype == "classification":
        confidence_str = (
            f"{round(perf['accuracy'] * 100, 1)}% accuracy, {perf['roc_auc']} AUC"
        )
    else:
        confidence_str = f"R²={perf['r2']}, MAE=€{perf['mae']}"

    prompt = PromptTemplate(
        input_variables=[
            "question", "dataset", "results_summary", "model_accuracy"
        ],
        template=SIMULATION_INSIGHT_PROMPT,
    )
    chain = prompt | llm
    response = await chain.ainvoke(
        {
            "question": question,
            "dataset": dataset,
            "results_summary": results_summary,
            "model_accuracy": confidence_str,
        }
    )
    return response.content.strip()


# ══════════════════════════════════════════════════════════════════════════════
# VISUALIZATION BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def build_comparison_chart(
    comparison_df: pd.DataFrame,
    title: str = "Scenario Comparison",
    model_type: str = "classification",
) -> go.Figure:
    colors = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"]
    if model_type == "classification":
        y_vals = comparison_df["Attrition Rate (raw)"] * 100
        y_label = "Predicted Attrition Rate (%)"
        text_fmt = [f"{v:.1f}%" for v in y_vals]
        y_range = [0, max(y_vals) * 1.4]
    else:
        y_vals = comparison_df["Mean Revenue (€)"]
        y_label = "Mean Revenue per Transaction (€)"
        text_fmt = [f"€{v:,.2f}" for v in y_vals]
        y_range = [min(y_vals) * 0.9, max(y_vals) * 1.15]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=comparison_df["Scenario"],
            y=y_vals,
            text=text_fmt,
            textposition="outside",
            marker_color=[colors[i % len(colors)] for i in range(len(comparison_df))],
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="Scenario",
        yaxis_title=y_label,
        height=450,
        yaxis=dict(range=y_range),
    )
    return fig


def build_sensitivity_chart(
    search_curve: pd.DataFrame,
    parameter: str,
    target_metric: str,
) -> go.Figure:
    is_pct = target_metric == "attrition_rate"
    y_vals = search_curve[target_metric] * (100 if is_pct else 1)
    y_label = f"{target_metric} (%)" if is_pct else f"{target_metric} (€)"
    x_vals = (search_curve["multiplier"] - 1) * 100

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines+markers",
            line=dict(color="steelblue", width=2),
        )
    )
    fig.update_layout(
        title=f"Impact of {parameter} change on {target_metric}",
        xaxis_title=f"{parameter} change (%)",
        yaxis_title=y_label,
        height=400,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════

async def simulation_agent(
    question: str,
    llm,
    dataset: str = "hr_data",
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Simulation Agent — full what-if workflow orchestrator.

    Steps:
      1.  Detect model (keyword scan on question)
      2.  Parse question with LLM → structured JSON
      3.  Fetch baseline rows from PostgreSQL
      4.  Run baseline predictions
      5.  Apply scenario(s) and compare
      6.  Generate LLM insights
      7.  Return result dict (includes Plotly figure)

    Args:
        question:  Natural language simulation question
        llm:       AzureChatOpenAI instance (shared from main.py)
        dataset:   "hr_data" or "sales_data"
        verbose:   Print step-by-step progress

    Returns:
        dict with keys: success, question, simulation_type, model_name,
        model_type, baseline, delta/comparison_table/optimization/
        sensitivity_curve, visualization, insights, ...
    """
    sep = "=" * 65
    if verbose:
        print(f"\n{sep}\nSIMULATION AGENT\n{sep}")
        print(f"Question: {question}")

    reg = ModelRegistry()
    pred_svc = PredictionService(reg)

    # 1 ── Model detection ────────────────────────────────────────────────────
    model_name = reg.detect_model_for_question(question, dataset)
    model_meta = reg.get_model_metadata(model_name)
    feat_meta = reg.get_feature_metadata(model_name)
    features = feat_meta["all_features"]
    mtype = model_meta.get("model_type", "classification")
    if verbose:
        print(f"\n[1] Model: {model_name} (type={mtype})")

    # 2 ── Parse question ─────────────────────────────────────────────────────
    parsed = await parse_simulation_query(question, model_name, features, dataset, llm)
    sim_type = parsed.get("simulation_type", "whatif")
    if verbose:
        print(f"[2] Sim type: {sim_type}")

    # 3 ── Baseline data ───────────────────────────────────────────────────────
    scope_filter = parsed.get("scope_filter") or {}
    # Sanitize and normalize before use
    scope_filter = _sanitize_scope_filter(scope_filter, features) if scope_filter else {}
    scope_filter = _normalize_scope_values(scope_filter) if scope_filter else {}

    # Rescue numeric absolute-value entries the LLM wrongly placed in scope_filter
    # (e.g. shippingcost="=2" means "set shipping to €2", not "filter rows where cost=2")
    cat_features = feat_meta.get("cat_features", [])
    scope_filter, rescued_mods = _rescue_scope_filter(scope_filter, cat_features)
    if verbose and rescued_mods:
        print(f"[3] Rescued from scope_filter → modifications: {rescued_mods}")

    if verbose and scope_filter:
        print(f"[3] Scope filter: {scope_filter}")
    baseline_df = fetch_baseline_data(
        dataset=dataset,
        table=model_meta["table"],
        features=features,
        scope_filter=scope_filter or None,
    )

    # Fallback: if scope_filter produced 0 rows, retry without it
    if len(baseline_df) == 0 and scope_filter:
        if verbose:
            print(f"[3] WARNING: scope_filter returned 0 rows — retrying without filter")
        baseline_df = fetch_baseline_data(
            dataset=dataset,
            table=model_meta["table"],
            features=features,
            scope_filter=None,
        )
        # Apply the original scope conditions as in-memory pandas filter instead
        for col, val in scope_filter.items():
            val_str = str(val).strip()
            if col in baseline_df.columns:
                for op in ("!=", ">=", "<=", ">", "<", "="):
                    if val_str.startswith(op):
                        operand = val_str[len(op):].strip()
                        try:
                            num = float(operand)
                            ops_map = {">=": "__ge__", "<=": "__le__", ">": "__gt__",
                                       "<": "__lt__", "=": "__eq__", "!=": "__ne__"}
                            baseline_df = baseline_df[
                                getattr(baseline_df[col], ops_map[op])(num)
                            ]
                        except ValueError:
                            baseline_df = baseline_df[baseline_df[col] == operand]
                        break
                else:
                    baseline_df = baseline_df[baseline_df[col] == val_str]
        scope_filter = {}  # already applied in-memory
        if verbose:
            print(f"[3] After in-memory filter: {len(baseline_df)} rows")

    if verbose:
        print(f"[3] Baseline rows: {len(baseline_df)}")

    if len(baseline_df) == 0:
        raise ValueError(
            "No data matched the filter criteria. "
            "The scope filter produced 0 records — try broadening your question."
        )

    # 4 ── Baseline predictions ────────────────────────────────────────────────
    baseline_result = pred_svc.predict(model_name, baseline_df)
    if verbose:
        agg = baseline_result["aggregate"]
        if mtype == "classification":
            print(f"[4] Baseline: {agg['attrition_rate']*100:.1f}% attrition")
        else:
            print(f"[4] Baseline: €{agg['mean_revenue']:.2f} mean revenue")

    result: Dict[str, Any] = {
        "success": True,
        "question": question,
        "simulation_type": sim_type,
        "model_name": model_name,
        "model_type": mtype,
        "model_performance": model_meta["performance"],
        "scope": scope_filter,
        "n_records_analyzed": len(baseline_df),
        "baseline": baseline_result["aggregate"],
        "parsed_params": parsed,
    }

    # 5 ── Scenario engine ─────────────────────────────────────────────────────
    if sim_type == "whatif":
        modifications = parsed.get("modifications", {})
        # Merge any rescued mods (numeric absolute-value conditions the LLM
        # mistakenly placed in scope_filter) into the modifications dict.
        if rescued_mods:
            modifications = {**rescued_mods, **modifications}  # parsed wins on conflict
        whatif_df = ScenarioEngine.create_scenario(baseline_df, modifications)
        whatif_result = pred_svc.predict(model_name, whatif_df)
        comparison_df = pred_svc.compare_scenarios(
            model_name, [("Baseline", baseline_df), ("What-If", whatif_df)]
        )
        if mtype == "classification":
            delta = (
                whatif_result["aggregate"]["attrition_rate"]
                - baseline_result["aggregate"]["attrition_rate"]
            )
            saved = (
                baseline_result["aggregate"]["predicted_leavers"]
                - whatif_result["aggregate"]["predicted_leavers"]
            )
            result["whatif"] = whatif_result["aggregate"]
            result["delta"] = {
                "attrition_rate_change": round(delta, 4),
                "attrition_rate_change_pct": round(
                    delta / baseline_result["aggregate"]["attrition_rate"] * 100, 1
                ),
                "employees_saved": saved,
            }
            results_summary = (
                f"Baseline attrition: {baseline_result['aggregate']['attrition_rate']*100:.1f}%"
                f" ({baseline_result['aggregate']['predicted_leavers']} leavers).\n"
                f"What-If: {modifications}\n"
                f"New attrition: {whatif_result['aggregate']['attrition_rate']*100:.1f}%"
                f" ({whatif_result['aggregate']['predicted_leavers']} leavers).\n"
                f"Change: {delta*100:+.1f} pp, {saved:+d} employees saved."
            )
        else:
            rev_delta = (
                whatif_result["aggregate"]["mean_revenue"]
                - baseline_result["aggregate"]["mean_revenue"]
            )
            rev_delta_pct = rev_delta / baseline_result["aggregate"]["mean_revenue"] * 100
            total_delta = (
                whatif_result["aggregate"]["total_revenue"]
                - baseline_result["aggregate"]["total_revenue"]
            )
            result["whatif"] = whatif_result["aggregate"]
            result["delta"] = {
                "mean_revenue_change": round(rev_delta, 2),
                "mean_revenue_change_pct": round(rev_delta_pct, 2),
                "total_revenue_change": round(total_delta, 2),
            }
            results_summary = (
                f"Baseline: €{baseline_result['aggregate']['mean_revenue']:.2f} mean / "
                f"€{baseline_result['aggregate']['total_revenue']:,.2f} total.\n"
                f"What-If: {modifications}\n"
                f"New: €{whatif_result['aggregate']['mean_revenue']:.2f} mean / "
                f"€{whatif_result['aggregate']['total_revenue']:,.2f} total.\n"
                f"Change: {rev_delta_pct:+.1f}% mean, €{total_delta:+,.2f} total."
            )
        result["comparison_table"] = comparison_df
        result["visualization"] = build_comparison_chart(
            comparison_df,
            f'{"Attrition" if mtype=="classification" else "Revenue"}: Baseline vs What-If',
            model_type=mtype,
        )

    elif sim_type == "multi_scenario":
        scenarios_raw = parsed.get("scenarios", [])
        scenario_pairs = [("Baseline", baseline_df)]
        for s in scenarios_raw:
            df_s = ScenarioEngine.create_scenario(
                baseline_df, s.get("modifications", {})
            )
            scenario_pairs.append((s["name"], df_s))
        comparison_df = pred_svc.compare_scenarios(model_name, scenario_pairs)
        result["comparison_table"] = comparison_df
        result["visualization"] = build_comparison_chart(
            comparison_df, "Multi-Scenario Comparison", model_type=mtype
        )
        results_summary = (
            f"Multi-scenario ({len(scenarios_raw)} scenarios):\n"
            + comparison_df.to_string(index=False)
        )

    elif sim_type == "optimization":
        opt_target = parsed.get("optimization_target") or {}
        opt_parameter = parsed.get(
            "optimization_parameter",
            "monthlyincome" if mtype == "classification" else "discount",
        )
        target_metric = opt_target.get(
            "metric", "attrition_rate" if mtype == "classification" else "mean_revenue"
        )
        target_value = float(opt_target.get("target_value", 0.10))
        opt_result = optimize_parameter(
            pred_svc, model_name, baseline_df,
            opt_parameter, target_metric, target_value,
        )
        result["optimization"] = opt_result
        result["visualization"] = build_sensitivity_chart(
            opt_result["search_curve"], opt_parameter, target_metric
        )
        results_summary = (
            f"Optimization — target {target_metric}={target_value}:\n"
            f"  Parameter: {opt_parameter}\n"
            f"  Required change: {opt_result['percent_change_needed']:+.1f}%\n"
            f"  Achieved: {opt_result['achieved_value']}  |  Met: {opt_result['target_met']}"
        )

    elif sim_type == "sensitivity":
        modifications = parsed.get("modifications", {})
        parameter = (
            list(modifications.keys())[0]
            if modifications
            else ("monthlyincome" if mtype == "classification" else "discount")
        )
        mods_range = [f"*{m:.2f}" for m in np.arange(1.0, 1.31, 0.05)]
        scenario_dfs = ScenarioEngine.sensitivity_analysis(
            baseline_df, parameter, mods_range
        )
        sens_rows = []
        for df_s in scenario_dfs:
            mod = df_s["_modification"].iloc[0]
            df_clean = df_s.drop(columns=["_scenario_label", "_modification"])
            pred = pred_svc.predict(model_name, df_clean)
            row_key = "attrition_rate" if mtype == "classification" else "mean_revenue"
            sens_rows.append(
                {
                    "modification": mod,
                    "multiplier": float(mod[1:]),
                    row_key: pred["aggregate"][row_key],
                }
            )
        sens_df = pd.DataFrame(sens_rows)
        result["sensitivity_curve"] = sens_df
        target_col = "attrition_rate" if mtype == "classification" else "mean_revenue"
        result["visualization"] = build_sensitivity_chart(
            sens_df, parameter, target_col
        )
        results_summary = (
            f"Sensitivity for {parameter}:\n" + sens_df.to_string(index=False)
        )
    else:
        results_summary = (
            f"Sim type '{sim_type}' not implemented. "
            f"Baseline: {baseline_result['aggregate']}"
        )

    # 6 ── LLM insights ────────────────────────────────────────────────────────
    if verbose:
        print("[5] Generating LLM insights...")
    result["insights"] = await generate_insights(
        question, results_summary, dataset, model_meta, llm
    )

    if verbose:
        print(f"[6] Done!\n{sep}\n")

    return result
