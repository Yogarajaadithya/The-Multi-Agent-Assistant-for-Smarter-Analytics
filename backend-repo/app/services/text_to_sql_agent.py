"""
Text-to-SQL Agent for Multi-Agent Analytics System
===================================================
Converts natural language questions to PostgreSQL queries and executes them.

Author: Yogarajaadithya
Date: November 19, 2025
"""

import json
import re
import pandas as pd
from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_community.utilities import SQLDatabase

from app.prompts.prompts import text_to_sql_agent_prompt
from app.utils.text_to_sql_utils import (
    get_database_connection,
    get_structured_schema,
    extract_sql,
    validate_sql
)


async def text_to_sql_agent(user_query: str, llm, db: SQLDatabase = None, context: str = None) -> Dict[str, Any]:
    """
    Text-to-SQL Agent - Converts natural language to SQL and executes query.
    
    Generates PostgreSQL queries from natural language questions and returns
    the query results as a pandas DataFrame.
    
    Args:
        user_query (str): The user's natural language question
        llm: The language model instance (from llm.py)
        db: SQLDatabase connection (creates new if None)
        context (str): Optional context about the data domain
    
    Returns:
        dict: The query results containing:
            - success: Boolean indicating if query succeeded
            - sql: Generated SQL query string
            - data: pandas DataFrame with results
            - rows: Number of rows returned
            - columns: List of column names
            - error: Error message if any
    
    Example:
        >>> from app.services.llm import get_lm_client
        >>> from langchain_openai import ChatOpenAI
        >>> 
        >>> llm = ChatOpenAI(api_key="...", base_url="...")
        >>> result = await text_to_sql_agent(
        ...     "What is the distribution by department?",
        ...     llm
        ... )
        >>> print(result['data'])
    """
    try:
        # Get database connection if not provided
        if db is None:
            db = get_database_connection()
        
        # Get schema dynamically
        schema = get_structured_schema(db)
        
        # Get schema and table name for the prompt
        import os
        schema_name = os.getenv('DB_SCHEMA', 'public')
        table_name = os.getenv('DB_TABLE', 'wa_fn_usec')
        schema_table = f"{schema_name}.{table_name}"
        
        # Default context if not provided
        if context is None:
            context = f"This is a {table_name} table in the {schema_name} schema. Use the columns defined in the schema above."
        
        # Create prompt from template
        sql_prompt = PromptTemplate.from_template(text_to_sql_agent_prompt)
        
        # Create chain using pipe operator
        chain = sql_prompt | llm
        
        # Generate SQL query
        response = await chain.ainvoke({
            "schema": schema,
            "schema_table": schema_table,
            "context": context,
            "user_query": user_query
        })
        generated_sql = response.content if hasattr(response, 'content') else str(response)
        
        # Parse JSON response to extract SQL and thinking
        thinking = None
        try:
            # Try to parse as JSON
            json_match = re.search(r'\{.*\}', generated_sql, re.DOTALL)
            if json_match:
                json_response = json.loads(json_match.group())
                sql_query = json_response.get('sql_query', '')
                thinking = json_response.get('thinking_out_loud', '')
            else:
                # Fallback to old extraction method
                sql_query = extract_sql(generated_sql)
        except (json.JSONDecodeError, KeyError):
            # Fallback to old extraction method if JSON parsing fails
            sql_query = extract_sql(generated_sql)
        
        # Validate SQL
        validate_sql(sql_query)
        
        # Execute SQL query
        with db._engine.connect() as conn:
            df = pd.read_sql(sql_query, conn)
        
        result = {
            "success": True,
            "sql": sql_query,
            "data": df,
            "rows": len(df),
            "columns": list(df.columns),
            "error": None
        }
        
        # Add thinking if available
        if thinking:
            result["thinking"] = thinking
        
        return result
    
    except Exception as err:
        error_message = str(err)
        
        # Check if it's an undefined column error (retry once with feedback)
        undefined_column = (
            "UndefinedColumn" in error_message
            or ("column" in error_message.lower() and "does not exist" in error_message.lower())
        )
        
        if undefined_column:
            try:
                # Retry with explicit guidance
                feedback_query = (
                    f"{user_query}\n\n"
                    "The previous SQL failed because it referenced a column that was not available. "
                    "Generate a corrected PostgreSQL SELECT that keeps all referenced columns in scope, "
                    "computing derived buckets inline in the main query instead of subqueries."
                )
                
                response_retry = await chain.ainvoke({
                    "schema": schema,
                    "schema_table": schema_table,
                    "context": context,
                    "user_query": feedback_query
                })
                generated_sql_retry = response_retry.content if hasattr(response_retry, 'content') else str(response_retry)
                
                # Parse JSON response for retry
                thinking_retry = None
                try:
                    json_match = re.search(r'\{.*\}', generated_sql_retry, re.DOTALL)
                    if json_match:
                        json_response = json.loads(json_match.group())
                        sql_query_retry = json_response.get('sql_query', '')
                        thinking_retry = json_response.get('thinking_out_loud', '')
                    else:
                        sql_query_retry = extract_sql(generated_sql_retry)
                except (json.JSONDecodeError, KeyError):
                    sql_query_retry = extract_sql(generated_sql_retry)
                
                validate_sql(sql_query_retry)
                
                with db._engine.connect() as conn:
                    df = pd.read_sql(sql_query_retry, conn)
                
                result_retry = {
                    "success": True,
                    "sql": sql_query_retry,
                    "data": df,
                    "rows": len(df),
                    "columns": list(df.columns),
                    "error": None
                }
                
                if thinking_retry:
                    result_retry["thinking"] = thinking_retry
                
                return result_retry
            except Exception as retry_err:
                error_message = f"Retry also failed: {str(retry_err)}"
        
        print(f"Error in text_to_sql_agent: {error_message}")
        return {
            "success": False,
            "sql": None,
            "data": None,
            "rows": 0,
            "columns": [],
            "error": error_message
        }
