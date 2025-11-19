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
            
            # Generate visualization code
            response = await chain.ainvoke({
                "data_summary": data_summary,
                "original_question": original_question or "Visualize this data"
            })
            generated_code = response.content if hasattr(response, 'content') else str(response)
            
            code = extract_code(generated_code)
        
        # Remove fig.show() if present
        code = code.replace('fig.show()', '').strip()
        
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
        print(f"[ERROR] Visualization generation failed: {str(err)}")
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
            "error": f"Visualization generation failed: {str(err)}"
        }
