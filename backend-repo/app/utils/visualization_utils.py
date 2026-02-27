"""
Utility functions for Visualization Agent
==========================================
Plotly code generation and DataFrame processing utilities.

Author: Yogarajaadithya
Date: November 19, 2025
"""

import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def get_data_summary(df: pd.DataFrame) -> str:
    """Generate a summary of the DataFrame for the LLM."""
    # Get column names and types explicitly
    column_list = "\n".join([f"  - {col} ({df[col].dtype})" for col in df.columns])
    
    summary = f"""
DATAFRAME SHAPE: {df.shape[0]} rows × {df.shape[1]} columns

AVAILABLE COLUMNS (USE THESE EXACT NAMES):
{column_list}

SAMPLE DATA (First {min(5, len(df))} rows):
{df.head().to_string()}

STATISTICS FOR NUMERICAL COLUMNS:
{df.describe().to_string() if not df.select_dtypes(include=['number']).empty else 'No numerical columns'}
"""
    return summary


def extract_code(text: str) -> str:
    """Extract Python code from LLM response."""
    # Remove thinking tags
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Extract from code blocks
    python_block = re.search(r"```python\s*(.*?)```", text, re.IGNORECASE | re.DOTALL)
    if python_block:
        code = python_block.group(1).strip()
    else:
        code_block = re.search(r"```\s*(.*?)```", text, re.DOTALL)
        code = code_block.group(1).strip() if code_block else text.strip()
    
    return code.strip()


def detect_single_value_df(df: pd.DataFrame) -> bool:
    """Check if DataFrame is single-value (1 row, 1 column)."""
    return df.shape[0] == 1 and df.shape[1] == 1


def detect_value_type(column_name: str) -> str:
    """
    Detect the semantic type of a value based on column name patterns.
    Returns: 'percentage', 'count', 'average', 'currency', or 'number'
    """
    col_lower = column_name.lower()
    
    # Check for percentage/rate patterns
    if any(pattern in col_lower for pattern in ['_percent', '_rate', 'rate_', 'percent', 'percentage']):
        return 'percentage'
    
    # Check for count patterns
    if any(pattern in col_lower for pattern in ['_count', 'count_', 'total_', 'num_', 'number_', 'how_many']):
        return 'count'
    
    # Check for average patterns
    if any(pattern in col_lower for pattern in ['avg_', 'average_', 'mean_', '_avg', '_average', '_mean']):
        return 'average'
    
    # Check for currency patterns
    if any(pattern in col_lower for pattern in ['_income', '_salary', '_revenue', '_price', '_amount', '_cost', 'income', 'salary', 'revenue']):
        return 'currency'
    
    # Default to number
    return 'number'


def generate_indicator_code(df: pd.DataFrame) -> str:
    """
    Generate code for single-value result as an Indicator (number card).
    Automatically detects format based on column name patterns.
    """
    value = float(df.iloc[0, 0])
    column_name = df.columns[0]
    title = column_name.replace('_', ' ').title()
    value_type = detect_value_type(column_name)
    
    # Determine formatting based on value type
    if value_type == 'percentage':
        number_format = "'.2f'"
        suffix = "'%'"
        color = "'#6366F1'"  # Purple for percentages
    elif value_type == 'count':
        number_format = "',.0f'"
        suffix = "''"
        color = "'#10B981'"  # Green for counts
    elif value_type == 'average':
        number_format = "',.2f'"
        suffix = "''"
        color = "'#F59E0B'"  # Amber for averages
    elif value_type == 'currency':
        number_format = "'$,.2f'"
        suffix = "''"
        color = "'#10B981'"  # Green for currency
    else:
        number_format = "',.2f'"
        suffix = "''"
        color = "'#6366F1'"  # Default purple
    
    return f"""import plotly.graph_objects as go

value = {value}
title_text = "{title}"

fig = go.Figure(go.Indicator(
    mode='number',
    value=value,
    title={{'text': title_text, 'font': {{'size': 20, 'color': '#374151'}}}},
    number={{
        'font': {{'size': 56, 'color': {color}}},
        'valueformat': {number_format},
        'suffix': {suffix}
    }}
))

fig.update_layout(
    height=250,
    template='plotly_white',
    margin=dict(l=20, r=20, t=60, b=20),
    paper_bgcolor='white'
)
"""


def create_fallback_visualization(df: pd.DataFrame, question: str = "") -> go.Figure:
    """Create a simple fallback visualization."""
    # Determine best fallback chart type
    if df.shape[1] == 1:
        # Single column - use bar chart
        fig = px.bar(
            df,
            y=df.columns[0],
            title=f"Distribution: {df.columns[0].replace('_', ' ').title()}",
            template='plotly_white'
        )
    elif df.shape[1] == 2:
        # Two columns - try bar chart with x and y
        fig = px.bar(
            df,
            x=df.columns[0],
            y=df.columns[1],
            title=question or "Data Visualization",
            template='plotly_white'
        )
    else:
        # Multiple columns - use the first two for visualization
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_cols) >= 2:
            fig = px.scatter(
                df,
                x=numeric_cols[0],
                y=numeric_cols[1],
                title=question or "Data Visualization",
                template='plotly_white'
            )
        else:
            fig = px.bar(
                df,
                x=df.columns[0],
                y=df.columns[1] if len(df.columns) > 1 else df.columns[0],
                title=question or "Data Visualization",
                template='plotly_white'
            )
    
    fig.update_layout(height=500)
    return fig
