"""
Text-to-SQL and Visualization Agent
====================================
Combined agent for converting natural language to SQL queries and generating visualizations.
Configured for Local LLM (LM Studio) and ready for FastAPI integration.

Author: Yogarajaadithya
Date: October 29, 2025
"""

import os
import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, Optional, Tuple
from io import StringIO
from dotenv import load_dotenv
from urllib.parse import quote_plus

from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# ═══════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════

# Load environment variables
load_dotenv(override=True)

# HR Data Dictionary Context
DATA_DICTIONARY = """
TABLE: employee_attrition
Description: HR analytics data collection for employee attrition

COLUMNS:
- age (int): Employee's age in years
- attrition (text): Whether employee left the company (Yes/No) - CATEGORICAL
- businesstravel (text): Frequency of business travel - CATEGORICAL
  VALUES: 'Travel_Rarely', 'Travel_Frequently', 'Non-Travel'
- dailyrate (int): Daily salary rate
- department (text): Employee's department - CATEGORICAL
- distancefromhome (int): Distance from home to workplace in miles
- education (int): Education level 1-5 - CATEGORICAL
- educationfield (text): Field of study - CATEGORICAL
- employeenumber (int): Unique employee identifier
- environmentsatisfaction (int): Work environment satisfaction 1-4 - CATEGORICAL
- gender (text): Male/Female - CATEGORICAL
  VALUES: 'Male', 'Female'
- hourlyrate (int): Hourly wage rate
- jobinvolvement (int): Job involvement level 1-4 - CATEGORICAL
- joblevel (int): Position level 1-5 - CATEGORICAL
- jobrole (text): Specific job title - CATEGORICAL
- jobsatisfaction (int): Job satisfaction level 1-4 - CATEGORICAL
- maritalstatus (text): Single/Married/Divorced - CATEGORICAL
- monthlyincome (int): Monthly salary
- monthlyrate (int): Monthly billing rate
- numcompaniesworked (int): Number of previous employers
- overtime (text): Works overtime Yes/No - CATEGORICAL
- percentsalaryhike (int): Percentage salary increase
- performancerating (int): Performance rating 1-4 - CATEGORICAL
- relationshipsatisfaction (int): Workplace relationship satisfaction 1-4 - CATEGORICAL
- stockoptionlevel (int): Stock option level 0-3 - CATEGORICAL
- totalworkingyears (int): Total years of work experience
- trainingtimeslastyear (int): Number of training sessions last year
- worklifebalance (int): Work-life balance rating 1-4 - CATEGORICAL
- yearsatcompany (int): Years at the company
- yearsincurrentrole (int): Years in current role
- yearssincelastpromotion (int): Years since last promotion
- yearswithcurrmanager (int): Years with current manager
"""


# ═══════════════════════════════════════════════════════════
# DATABASE CONNECTION
# ═══════════════════════════════════════════════════════════

def get_database_connection():
    """
    Create and return a database connection.
    
    Returns:
        SQLDatabase instance connected to PostgreSQL
    """
    # Build PostgreSQL connection URL safely
    encoded_pw = quote_plus(os.getenv("DB_PASSWORD"))
    postgres_url = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{encoded_pw}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    
    # Connect to PostgreSQL with hr_data schema
    db = SQLDatabase.from_uri(
        postgres_url,
        engine_args={"connect_args": {"options": f"-csearch_path={os.getenv('DB_SCHEMA', 'public')}"}}
    )
    
    return db


# ═══════════════════════════════════════════════════════════
# LLM INITIALIZATION
# ═══════════════════════════════════════════════════════════

def get_llm():
    """
    Initialize and return the LLM instance.
    Configured for Local LLM (LM Studio) by default.
    
    Returns:
        ChatOpenAI instance configured for local LLM
    """
    llm = ChatOpenAI(
        model=os.environ.get("OPENAI_MODEL", "ibm/granite-3.2-8b"),
        base_url=os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:1234/v1"),
        api_key=os.environ.get("OPENAI_API_KEY", "lm-studio"),
        temperature=0.0,
    )
    return llm


# ═══════════════════════════════════════════════════════════
# TEXT-TO-SQL AGENT
# ═══════════════════════════════════════════════════════════

