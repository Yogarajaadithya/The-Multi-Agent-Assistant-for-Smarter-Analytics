"""
Statistical Testing Agent for Multi-Agent Analytics System
==============================================================
Executes statistical tests based on hypothesis specifications.

Author: Yogarajaadithya
Date: November 19, 2025
"""

import json
import pandas as pd
import logging
from typing import Dict, Any
from langchain_core.prompts import PromptTemplate

logger = logging.getLogger(__name__)

from app.utils.stats_utils import (
    load_dataset_data,
    chi_square_test,
    t_test,
    anova_test,
    pearson_correlation,
    spearman_correlation
)
from app.services.dataset_manager import get_dataset_manager
from app.prompts.prompts import stats_agent_prompt


async def stats_agent(
    hypotheses_result: Dict[str, Any],
    df: pd.DataFrame = None,
    llm = None,
    original_question: str = ""
) -> Dict[str, Any]:
    """
    Statistical Testing Agent - Executes statistical tests for hypotheses.
    
    Performs appropriate statistical tests based on variable types in each hypothesis
    and returns comprehensive test results with LLM-generated interpretations.
    
    Args:
        hypotheses_result (dict): Result from hypothesis_agent containing:
            - hypotheses: List of hypothesis objects
        df (pandas.DataFrame): Optional DataFrame to test on (loads from DB if None)
        llm: Optional language model for generating user-friendly interpretations
        original_question (str): Original user question for context in interpretation
    
    Returns:
        dict: Statistical test results containing:
            - summary: Overview with total hypotheses and dataset info
            - hypothesis_results: List of test results for each hypothesis
            - llm_interpretation: User-friendly interpretation (if LLM provided)
            - error: Error message if testing failed
    
    Example:
        >>> hypotheses = await hypothesis_agent("Why do employees leave?", llm)
        >>> results = await stats_agent(hypotheses, llm=llm, original_question="Why do employees leave?")
        >>> print(results['llm_interpretation']['overall_summary'])
    """
    try:
        # Load data if not provided
        if df is None:
            dataset_manager = get_dataset_manager()
            df = load_dataset_data(dataset_manager)
        
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
        
        # Generate LLM interpretation if LLM is provided
        if llm is not None:
            try:
                interpretation = await _generate_llm_interpretation(
                    all_results, 
                    llm, 
                    original_question
                )
                all_results["llm_interpretation"] = interpretation
            except Exception as interp_err:
                logger.warning(f"LLM interpretation failed: {str(interp_err)}")
                all_results["llm_interpretation"] = {
                    "error": f"Interpretation generation failed: {str(interp_err)}"
                }
        
        return all_results
    
    except Exception as err:
        error_msg = f"Statistical testing failed: {str(err)}"
        logger.error(f"Error in stats_agent: {str(err)}", exc_info=True)
        return {
            "error": error_msg,
            "summary": {"total_hypotheses": 0, "dataset_shape": [0, 0]},
            "hypothesis_results": []
        }


async def _generate_llm_interpretation(
    stats_results: Dict[str, Any],
    llm,
    original_question: str
) -> Dict[str, Any]:
    """
    Generate user-friendly interpretation of statistical results using LLM.
    
    Args:
        stats_results: Raw statistical test results
        llm: Language model instance
        original_question: Original user question for context
    
    Returns:
        dict: LLM-generated interpretation with insights and recommendations
    """
    # Format stats results for the prompt
    formatted_results = json.dumps(stats_results, indent=2, default=str)
    
    # Create prompt from template
    interpretation_prompt = PromptTemplate.from_template(stats_agent_prompt)
    
    # Create chain
    chain = interpretation_prompt | llm
    
    # Generate interpretation
    response = await chain.ainvoke({
        "original_question": original_question or "Analyze the factors affecting the outcome",
        "stats_results": formatted_results
    })
    
    # Extract response content
    response_text = response.content if hasattr(response, 'content') else str(response)
    
    # Parse JSON from response
    try:
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            interpretation = json.loads(json_match.group())
            return interpretation
        else:
            # Return as plain text if JSON parsing fails
            return {
                "overall_summary": response_text,
                "hypothesis_interpretations": [],
                "key_takeaways": [],
                "limitations": "Could not parse structured response"
            }
    except json.JSONDecodeError:
        return {
            "overall_summary": response_text,
            "hypothesis_interpretations": [],
            "key_takeaways": [],
            "limitations": "Could not parse structured response"
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
