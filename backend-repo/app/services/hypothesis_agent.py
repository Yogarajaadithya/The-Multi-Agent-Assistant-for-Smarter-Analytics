"""
Hypothesis Generation Agent for Multi-Agent Analytics System
=============================================================
Generates testable bivariate hypotheses based on user questions.

Author: Yogarajaadithya
Date: November 19, 2025
"""

import os
from typing import Dict, Any
from langchain_core.prompts import PromptTemplate

from app.prompts.prompts import hypothesis_agent_prompt
from app.utils.hypothesis_utils import parse_json_response


async def hypothesis_agent(
    user_query: str,
    llm,
    num_hypotheses: int = 3,
    context: str = None
) -> Dict[str, Any]:
    """
    Hypothesis Agent - Generates testable bivariate hypotheses.
    
    Generates testable hypotheses involving two variables based on the user's
    research question about data analytics.
    
    Args:
        user_query (str): The user's research question
        llm: The language model instance (from llm.py)
        num_hypotheses (int): Number of hypotheses to generate (default: 3)
        context (str): Optional dataset context (auto-loads from documentation file if None)
    
    Returns:
        dict: The generated hypotheses containing:
            - hypotheses: List of hypothesis objects with:
                - hypothesis_id: Unique identifier
                - null_hypothesis: H0 statement
                - alternative_hypothesis: H1 statement
                - variable_1: First variable name
                - variable_2: Second variable name
                - variable_1_type: "categorical" or "numerical"
                - variable_2_type: "categorical" or "numerical"
                - recommended_test: Statistical test name
                - rationale: Explanation
            - error: Error message if generation failed
    
    Example:
        >>> from langchain_openai import ChatOpenAI
        >>> 
        >>> llm = ChatOpenAI(api_key="...", base_url="...")
        >>> result = await hypothesis_agent(
        ...     "Why do employees leave the company?",
        ...     llm,
        ...     num_hypotheses=3
        ... )
        >>> for h in result['hypotheses']:
        ...     print(h['alternative_hypothesis'])
    """
    try:
        # Load context from documentation file if not provided
        if context is None:
            # Get the project root directory (3 levels up from this file)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            data_folder = os.path.join(project_root, 'data')
            
            # Try to find any documentation file in the data folder
            context_file = None
            if os.path.exists(data_folder):
                for filename in os.listdir(data_folder):
                    if 'documentation' in filename.lower() and filename.endswith('.txt'):
                        context_file = os.path.join(data_folder, filename)
                        break
                    elif 'kpi' in filename.lower() and filename.endswith('.txt'):
                        context_file = os.path.join(data_folder, filename)
                        break
                    elif 'data_dictionary' in filename.lower() and filename.endswith('.csv'):
                        context_file = os.path.join(data_folder, filename)
                        break
            
            # Load context from file if found
            if context_file and os.path.exists(context_file):
                try:
                    with open(context_file, 'r', encoding='utf-8') as f:
                        context = f.read()
                except Exception as e:
                    print(f"Warning: Could not read context file: {e}")
                    context = None
            
            # Fallback: Generate context from database schema
            if context is None:
                from app.utils.text_to_sql_utils import get_database_connection, get_structured_schema
                try:
                    db = get_database_connection()
                    schema_info = get_structured_schema(db)
                    context = f"DATASET SCHEMA:\\n{schema_info}\\n\\nUse the columns defined above for generating hypotheses."
                except Exception as e:
                    print(f"Warning: Could not generate context from schema: {e}")
                    context = "DATASET: Analyze relationships between variables in the dataset based on the user's question."
        
        # Create prompt from template
        hyp_prompt = PromptTemplate.from_template(hypothesis_agent_prompt)
        
        # Create chain using pipe operator
        chain = hyp_prompt | llm
        
        # Generate hypotheses
        response = await chain.ainvoke({
            "user_query": user_query,
            "num_hypotheses": num_hypotheses,
            "context": context
        })
        generated_hypotheses = response.content if hasattr(response, 'content') else str(response)
        
        # Clean and parse response
        hypotheses_data = parse_json_response(generated_hypotheses)
        
        return hypotheses_data
    
    except TimeoutError as err:
        error_msg = f"LLM request timed out: {str(err)}"
        print(f"[ERROR] TIMEOUT ERROR: {error_msg}")
        return {
            "error": error_msg,
            "hypotheses": []
        }
    
    except ConnectionError as err:
        error_msg = f"Failed to connect to LLM server: {str(err)}"
        print(f"[ERROR] CONNECTION ERROR: {error_msg}")
        return {
            "error": error_msg,
            "hypotheses": []
        }
    
    except Exception as err:
        error_msg = f"Hypothesis generation failed: {str(err)}"
        print(f"[ERROR] in hypothesis_agent: {error_msg}")
        return {
            "error": error_msg,
            "hypotheses": []
        }
