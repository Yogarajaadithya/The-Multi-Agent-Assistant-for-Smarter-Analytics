"""
Statistical Testing Agent for Multi-Agent Analytics System
==============================================================
Executes statistical tests based on hypothesis specifications.

Author: Yogarajaadithya
Date: November 19, 2025
"""

import pandas as pd
from typing import Dict, Any

from app.utils.stats_utils import (
    load_hr_data,
    chi_square_test,
    t_test,
    anova_test,
    pearson_correlation,
    spearman_correlation
)


async def stats_agent(hypotheses_result: Dict[str, Any], df: pd.DataFrame = None) -> Dict[str, Any]:
    """
    Statistical Testing Agent - Executes statistical tests for hypotheses.
    
    Performs appropriate statistical tests based on variable types in each hypothesis
    and returns comprehensive test results with interpretations.
    
    Args:
        hypotheses_result (dict): Result from hypothesis_agent containing:
            - hypotheses: List of hypothesis objects
        df (pandas.DataFrame): Optional DataFrame to test on (loads from DB if None)
    
    Returns:
        dict: Statistical test results containing:
            - summary: Overview with total hypotheses and dataset info
            - hypothesis_results: List of test results for each hypothesis
            - error: Error message if testing failed
    
    Example:
        >>> hypotheses = await hypothesis_agent("Why do employees leave?", llm)
        >>> results = await stats_agent(hypotheses)
        >>> for r in results['hypothesis_results']:
        ...     print(r['statistical_results']['interpretation'])
    """
    try:
        # Load data if not provided
        if df is None:
            df = load_hr_data()
        
        # Normalize column names
        df.columns = df.columns.str.lower()
        
        # Check for errors in hypothesis generation
        if "error" in hypotheses_result:
            return {"error": hypotheses_result["error"]}
        
        hypotheses = hypotheses_result.get("hypotheses", [])
        
        if not hypotheses:
            return {"error": "No hypotheses to test"}
        
        # Initialize results
        all_results = {
            "summary": {
                "total_hypotheses": len(hypotheses),
                "dataset_shape": list(df.shape)
            },
            "hypothesis_results": []
        }
        
        # Execute test for each hypothesis
        for hypothesis in hypotheses:
            result = _execute_hypothesis_test(hypothesis, df)
            all_results["hypothesis_results"].append(result)
        
        return all_results
    
    except Exception as err:
        print(f"Error in stats_agent: {str(err)}")
        return {
            "error": f"Statistical testing failed: {str(err)}",
            "summary": {"total_hypotheses": 0, "dataset_shape": [0, 0]},
            "hypothesis_results": []
        }


def _execute_hypothesis_test(hypothesis: dict, df: pd.DataFrame) -> dict:
    """Execute the appropriate statistical test based on hypothesis variable types."""
    var1 = hypothesis.get('variable_1', '').lower()
    var2 = hypothesis.get('variable_2', '').lower()
    var1_type = hypothesis.get('variable_1_type', '')
    var2_type = hypothesis.get('variable_2_type', '')
    
    if var1 not in df.columns or var2 not in df.columns:
        return {
            "error": f"Variables not found in dataset. Available: {list(df.columns)}",
            "hypothesis_id": hypothesis.get('hypothesis_id'),
            "null_hypothesis": hypothesis.get('null_hypothesis'),
            "alternative_hypothesis": hypothesis.get('alternative_hypothesis')
        }
    
    results = {
        "hypothesis_id": hypothesis.get('hypothesis_id'),
        "null_hypothesis": hypothesis.get('null_hypothesis'),
        "alternative_hypothesis": hypothesis.get('alternative_hypothesis'),
        "variable_1": var1,
        "variable_2": var2,
        "variable_1_type": var1_type,
        "variable_2_type": var2_type,
        "recommended_test": hypothesis.get('recommended_test'),
        "statistical_results": {}
    }
    
    # Select and execute appropriate test
    if var1_type == "categorical" and var2_type == "categorical":
        results["statistical_results"] = chi_square_test(df, var1, var2)
    elif var1_type == "categorical" and var2_type == "numerical":
        num_groups = df[var1].nunique()
        results["statistical_results"] = t_test(df, var1, var2) if num_groups == 2 else anova_test(df, var1, var2)
    elif var1_type == "numerical" and var2_type == "categorical":
        num_groups = df[var2].nunique()
        results["statistical_results"] = t_test(df, var2, var1) if num_groups == 2 else anova_test(df, var2, var1)
    elif var1_type == "numerical" and var2_type == "numerical":
        results["statistical_results"] = {
            "pearson": pearson_correlation(df, var1, var2),
            "spearman": spearman_correlation(df, var1, var2)
        }
    
    return results
