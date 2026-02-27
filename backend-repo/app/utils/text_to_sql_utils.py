"""
Utility functions for Text-to-SQL Agent
========================================
Database connection and SQL processing utilities.

Author: Yogarajaadithya
Date: November 19, 2025
"""

import os
import re
from dotenv import load_dotenv
from urllib.parse import quote_plus
from langchain_community.utilities import SQLDatabase

load_dotenv(override=True)


def get_database_connection(schema_name: str = None):
    """
    Create and return a database connection.
    
    Args:
        schema_name: Optional schema name to set as search_path
        
    Returns:
        SQLDatabase instance connected to PostgreSQL
    """
    if schema_name is None:
        schema_name = os.getenv("DEFAULT_DATASET", "hr_data")
    
    encoded_pw = quote_plus(os.getenv("DB_PASSWORD"))
    postgres_url = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{encoded_pw}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    
    db = SQLDatabase.from_uri(
        postgres_url,
        engine_args={"connect_args": {"options": f"-csearch_path={schema_name}"}}
    )
    
    return db


def get_structured_schema(db: SQLDatabase = None, schema_name: str = None, table_name: str = None) -> str:
    """
    Generate CREATE TABLE style schema representation dynamically from database.
    Includes sample values for categorical (TEXT) columns to help LLM generate accurate filters.
    
    Args:
        db: SQLDatabase connection (creates new if None)
        schema_name: Schema name (uses DEFAULT_DATASET if None)
        table_name: Table name (uses dataset's main table if None)
    
    Returns:
        str: CREATE TABLE statement with columns and categorical values
    """
    if db is None:
        db = get_database_connection(schema_name)
    
    if schema_name is None:
        schema_name = os.getenv('DEFAULT_DATASET', 'hr_data')
    
    if table_name is None:
        # Get table name from dataset manager
        from app.services.dataset_manager import get_dataset_manager
        dataset_manager = get_dataset_manager()
        table_name = dataset_manager.get_table_name()
    
    full_table_name = f"{schema_name}.{table_name}"
    
    try:
        # Query information_schema directly for the specific table
        query = f"""
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = '{schema_name}'
        AND table_name = '{table_name}'
        ORDER BY ordinal_position;
        """
        
        with db._engine.connect() as conn:
            import pandas as pd
            columns_df = pd.read_sql(query, conn)
        
        if columns_df.empty:
            raise ValueError(f"Table {full_table_name} not found or has no columns")
        
        # Get distinct values for TEXT/categorical columns (limit to reasonable number)
        categorical_values = {}
        for _, row in columns_df.iterrows():
            col_name = row['column_name']
            data_type = row['data_type'].lower()
            
            # Only get distinct values for TEXT-like columns
            if 'char' in data_type or 'text' in data_type:
                try:
                    distinct_query = f"""
                    SELECT DISTINCT {col_name} 
                    FROM {full_table_name} 
                    WHERE {col_name} IS NOT NULL 
                    ORDER BY {col_name} 
                    LIMIT 15
                    """
                    distinct_df = pd.read_sql(distinct_query, conn)
                    if not distinct_df.empty and len(distinct_df) <= 15:
                        values = distinct_df[col_name].tolist()
                        categorical_values[col_name] = values
                except Exception:
                    pass  # Skip if we can't get distinct values
        
        # Build CREATE TABLE statement with categorical values
        schema_lines = [f"CREATE TABLE {full_table_name} ("]
        
        for _, row in columns_df.iterrows():
            col_name = row['column_name']
            data_type = row['data_type'].upper()
            
            # Map PostgreSQL types to simpler names
            if 'char' in data_type.lower() or 'text' in data_type.lower():
                data_type = 'TEXT'
            elif 'int' in data_type.lower():
                data_type = 'INTEGER'
            elif 'numeric' in data_type.lower() or 'decimal' in data_type.lower():
                data_type = 'NUMERIC'
            elif 'float' in data_type.lower() or 'double' in data_type.lower():
                data_type = 'FLOAT'
            elif 'bool' in data_type.lower():
                data_type = 'BOOLEAN'
            elif 'date' in data_type.lower():
                data_type = 'DATE'
            elif 'time' in data_type.lower():
                data_type = 'TIMESTAMP'
            
            # Add categorical values as comment if available
            if col_name in categorical_values:
                values_str = ", ".join([f"'{v}'" for v in categorical_values[col_name]])
                schema_lines.append(f"    {col_name} {data_type},  -- Possible values: [{values_str}]")
            else:
                schema_lines.append(f"    {col_name} {data_type},")
        
        # Remove trailing comma and close
        schema_lines[-1] = schema_lines[-1].rstrip(',')
        if schema_lines[-1].endswith(']'):
            # Has a comment, just close the parenthesis
            schema_lines.append(");")
        else:
            schema_lines.append(");")
        
        return "\n".join(schema_lines)
        
    except Exception as e:
        print(f"Warning: Could not generate schema dynamically: {e}")
        # Return minimal schema info
        return f"""CREATE TABLE {full_table_name} (
    -- Schema information unavailable
    -- Please ensure the table exists and you have proper permissions
);"""


def extract_sql(text: str) -> str:
    """Extract SQL from LLM response."""
    # Remove thinking tags
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Try extracting from code blocks
    sql_block = re.search(r"```sql\s*(.*?)```", text, re.IGNORECASE | re.DOTALL)
    if sql_block:
        sql = sql_block.group(1)
    else:
        code_block = re.search(r"```\s*(.*?)```", text, re.DOTALL)
        sql = code_block.group(1) if code_block else text
    
    # Clean up
    sql = sql.strip().strip(';')
    
    # Fallback: extract SELECT statement
    if not sql.strip().upper().startswith("SELECT"):
        select_match = re.search(r'(SELECT\s+.*?)(?:;|$)', sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            sql = select_match.group(1).strip()
    
    return sql.strip()


def validate_sql(sql: str) -> bool:
    """Basic SQL validation."""
    sql_lower = sql.lower().strip()
    
    # Must be a SELECT query
    if not sql_lower.startswith('select'):
        raise ValueError("Only SELECT queries are allowed")
    
    # Get expected table name from dataset manager
    from app.services.dataset_manager import get_dataset_manager
    dataset_manager = get_dataset_manager()
    current_dataset = dataset_manager.get_current_dataset()
    schema_name = current_dataset.schema_name
    table_name = current_dataset.main_table
    full_table_name = f"{schema_name}.{table_name}"
    
    # Must reference the correct table with schema
    if full_table_name.lower() not in sql_lower:
        raise ValueError(f"Query must reference '{full_table_name}' table with schema prefix")
    
    return True