class TextToSQLAgent:
    """
    Text-to-SQL Agent for HR Analytics.
    
    Converts natural language queries to SQL and executes them.
    """
    
    def __init__(self, db: SQLDatabase, llm: ChatOpenAI):
        """
        Initialize the agent with database connection and LLM.
        
        Args:
            db: LangChain SQLDatabase instance
            llm: LangChain ChatOpenAI instance
        """
        self.db = db
        self.llm = llm
        self.schema_info = self._get_structured_schema()
        self._setup_chain()
        
    def _get_structured_schema(self) -> str:
        """Generate CREATE TABLE style schema representation."""
        structured_schema = """
CREATE TABLE employee_attrition (
    -- Employee Demographics
    age INTEGER,
    gender TEXT,  -- Values: 'Male', 'Female'
    maritalstatus TEXT,  -- Values: 'Single', 'Married', 'Divorced'
    
    -- Employment Details
    employeenumber INTEGER PRIMARY KEY,
    department TEXT,  -- e.g., 'Sales', 'Research & Development', 'Human Resources'
    jobrole TEXT,  -- e.g., 'Sales Executive', 'Research Scientist', 'Manager'
    joblevel INTEGER,  -- Range: 1-5
    
    -- Work Conditions
    attrition TEXT,  -- Values: 'Yes', 'No' (TARGET VARIABLE)
    overtime TEXT,  -- Values: 'Yes', 'No'
    businesstravel TEXT,  -- Values: 'Travel_Rarely', 'Travel_Frequently', 'Non-Travel'
    distancefromhome INTEGER,
    
    -- Compensation
    monthlyincome INTEGER,
    monthlyrate INTEGER,
    dailyrate INTEGER,
    hourlyrate INTEGER,
    percentsalaryhike INTEGER,
    stockoptionlevel INTEGER,  -- Range: 0-3
    
    -- Work History
    totalworkingyears INTEGER,
    yearsatcompany INTEGER,
    yearsincurrentrole INTEGER,
    yearssincelastpromotion INTEGER,
    yearswithcurrmanager INTEGER,
    numcompaniesworked INTEGER,
    
    -- Satisfaction Ratings (1-4 scale: 1=Low, 4=High)
    jobsatisfaction INTEGER,
    environmentsatisfaction INTEGER,
    relationshipsatisfaction INTEGER,
    worklifebalance INTEGER,
    performancerating INTEGER,
    jobinvolvement INTEGER,
    
    -- Education
    education INTEGER,  -- Range: 1-5 (1=Below College, 5=Doctor)
    educationfield TEXT,  -- e.g., 'Life Sciences', 'Medical', 'Marketing'
    
    -- Training
    trainingtimeslastyear INTEGER
);
"""
        return structured_schema
    
    def _setup_chain(self):
        """Setup the LangChain prompt and chain."""
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "You are an expert PostgreSQL query generator. Generate ONLY valid SELECT queries.\n\n"
             
             "# CORE RULES\n"
             "1. Return ONLY raw SQL - no markdown, no explanations, no thinking tags\n"
             "2. All table/column names are LOWERCASE\n"
             "3. Only SELECT queries allowed (no INSERT/UPDATE/DELETE/DROP/ALTER/CREATE)\n"
             "4. Use ONLY columns from the schema below\n"
             "5. For ambiguous questions, make reasonable assumptions based on HR context\n"
             "6. ⚠️ CRITICAL: Use EXACT column names - watch for spelling (e.g., 'businesstravel' NOT 'businestravel')\n\n"
             
             "# CRITICAL: PERCENTAGE CALCULATIONS\n"
             "PostgreSQL uses integer division by default. Always cast to numeric:\n"
             "✓ CORRECT: (COUNT(...)::numeric / COUNT(*)::numeric) * 100\n"
             "✗ WRONG: (COUNT(...) / COUNT(*)) * 100  -- Returns 0!\n\n"
             
             "# QUERY PATTERNS\n\n"
             
             "## Pattern 1: Single Group Rate/Percentage\n"
             "Question: \"What is the [rate] for [specific group]?\"\n"
             "Solution: Use WHERE to filter, then calculate rate\n"
             "```sql\n"
             "SELECT ROUND((COUNT(CASE WHEN condition THEN 1 END)::numeric / COUNT(*)::numeric) * 100, 2) as rate\n"
             "FROM employee_attrition\n"
             "WHERE filter_condition;\n"
             "```\n\n"
             
             "## Pattern 2: Compare Groups\n"
             "Question: \"Compare [metric] between [group1] and [group2]\"\n"
             "Solution: Use GROUP BY\n"
             "```sql\n"
             "SELECT grouping_column, \n"
             "       COUNT(*) as total,\n"
             "       ROUND((COUNT(CASE WHEN condition THEN 1 END)::numeric / COUNT(*)::numeric) * 100, 2) as rate\n"
             "FROM employee_attrition\n"
             "GROUP BY grouping_column\n"
             "ORDER BY rate DESC;\n"
             "```\n\n"
             
             "# DATABASE SCHEMA\n"
             "```sql\n"
             "{schema}\n"
             "```\n\n"
             
             "# FEW-SHOT EXAMPLES\n\n"
             
             "Example 1:\n"
             "Q: What is the male attrition rate?\n"
             "A: SELECT ROUND((COUNT(CASE WHEN attrition='Yes' THEN 1 END)::numeric / COUNT(*)::numeric) * 100, 2) as male_attrition_rate FROM employee_attrition WHERE gender = 'Male'\n\n"
             
             "Example 2:\n"
             "Q: Compare attrition rates between genders\n"
             "A: SELECT gender, COUNT(*) as total_employees, COUNT(CASE WHEN attrition='Yes' THEN 1 END) as employees_left, ROUND((COUNT(CASE WHEN attrition='Yes' THEN 1 END)::numeric / COUNT(*)::numeric) * 100, 2) as attrition_rate FROM employee_attrition GROUP BY gender ORDER BY gender\n\n"
             
             "Example 3:\n"
             "Q: Show average salary by department\n"
             "A: SELECT department, COUNT(*) as employee_count, ROUND(AVG(monthlyincome)::numeric, 2) as avg_salary FROM employee_attrition GROUP BY department ORDER BY avg_salary DESC\n\n"
             
             "# IMPORTANT REMINDERS\n"
             "- ALWAYS cast to ::numeric for division operations\n"
             "- Use WHERE for single-group filters\n"
             "- Use GROUP BY for comparisons\n"
             "- Return ONLY the SQL query\n"),
            ("user", 
             "Generate a PostgreSQL query for: {question}\n\n"
             "Return ONLY the SQL query with no formatting or explanation.")
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def _extract_sql(self, text: str) -> str:
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
    
    def _validate_sql(self, sql: str) -> bool:
        """SQL validation with error messages."""
        sql_upper = sql.upper()
        
        if not sql_upper.strip().startswith("SELECT"):
            raise ValueError(f"Only SELECT queries allowed. Your query starts with: {sql[:50]}...")
        
        dangerous_ops = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE", "EXEC"]
        for op in dangerous_ops:
            if op in sql_upper:
                raise ValueError(f"Unsafe SQL: {op} operation not allowed")
        
        if "employee_attrition" not in sql.lower():
            raise ValueError("Query must reference 'employee_attrition' table")
        
        return True
    
    def generate_sql(self, question: str) -> str:
        """
        Generate SQL query from natural language question.
        
        Args:
            question: Natural language query
            
        Returns:
            SQL query string
        """
        response = self.chain.invoke({
            "schema": self.schema_info,
            "question": question
        })
        
        sql = self._extract_sql(response)
        self._validate_sql(sql)
        
        return sql
    
    def execute_sql(self, sql: str) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame.
        
        Args:
            sql: SQL query string
            
        Returns:
            pandas DataFrame with query results
        """
        with self.db._engine.connect() as conn:
            df = pd.read_sql(sql, conn)
        
        return df
    
    def query(self, question: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Complete pipeline: Question → SQL → DataFrame
        
        Args:
            question: Natural language query
            verbose: If True, print generated SQL
            
        Returns:
            Dictionary with 'sql', 'data' (DataFrame), and 'error' (if any)
        """
        try:
            # Generate SQL
            sql = self.generate_sql(question)
            
            if verbose:
                print("Generated SQL:", sql)
            
            # Execute and return DataFrame
            df = self.execute_sql(sql)
            
            return {
                "success": True,
                "sql": sql,
                "data": df,
                "rows": len(df),
                "columns": list(df.columns),
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "sql": None,
                "data": None,
                "rows": 0,
                "columns": [],
                "error": str(e)
            }


