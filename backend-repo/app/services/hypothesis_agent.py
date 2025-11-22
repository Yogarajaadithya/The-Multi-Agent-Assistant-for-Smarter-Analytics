"""
Hypothesis Generation Agent for Multi-Agent Analytics System
=============================================================
Generates testable bivariate hypotheses based on user questions.

Author: Yogarajaadithya
Date: November 19, 2025
"""

import os
import pandas as pd
from typing import Dict, Any
from langchain_core.prompts import PromptTemplate

from app.prompts.prompts import hypothesis_agent_prompt
from app.utils.hypothesis_utils import parse_json_response


def _load_dataset_context() -> str:
    """
    Load comprehensive dataset context from data dictionary and KPI documentation.
    
    Returns:
        str: Formatted context string with variable information and HR domain knowledge
    """
    try:
        # Get the project root directory (3 levels up from this file)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        data_folder = os.path.join(project_root, 'data')
        
        context_parts = []
        
        # Load HR Data Dictionary (CSV)
        data_dict_file = os.path.join(data_folder, 'HR_Data_Dictionary.csv')
        if os.path.exists(data_dict_file):
            try:
                df_dict = pd.read_csv(data_dict_file)
                
                context_parts.append("=" * 80)
                context_parts.append("AVAILABLE VARIABLES (Data Dictionary)")
                context_parts.append("=" * 80)
                context_parts.append("\nUse ONLY these exact column names (all lowercase):\n")
                
                # Format each variable with its key information
                for _, row in df_dict.iterrows():
                    col_name = str(row.get('Column Name', '')).strip().lower()
                    col_desc = str(row.get('Column Description', 'No description'))
                    col_type = str(row.get('Column Data Type', 'Unknown'))
                    is_cat = str(row.get('is_categorical', 'FALSE')).upper()
                    var_type = "CATEGORICAL" if is_cat == "TRUE" else "NUMERICAL"
                    
                    context_parts.append(f"• {col_name}")
                    context_parts.append(f"  Type: {var_type} ({col_type})")
                    context_parts.append(f"  Description: {col_desc}")
                    context_parts.append(f"  is_categorical: {is_cat}")
                    context_parts.append("")
                
                print(f"[INFO] Loaded {len(df_dict)} variables from data dictionary")
            except Exception as e:
                print(f"[WARNING] Could not load data dictionary: {e}")
        
        # Load HR KPI Documentation (TXT)
        kpi_doc_file = os.path.join(data_folder, 'hr_kpi_documentation.txt')
        if os.path.exists(kpi_doc_file):
            try:
                with open(kpi_doc_file, 'r', encoding='utf-8') as f:
                    kpi_content = f.read()
                
                context_parts.append("\n" + "=" * 80)
                context_parts.append("HR DOMAIN KNOWLEDGE (KPI Documentation)")
                context_parts.append("=" * 80)
                context_parts.append("\nUse this domain knowledge to inform your hypothesis generation:\n")
                context_parts.append(kpi_content)
                context_parts.append("")
                
                print(f"[INFO] Loaded HR KPI documentation")
            except Exception as e:
                print(f"[WARNING] Could not load KPI documentation: {e}")
        
        # If we have context, return it
        if context_parts:
            return "\n".join(context_parts)
        
        # Fallback: Try to generate from database schema
        print("[INFO] No data files found, generating context from database schema...")
        from app.utils.text_to_sql_utils import get_database_connection, get_structured_schema
        try:
            db = get_database_connection()
            schema_info = get_structured_schema(db)
            return f"DATASET SCHEMA:\n{schema_info}\n\nUse the columns defined above for generating hypotheses."
        except Exception as e:
            print(f"[WARNING] Could not generate context from schema: {e}")
            return "DATASET: HR Employee Attrition dataset. Analyze relationships between variables based on the user's question."
    
    except Exception as e:
        print(f"[ERROR] Failed to load dataset context: {e}")
        return "DATASET: HR Employee Attrition dataset. Analyze relationships between variables based on the user's question."


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
        # Load comprehensive context from data dictionary and KPI documentation
        if context is None:
            context = _load_dataset_context()
        
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
