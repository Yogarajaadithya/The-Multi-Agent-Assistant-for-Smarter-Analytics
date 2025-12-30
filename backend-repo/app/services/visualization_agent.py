"""
Visualization Agent for Multi-Agent Analytics System
========================================================
Generates Plotly visualizations from pandas DataFrames using LLM.

Author: Yogarajaadithya
Date: November 19, 2025
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any
from langchain_core.prompts import PromptTemplate

from app.prompts.prompts import visualization_agent_prompt
from app.utils.visualization_utils import (
    get_data_summary,
    extract_code,
    detect_single_value_df,
    generate_indicator_code
)


async def visualization_agent(df: pd.DataFrame, llm, original_question: str = "") -> Dict[str, Any]:
    """
    Visualization Agent - Generates Plotly visualizations from DataFrames.
    
    Creates appropriate visualizations using LLM to generate executable Plotly code
    based on the DataFrame structure and content.
    
    Args:
        df (pandas.DataFrame): The data to visualize
        llm: The language model instance (from llm.py)
        original_question (str): Optional original user question for context
    
    Returns:
        dict: The visualization results containing:
            - success: Boolean indicating if visualization succeeded
            - code: Generated Python code string
            - figure: Plotly figure object
            - error: Error message if any
    
    Example:
        >>> import pandas as pd
        >>> from langchain_openai import ChatOpenAI
        >>> 
        >>> df = pd.DataFrame({'dept': ['Sales', 'IT'], 'count': [10, 15]})
        >>> llm = ChatOpenAI(api_key="...", base_url="...")
        >>> result = await visualization_agent(
        ...     df,
        ...     llm,
        ...     "Show employee count by department"
        ... )
        >>> result['figure'].show()
    """
    max_retries = 2
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Special handling for single-value DataFrames
            if detect_single_value_df(df):
                code = generate_indicator_code(df)
            else:
                # Generate code using LLM
                data_summary = get_data_summary(df)
                
                # Create prompt from template
                viz_prompt = PromptTemplate.from_template(visualization_agent_prompt)
                
                # Create chain using pipe operator
                chain = viz_prompt | llm
                
                # Add error context for retry attempts
                error_hint = ""
                if attempt > 0 and last_error:
                    error_hint = f"\n\nPREVIOUS ATTEMPT FAILED with error: {last_error}\nDO NOT repeat the same mistake. Use only valid Plotly properties."
                
                # Generate visualization code
                response = await chain.ainvoke({
                    "data_summary": data_summary + error_hint,
                    "original_question": original_question or "Visualize this data"
                })
                generated_code = response.content if hasattr(response, 'content') else str(response)
                
                code = extract_code(generated_code)
            
            # Remove fig.show() if present
            code = code.replace('fig.show()', '').strip()
            
            # Validate for common errors before execution
            if 'subtitle=' in code and 'go.Indicator' in code:
                # Fix common mistake: replace subtitle with title annotation
                print("[WARNING] Detected invalid 'subtitle' property in Indicator. Attempting to fix...")
                code = code.replace('subtitle=', '# subtitle=  # Invalid property - ')
            
            # Execute code
            namespace = {
                'df': df,
                'px': px,
                'go': go,
                'pd': pd
            }
            
            exec(code, namespace)
            
            # Retrieve figure
            if 'fig' not in namespace:
                raise ValueError("Generated code did not create a 'fig' variable")
            
            fig = namespace['fig']
            
            return {
                "success": True,
                "code": code,
                "figure": fig,
                "error": None
            }
        
        except Exception as err:
            last_error = str(err)
            print(f"[ERROR] Visualization attempt {attempt + 1}/{max_retries} failed: {last_error}")
            
            if attempt < max_retries - 1:
                print(f"[INFO] Retrying visualization generation...")
                continue
            
            # Final attempt failed
            print("[ERROR] Visualization generation failed after all retries")
            print("[ERROR] Generated code that caused the error:")
            print(f"{'='*70}")
            print(code if 'code' in locals() else 'No code generated')
            print(f"{'='*70}")
            print(f"[ERROR] Available DataFrame columns: {df.columns.tolist()}")
            print(f"[ERROR] DataFrame shape: {df.shape}")
            
            return {
                "success": False,
                "code": code if 'code' in locals() else None,
                "figure": None,
                "error": f"Visualization generation failed: {last_error}"
            }
    
    # Should never reach here, but just in case
    return {
        "success": False,
        "code": None,
        "figure": None,
        "error": "Visualization generation failed: Maximum retries exceeded"
    }