# ═══════════════════════════════════════════════════════════
# VISUALIZATION AGENT
# ═══════════════════════════════════════════════════════════

class VisualizationAgent:
    """
    Plotly Visualization Generator using LLM.
    
    Generates appropriate visualizations based on DataFrame content.
    """
    
    def __init__(self, llm: ChatOpenAI):
        """
        Initialize with LLM instance.
        
        Args:
            llm: LangChain ChatOpenAI instance
        """
        self.llm = llm
        self._setup_prompt()
    
    def _setup_prompt(self):
        """Setup the visualization generation prompt."""
        self.prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an EXPERT Python Plotly visualization developer. Your job is to generate COMPLETE, "
             "EXECUTABLE Python code that creates appropriate Plotly visualizations.\n\n"
             
             "CRITICAL RULES:\n"
             "1. Return ONLY executable Python code - NO markdown, NO explanations\n"
             "2. Code must be complete and ready to execute\n"
             "3. Assume 'df' variable already exists with the data\n"
             "4. Import statements: plotly.express as px, plotly.graph_objects as go\n"
             "5. MUST create variable 'fig' containing the Plotly figure\n"
             "6. DO NOT include fig.show() - just create the figure\n"
             "7. Use ONLY columns that exist in the data summary\n"
             "8. Handle missing data gracefully\n\n"
             
             "CHART TYPE SELECTION:\n"
             "- Bar Chart: Comparing categories\n"
             "- Grouped/Stacked Bar: Comparing categories with subcategories\n"
             "- Line Chart: Trends over time\n"
             "- Scatter Plot: Correlation between numerical variables\n"
             "- Pie Chart: Part-to-whole relationships (<7 categories)\n"
             "- Heatmap: Correlation matrix or 2D categorical data\n\n"
             
             "BEST PRACTICES:\n"
             "- Add meaningful titles describing the insight\n"
             "- Use texttemplate to show values on bars/points\n"
             "- Sort data logically\n"
             "- Add hover_data for context\n"
             "- Format numbers appropriately\n"
             "- Use template='plotly_white' for clean styling\n\n"
             
             "DATA SUMMARY:\n"
             "{data_summary}\n\n"
             
             "DATA DICTIONARY:\n"
             "{data_dictionary}\n\n"
             
             "Remember: Return ONLY Python code. No markdown, no explanations.\n"),
            ("user",
             "Create a Plotly visualization for this data:\n\n"
             "Original Question: {original_question}\n\n"
             "Generate complete, executable Python code that creates the most appropriate visualization.\n"
             "The code must create a 'fig' variable. DO NOT include fig.show().")
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def _get_data_summary(self, df: pd.DataFrame) -> str:
        """Generate a summary of the DataFrame for the LLM."""
        buffer = StringIO()
        df.info(buf=buffer)
        info_str = buffer.getvalue()
        
        summary = f"""
DATAFRAME SHAPE: {df.shape[0]} rows × {df.shape[1]} columns

COLUMN INFO:
{info_str}

FIRST 5 ROWS:
{df.head().to_string()}

BASIC STATISTICS:
{df.describe().to_string()}
"""
        return summary
    
    def _extract_code(self, text: str) -> str:
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
    
    def _detect_single_value_df(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame is single-value (1 row, 1 column)."""
        return df.shape[0] == 1 and df.shape[1] == 1
    
    def _generate_indicator_code(self, df: pd.DataFrame) -> str:
        """Generate code for single-value result as a bar chart."""
        value = float(df.iloc[0, 0])
        column_name = df.columns[0]
        title = column_name.replace('_', ' ').title()

        is_percentage = 'rate' in column_name.lower() or 'percent' in column_name.lower()

        return f"""import plotly.graph_objects as go

value = {value}
title_text = "{title}"

fig = go.Figure(go.Bar(
    x=[value],
    y=[title_text],
    orientation='h',
    marker={{'color': '#6366F1'}},
    text=[f"{{value:.2f}}{'%' if {is_percentage} else ''}"],
    textposition='outside'
))

xaxis_range = [0, 100] if {is_percentage} else None

fig.update_layout(
    height=320,
    template='plotly_white',
    title={{'text': title_text, 'x': 0.01}},
    xaxis={{
        'title': 'Percentage' if {is_percentage} else 'Value',
        'range': xaxis_range,
        'ticksuffix': '%' if {is_percentage} else ''
    }},
    yaxis={{'visible': False}},
    margin={{'l': 80, 'r': 40, 't': 60, 'b': 40}}
)
"""
    
    def generate_code(self, df: pd.DataFrame, original_question: str = "") -> str:
        """
        Generate Plotly visualization code based on DataFrame.
        
        Args:
            df: pandas DataFrame with data to visualize
            original_question: The original user question (for context)
            
        Returns:
            Python code string
        """
        # Special handling for single-value DataFrames
        if self._detect_single_value_df(df):
            return self._generate_indicator_code(df)
        
        data_summary = self._get_data_summary(df)
        
        response = self.chain.invoke({
            "data_summary": data_summary,
            "data_dictionary": DATA_DICTIONARY,
            "original_question": original_question or "Visualize this data"
        })
        
        code = self._extract_code(response)
        return code
    
    def visualize(self, df: pd.DataFrame, original_question: str = "", verbose: bool = False) -> Dict[str, Any]:
        """
        Complete pipeline: DataFrame → Code → Execution → Visualization
        
        Args:
            df: pandas DataFrame with data
            original_question: Original user question for context
            verbose: If True, print generated code
            
        Returns:
            Dictionary with 'success', 'code', 'figure', and 'error'
        """
        try:
            # Generate code
            code = self.generate_code(df, original_question)
            
            # Remove fig.show() if present (prevents opening browser windows)
            code = code.replace('fig.show()', '').strip()
            
            if verbose:
                print("Generated Code:")
                print(code)
            
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
                
        except Exception as e:
            return {
                "success": False,
                "code": code if 'code' in locals() else None,
                "figure": None,
                "error": str(e)
            }


# ═══════════════════════════════════════════════════════════
# COMBINED AGENT (For FastAPI Integration)
# ═══════════════════════════════════════════════════════════

class CombinedAgent:
    """
    Combined Text-to-SQL and Visualization Agent.
    
    Provides a single interface for both SQL generation and visualization.
    Ready for FastAPI integration.
    """
    
    def __init__(self):
        """Initialize the combined agent with database, LLM, and sub-agents."""
        self.db = get_database_connection()
        self.llm = get_llm()
        self.sql_agent = TextToSQLAgent(self.db, self.llm)
        self.viz_agent = VisualizationAgent(self.llm)
    
    def process_query(self, question: str, include_viz: bool = True, verbose: bool = False) -> Dict[str, Any]:
        """
        Process a natural language query end-to-end.
        
        Args:
            question: Natural language query about HR data
            include_viz: If True, generate visualization
            verbose: If True, print intermediate steps
            
        Returns:
            Dictionary with SQL, data, visualization code, and figure
        """
        # Step 1: Generate and execute SQL
        sql_result = self.sql_agent.query(question, verbose=verbose)
        
        if not sql_result["success"]:
            return {
                "success": False,
                "question": question,
                "sql": None,
                "data": None,
                "visualization": None,
                "error": sql_result["error"]
            }
        
        # Step 2: Generate visualization (if requested)
        viz_result = None
        if include_viz and sql_result["data"] is not None and len(sql_result["data"]) > 0:
            viz_result = self.viz_agent.visualize(
                sql_result["data"], 
                original_question=question,
                verbose=verbose
            )
        
        return {
            "success": True,
            "question": question,
            "sql": sql_result["sql"],
            "data": sql_result["data"],
            "rows": sql_result["rows"],
            "columns": sql_result["columns"],
            "visualization": viz_result,
            "error": None
        }
    
    def get_sql_only(self, question: str) -> Dict[str, Any]:
        """Get SQL and data without visualization."""
        return self.sql_agent.query(question)
    
    def get_visualization_only(self, df: pd.DataFrame, question: str = "") -> Dict[str, Any]:
        """Generate visualization for existing DataFrame."""
        return self.viz_agent.visualize(df, question)


# ═══════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS FOR FASTAPI
# ═══════════════════════════════════════════════════════════

def initialize_agent() -> CombinedAgent:
    """
    Initialize and return a CombinedAgent instance.
    Use this in FastAPI startup event.
    
    Returns:
        CombinedAgent instance ready to use
    """
    return CombinedAgent()


def query_to_dataframe(question: str, agent: CombinedAgent = None) -> Tuple[pd.DataFrame, str, Optional[str]]:
    """
    Simple function to get DataFrame from natural language query.
    
    Args:
        question: Natural language query
        agent: CombinedAgent instance (will create new if None)
        
    Returns:
        Tuple of (DataFrame, SQL query, error message)
    """
    if agent is None:
        agent = CombinedAgent()
    
    result = agent.get_sql_only(question)
    
    if result["success"]:
        return result["data"], result["sql"], None
    else:
        return None, None, result["error"]


# ═══════════════════════════════════════════════════════════
# MAIN - FOR TESTING
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    """
    Test the combined agent locally.
    Run: python TTS_vis.py
    """
    print("Initializing Combined Agent...")
    agent = CombinedAgent()
    print("✅ Agent initialized successfully!\n")
    
    # Test queries
    test_questions = [
        "What is the attrition rate by department?",
        "Show average monthly income by gender",
        "How many employees are in each job role?"
    ]
    
    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print('='*60)
        
        result = agent.process_query(question, include_viz=False, verbose=True)
        
        if result["success"]:
            print(f"\n✅ Success!")
            print(f"SQL: {result['sql']}")
            print(f"Rows returned: {result['rows']}")
            print(f"\nData preview:")
            print(result["data"].head())
        else:
            print(f"\n❌ Error: {result['error']}")
    
    print("\n" + "="*60)
    print("Testing complete!")
