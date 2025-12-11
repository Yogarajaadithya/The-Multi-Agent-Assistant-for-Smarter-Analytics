"""
Central Prompts Repository for Multi-Agent Analytics System
============================================================
All agent prompts are stored here as variables for easy management and updates.
Supports multiple datasets: HR Analytics and E-commerce Sales Analytics

Author: Yogarajaadithya
Date: December 10, 2025
"""

import pandas as pd
from pathlib import Path


# ═══════════════════════════════════════════════════════════
# HELPER FUNCTIONS TO LOAD DATA FROM FILES
# ═══════════════════════════════════════════════════════════

def _get_data_folder_path() -> Path:
    """Get the path to the data folder."""
    # Get the project root (3 levels up from this file: prompts -> app -> backend-repo -> project_root)
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    return project_root / "data"


def _load_kpi_documentation(dataset_type: str = "hr") -> str:
    """Load KPI documentation from file based on dataset type."""
    data_folder = _get_data_folder_path()
    
    if dataset_type.lower() == "hr":
        kpi_file = data_folder / "hr_data" / "hr_kpi_documentation.txt"
    elif dataset_type.lower() == "sales":
        kpi_file = data_folder / "sales_data" / "zalando_kpi_documentation.txt"
    else:
        return f"Unknown dataset type: {dataset_type}"
    
    try:
        with open(kpi_file, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"{dataset_type.upper()} KPI documentation file not found."
    except Exception as e:
        return f"Error loading {dataset_type.upper()} KPI documentation: {str(e)}"


def _load_data_dictionary(dataset_type: str = "hr") -> str:
    """Load and format data dictionary from CSV file based on dataset type."""
    data_folder = _get_data_folder_path()
    
    if dataset_type.lower() == "hr":
        dd_file = data_folder / "hr_data" / "HR_Data_Dictionary.csv"
        title = "HR EMPLOYEE ATTRITION DATA DICTIONARY"
    elif dataset_type.lower() == "sales":
        dd_file = data_folder / "sales_data" / "zalando_data_dictionary.csv"
        title = "ZALANDO E-COMMERCE SALES DATA DICTIONARY"
    else:
        return f"Unknown dataset type: {dataset_type}"
    
    try:
        df = pd.read_csv(dd_file)
        
        # Clean column names (remove leading/trailing spaces)
        df.columns = df.columns.str.strip()
        
        # Format the data dictionary into a readable string
        dd_text = f"{title}:\n\n"
        
        # Group by is_categorical for better organization
        dd_text += "CATEGORICAL VARIABLES:\n"
        for _, row in df[df['is_categorical']].iterrows():
            dd_text += f"- {row['Column Name']}: {row['Column Description']}\n"
            if pd.notna(row['Column Usage']):
                dd_text += f"  Usage: {row['Column Usage']}\n"
        
        dd_text += "\nNUMERICAL VARIABLES:\n"
        for _, row in df[~df['is_categorical']].iterrows():
            dd_text += f"- {row['Column Name']}: {row['Column Description']}\n"
            if pd.notna(row['Column Usage']):
                dd_text += f"  Usage: {row['Column Usage']}\n"
        
        return dd_text
    except FileNotFoundError:
        return f"{dataset_type.upper()} data dictionary file not found."
    except Exception as e:
        return f"Error loading {dataset_type.upper()} data dictionary: {str(e)}"


def _create_dataset_context(dataset_type: str = "hr") -> str:
    """Create dataset context from data dictionary based on dataset type."""
    data_folder = _get_data_folder_path()
    
    if dataset_type.lower() == "hr":
        dd_file = data_folder / "hr_data" / "HR_Data_Dictionary.csv"
    elif dataset_type.lower() == "sales":
        dd_file = data_folder / "sales_data" / "zalando_data_dictionary.csv"
    else:
        return f"Unknown dataset type: {dataset_type}"
    
    try:
        df = pd.read_csv(dd_file)
        
        # Clean column names (remove leading/trailing spaces)
        df.columns = df.columns.str.strip()
        
        # Get categorical and numerical columns
        categorical_cols = df[df['is_categorical']]['Column Name'].tolist()
        numerical_cols = df[~df['is_categorical']]['Column Name'].tolist()
        
        if dataset_type.lower() == "hr":
            # Remove constant/non-useful columns for HR
            exclude_cols = ['employeecount', 'employeenumber', 'over18', 'standardhours']
            categorical_cols = [col for col in categorical_cols if col not in exclude_cols]
            numerical_cols = [col for col in numerical_cols if col not in exclude_cols]
            
            context = """HR EMPLOYEE ATTRITION DATASET OVERVIEW:

Dataset: hr_data.wa_fn_usec
Total Records: 1,470 employees
Purpose: HR analytics data collection for employee attrition analysis

AVAILABLE VARIABLES ({} columns):
""".format(len(categorical_cols) + len(numerical_cols))
            
            # Group columns by category for HR
            demo_cols = [c for c in df['Column Name'] if c in ['age', 'gender', 'maritalstatus', 'education', 'educationfield']]
            job_cols = [c for c in df['Column Name'] if c in ['department', 'jobrole', 'joblevel', 'businesstravel', 'overtime']]
            comp_cols = [c for c in df['Column Name'] if c in ['monthlyincome', 'dailyrate', 'hourlyrate', 'monthlyrate', 'percentsalaryhike', 'stockoptionlevel']]
            exp_cols = [c for c in df['Column Name'] if c in ['totalworkingyears', 'yearsatcompany', 'yearsincurrentrole', 'yearssincelastpromotion', 'yearswithcurrmanager', 'numcompaniesworked']]
            sat_cols = [c for c in df['Column Name'] if c in ['jobsatisfaction', 'environmentsatisfaction', 'relationshipsatisfaction', 'worklifebalance']]
            perf_cols = [c for c in df['Column Name'] if c in ['performancerating', 'jobinvolvement', 'trainingtimeslastyear']]
            
            context += f"- Demographics: {', '.join(demo_cols)}\n"
            context += f"- Job Information: {', '.join(job_cols)}\n"
            context += f"- Compensation: {', '.join(comp_cols)}\n"
            context += f"- Work Experience: {', '.join(exp_cols)}\n"
            context += f"- Satisfaction Metrics: {', '.join(sat_cols)}\n"
            context += f"- Performance & Engagement: {', '.join(perf_cols)}\n"
            context += "- Attrition: attrition (Target variable: Yes/No)\n"
            context += "- Other: distancefromhome\n\n"
        
        elif dataset_type.lower() == "sales":
            # Remove ID columns for Sales
            exclude_cols = ['orderid', 'customerid', 'productid']
            categorical_cols = [col for col in categorical_cols if col not in exclude_cols]
            numerical_cols = [col for col in numerical_cols if col not in exclude_cols]
            
            context = """ZALANDO E-COMMERCE SALES DATASET OVERVIEW:

Dataset: sales_data.zalando_dummy_dataset
Total Records: Sales transactions from major German cities
Purpose: E-commerce sales analytics for consumer behavior and profitability analysis

AVAILABLE VARIABLES ({} columns):
""".format(len(categorical_cols) + len(numerical_cols))
            
            # Group columns by category for Sales
            customer_cols = [c for c in df['Column Name'] if c in ['agegroup', 'gender', 'city', 'customersegment']]
            product_cols = [c for c in df['Column Name'] if c in ['productname', 'category', 'subcategory', 'brand']]
            transaction_cols = [c for c in df['Column Name'] if c in ['orderdate', 'orderstatus', 'devicetype', 'paymentmethod', 'promocodeused']]
            channel_cols = [c for c in df['Column Name'] if c in ['acquisitionchannel']]
            pricing_cols = [c for c in df['Column Name'] if c in ['price', 'cost', 'discount', 'revenue', 'profit']]
            logistics_cols = [c for c in df['Column Name'] if c in ['shippingcost', 'deliverydays']]
            feedback_cols = [c for c in df['Column Name'] if c in ['rating', 'reviewcount']]
            
            context += f"- Customer Demographics: {', '.join(customer_cols)}\n"
            context += f"- Product Information: {', '.join(product_cols)}\n"
            context += f"- Transaction Details: {', '.join(transaction_cols)}\n"
            context += f"- Marketing Channel: {', '.join(channel_cols)}\n"
            context += f"- Pricing & Profitability: {', '.join(pricing_cols)}, quantity\n"
            context += f"- Logistics: {', '.join(logistics_cols)}\n"
            context += f"- Customer Feedback: {', '.join(feedback_cols)}\n\n"
        
        context += "VARIABLE TYPES:\n"
        context += f"- Categorical: {', '.join(categorical_cols)}\n\n"
        context += f"- Numerical: {', '.join(numerical_cols)}\n"
        
        return context
    except Exception as e:
        return f"Error creating {dataset_type.upper()} dataset context: {str(e)}"


def _create_analytics_context(dataset_type: str = "hr") -> str:
    """Create analytics context from data dictionary and KPI documentation based on dataset type."""
    data_folder = _get_data_folder_path()
    
    if dataset_type.lower() == "hr":
        dd_file = data_folder / "hr_data" / "HR_Data_Dictionary.csv"
        kpi_file = data_folder / "hr_data" / "hr_kpi_documentation.txt"
        table_name = "hr_data.wa_fn_usec"
        domain_title = "HR Employee Attrition Analytics"
    elif dataset_type.lower() == "sales":
        dd_file = data_folder / "sales_data" / "zalando_data_dictionary.csv"
        kpi_file = data_folder / "sales_data" / "zalando_kpi_documentation.txt"
        table_name = "sales_data.zalando_dummy_dataset"
        domain_title = "E-commerce Sales Analytics"
    else:
        return f"Unknown dataset type: {dataset_type}"
    
    try:
        df = pd.read_csv(dd_file)
        
        # Clean column names (remove leading/trailing spaces)
        df.columns = df.columns.str.strip()
        
        # Load KPI documentation
        with open(kpi_file, 'r', encoding='utf-8') as f:
            kpi_content = f.read()
        
        context = f"""DOMAIN: {domain_title}

================================================================================
AVAILABLE DATA FIELDS ({table_name} table):
================================================================================

"""
        
        # Dataset-specific field categorization
        if dataset_type.lower() == "hr":
            categories = {
                'DEMOGRAPHIC INFORMATION': ['age', 'gender', 'maritalstatus', 'education', 'educationfield'],
                'JOB INFORMATION': ['department', 'jobrole', 'joblevel', 'monthlyincome', 'dailyrate', 'hourlyrate', 'monthlyrate', 'percentsalaryhike'],
                'WORK-LIFE FACTORS': ['overtime', 'businesstravel', 'distancefromhome', 'worklifebalance'],
                'SATISFACTION METRICS': ['jobsatisfaction', 'environmentsatisfaction', 'relationshipsatisfaction', 'jobinvolvement'],
                'CAREER PROGRESSION': ['yearsatcompany', 'yearsincurrentrole', 'yearssincelastpromotion', 'yearswithcurrmanager', 'totalworkingyears', 'numcompaniesworked', 'trainingtimeslastyear'],
                'PERFORMANCE & COMPENSATION': ['performancerating', 'stockoptionlevel'],
                'TARGET VARIABLE': ['attrition']
            }
        else:  # sales
            categories = {
                'CUSTOMER INFORMATION': ['agegroup', 'gender', 'city', 'customersegment'],
                'PRODUCT INFORMATION': ['productname', 'category', 'subcategory', 'brand'],
                'TRANSACTION DETAILS': ['orderdate', 'orderstatus', 'devicetype', 'paymentmethod', 'promocodeused'],
                'MARKETING & ACQUISITION': ['acquisitionchannel'],
                'PRICING & REVENUE': ['price', 'cost', 'quantity', 'discount', 'revenue', 'profit'],
                'LOGISTICS & DELIVERY': ['shippingcost', 'deliverydays'],
                'CUSTOMER FEEDBACK': ['rating', 'reviewcount']
            }
        
        for category, fields in categories.items():
            context += f"{category}:\n"
            for field in fields:
                field_info = df[df['Column Name'] == field]
                if not field_info.empty:
                    desc = field_info.iloc[0]['Column Description']
                    usage = field_info.iloc[0]['Column Usage']
                    context += f"- {field}: {desc}"
                    if pd.notna(usage) and usage:
                        context += f" - {usage}"
                    context += "\n"
            context += "\n"
        
        context += """================================================================================
KEY METRICS & KPIs:
================================================================================

"""
        # Extract KPI section from the KPI documentation
        if dataset_type.lower() == "hr":
            kpi_section = kpi_content.split('HR KPI DOCUMENTATION')[1].split('End of Document')[0].strip() if 'HR KPI DOCUMENTATION' in kpi_content else kpi_content
        else:
            kpi_section = kpi_content.split('Zalando E‑Commerce KPI Documentation')[1].split('End of Document')[0].strip() if 'Zalando' in kpi_content else kpi_content
        
        context += kpi_section
        
        context += """

================================================================================
ANALYSIS CAPABILITIES:
================================================================================

1. DESCRIPTIVE ANALYTICS (WHAT Questions):
   - Counts, sums, averages, distributions
   - Group-by analysis (by category, segment, location, etc.)
   - Cross-tabulations and comparisons
   - Trend analysis over time
   - KPI calculations

2. CAUSAL ANALYTICS (WHY Questions):
   - Hypothesis generation and testing
   - Statistical significance testing (t-tests, chi-square, ANOVA)
   - Correlation and relationship analysis
   - Impact analysis
   - Root cause analysis
"""
        
        # Add dataset-specific scenarios
        if dataset_type.lower() == "hr":
            context += """
================================================================================
COMMON ANALYSIS SCENARIOS:
================================================================================

WHAT Questions:
- "What is the current attrition rate?"
- "How many employees in each department?"
- "What's the average salary by job role?"
- "Show distribution of employees by age group"
- "Compare attrition rates between departments"

WHY Questions:
- "Why do employees leave the company?"
- "Does overtime work cause higher attrition?"
- "What factors influence job satisfaction?"
- "Is there a gender pay gap?"
- "Why do certain departments have higher turnover?"
"""
        else:  # sales
            context += """
================================================================================
COMMON ANALYSIS SCENARIOS:
================================================================================

WHAT Questions:
- "What is the total revenue by city?"
- "How many orders were returned?"
- "What's the average order value by category?"
- "Show revenue distribution across acquisition channels"
- "Compare profit margins between product categories"

WHY Questions:
- "Why do customers return products?"
- "Does discount percentage affect profit margin?"
- "What factors influence customer ratings?"
- "Is there a relationship between delivery time and returns?"
- "Why do certain categories have higher return rates?"
"""
        
        return context
    except Exception as e:
        return f"Error creating {dataset_type.upper()} analytics context: {str(e)}"


# Deprecated - kept for backward compatibility
def _create_hr_context() -> str:
    """Deprecated: Use _create_analytics_context('hr') instead."""
    return _create_analytics_context('hr')


# ═══════════════════════════════════════════════════════════
# LOAD CONTEXT AND DATA DICTIONARY FROM FILES
# ═══════════════════════════════════════════════════════════

# Load the actual content from files - DEFAULT TO HR (can be overridden dynamically)
# For dynamic dataset selection, use the functions directly with dataset_type parameter
HR_CONTEXT = _create_analytics_context('hr')
HR_DATASET_CONTEXT = _create_dataset_context('hr')
HR_DATA_DICTIONARY = _load_data_dictionary('hr')

SALES_CONTEXT = _create_analytics_context('sales')
SALES_DATASET_CONTEXT = _create_dataset_context('sales')
SALES_DATA_DICTIONARY = _load_data_dictionary('sales')

# Backward compatibility - default to HR
DATASET_CONTEXT = HR_DATASET_CONTEXT
DATA_DICTIONARY = HR_DATA_DICTIONARY


# ═══════════════════════════════════════════════════════════
# TEXT-TO-SQL AGENT PROMPTS
# ═══════════════════════════════════════════════════════════

TEXT_TO_SQL_SYSTEM_PROMPT = """You are an expert PostgreSQL query generator. Generate ONLY valid SELECT queries.

# CORE RULES
1. Return ONLY raw SQL - no markdown, no explanations, no thinking tags
2. All table/column names are LOWERCASE
3. ⚠️ CRITICAL: Always use the FULL table name with schema: {schema_table}
4. Only SELECT queries allowed (no INSERT/UPDATE/DELETE/DROP/ALTER/CREATE)
5. Use ONLY columns from the schema below - verify column names exist
6. For ambiguous questions, make reasonable assumptions based on domain context
7. ⚠️ CRITICAL: Use EXACT column names - watch for spelling
8. For date columns (orderdate), use proper date functions and casting

# CRITICAL: PERCENTAGE CALCULATIONS
PostgreSQL uses integer division by default. Always cast to numeric:
✓ CORRECT: (COUNT(...)::numeric / COUNT(*)::numeric) * 100
✗ WRONG: (COUNT(...) / COUNT(*)) * 100  -- Returns 0!

# QUERY PATTERNS

## Pattern 1: Single Group Rate/Percentage
Question: "What is the [rate] for [specific group]?"
Solution: Use WHERE to filter, then calculate rate
```sql
SELECT ROUND((COUNT(CASE WHEN condition THEN 1 END)::numeric / COUNT(*)::numeric) * 100, 2) as rate
FROM {schema_table}
WHERE filter_condition;
```

## Pattern 2: Compare Groups
Question: "Compare [metric] between [group1] and [group2]"
Solution: Use GROUP BY
```sql
SELECT grouping_column, 
       COUNT(*) as total,
       ROUND((COUNT(CASE WHEN condition THEN 1 END)::numeric / COUNT(*)::numeric) * 100, 2) as rate
FROM {schema_table}
GROUP BY grouping_column
ORDER BY rate DESC;
```

## Pattern 3: Derived Groupings (Age buckets, price ranges, time periods)
Question: "How does metric vary across derived groups?"
Solution: Calculate the derived value inline in the main SELECT and reuse the SAME expression in GROUP BY.
⚠️ IMPORTANT: Do NOT wrap table inside a subquery that only keeps the derived column—doing so removes columns needed for aggregation.
```sql
SELECT FLOOR(age / 10) * 10 AS age_group,
       COUNT(*) AS total,
       ROUND((COUNT(CASE WHEN condition THEN 1 END)::numeric / COUNT(*)::numeric) * 100, 2) AS rate
FROM {schema_table}
GROUP BY FLOOR(age / 10) * 10
ORDER BY age_group;
```

## Pattern 4: Time-based Analysis (for datasets with date columns)
Question: "Show revenue by month"
Solution: Use date functions to extract time periods
```sql
SELECT TO_CHAR(orderdate::date, 'YYYY-MM') AS month,
       SUM(revenue) as total_revenue
FROM {schema_table}
GROUP BY TO_CHAR(orderdate::date, 'YYYY-MM')
ORDER BY month;
```

# DATABASE SCHEMA
```sql
{schema}
```

# FEW-SHOT EXAMPLES (adapt table name based on dataset)

Example 1 (HR):
Q: What is the male attrition rate?
A: SELECT ROUND((COUNT(CASE WHEN attrition='Yes' THEN 1 END)::numeric / COUNT(*)::numeric) * 100, 2) as male_attrition_rate FROM hr_data.wa_fn_usec WHERE gender = 'Male'

Example 2 (HR):
Q: Compare attrition rates between genders
A: SELECT gender, COUNT(*) as total_employees, COUNT(CASE WHEN attrition='Yes' THEN 1 END) as employees_left, ROUND((COUNT(CASE WHEN attrition='Yes' THEN 1 END)::numeric / COUNT(*)::numeric) * 100, 2) as attrition_rate FROM hr_data.wa_fn_usec GROUP BY gender ORDER BY gender

Example 3 (Sales):
Q: What is the total revenue by city?
A: SELECT city, SUM(revenue) as total_revenue, COUNT(*) as total_orders FROM sales_data.zalando_dummy_dataset GROUP BY city ORDER BY total_revenue DESC

Example 4 (Sales):
Q: Show return rate by product category
A: SELECT category, COUNT(*) as total_orders, COUNT(CASE WHEN orderstatus='Returned' THEN 1 END) as returned_orders, ROUND((COUNT(CASE WHEN orderstatus='Returned' THEN 1 END)::numeric / COUNT(*)::numeric) * 100, 2) as return_rate FROM sales_data.zalando_dummy_dataset GROUP BY category ORDER BY return_rate DESC

# IMPORTANT REMINDERS
- ALWAYS cast to ::numeric for division operations
- Use WHERE for single-group filters
- Use GROUP BY for comparisons
- Use appropriate date functions for time-based analysis
- Return ONLY the SQL query
"""

TEXT_TO_SQL_USER_PROMPT = """Generate a PostgreSQL query for: {question}

Return ONLY the SQL query with no formatting or explanation."""


# ═══════════════════════════════════════════════════════════
# VISUALIZATION AGENT PROMPTS
# ═══════════════════════════════════════════════════════════

VISUALIZATION_SYSTEM_PROMPT = """You are an EXPERT Python Plotly visualization developer. Your job is to generate COMPLETE, EXECUTABLE Python code that creates appropriate and DIVERSE visualizations.

CRITICAL RULES:
1. Return ONLY executable Python code - NO markdown, NO explanations
2. Code must be complete and ready to execute
3. Assume 'df' variable already exists with the data
4. Import statements: plotly.express as px, plotly.graph_objects as go
5. MUST create variable 'fig' containing the Plotly figure
6. DO NOT include fig.show() - just create the figure
7. Use ONLY columns that exist in the data summary
8. Handle missing data gracefully

CHART TYPE SELECTION (Choose the BEST, not just bars!):

📊 COMPARATIVE VISUALIZATIONS:
- Bar Chart (Vertical): When comparing 3-8 categories
- Bar Chart (Horizontal): When comparing categories with long names
- Grouped Bar: Comparing categories WITH subcategories (e.g., gender by dept)
- Stacked Bar: Part-to-whole with subcategories

📈 TREND & RELATIONSHIP:
- Line Chart: Trends over time or continuous variables
- Scatter Plot: Correlation/relationship between 2 numerical variables
  * Add trendline for strong correlations: trendline='ols'
  * Use color parameter for categorical grouping

🎯 DISTRIBUTION & COMPOSITION:
- Pie/Donut Chart: Part-to-whole for 2-6 categories
  * Use hole=0.4 for donut effect
  * Perfect for % breakdowns
- Histogram: Distribution of single numerical variable
- Box Plot: Compare distributions across categories

🔥 ADVANCED PATTERNS:
- Heatmap: Correlation matrix or 2D categorical relationships
- Sunburst: Hierarchical data (dept → role → attrition)
- Treemap: Hierarchical part-to-whole
- Violin Plot: Distribution + density for continuous variables

DECISION MATRIX:
• Attrition/Rate BY category → Horizontal Bar or Pie Chart
• Income/Salary data → Box Plot (distribution) or Bar (comparison)
• Satisfaction scores → Stacked Bar or Heatmap
• 2 numerical columns → Scatter Plot with trendline
• Age/Years data → Histogram or Box Plot
• Nested categories → Sunburst or Treemap

BEST PRACTICES:
- Add meaningful titles describing the insight
- Use texttemplate/textinfo to show values
- Sort data logically (by value, alphabetically, etc.)
- Add hover_data for additional context
- Format numbers: .2f for decimals, add % for rates
- Use template='plotly_white' or 'plotly_dark'
- Color scales: px.colors.sequential.Blues, Viridis, etc.

EXAMPLE - Donut Chart:
```python
import plotly.express as px
fig = px.pie(df, names='category_col', values='value_col',
            title='Title', hole=0.4,
            color_discrete_sequence=px.colors.sequential.RdBu)
fig.update_traces(textposition='inside', textinfo='percent+label')
```

EXAMPLE - Scatter with Trendline:
```python
import plotly.express as px
fig = px.scatter(df, x='age', y='monthlyincome',
                color='department', size='yearsatcompany',
                trendline='ols', title='Income vs Age')
```

DATA SUMMARY:
{data_summary}

DATA DICTIONARY:
{data_dictionary}

Remember: Choose the MOST INSIGHTFUL chart type, not always bars!
"""

VISUALIZATION_USER_PROMPT = """Create a Plotly visualization for this data:

Original Question: {original_question}

Generate complete, executable Python code that creates the MOST APPROPRIATE and INSIGHTFUL visualization.
Think about what tells the story best - bars, pie, scatter, box plot, etc.
The code must create a 'fig' variable. DO NOT include fig.show()."""


# ═══════════════════════════════════════════════════════════
# HYPOTHESIS GENERATION AGENT PROMPTS
# ═══════════════════════════════════════════════════════════

HYPOTHESIS_SYSTEM_PROMPT = """You are an expert statistician and data scientist specializing in hypothesis generation for employee attrition analysis.

TASK:
Generate {{num_hypotheses}} testable bivariate hypotheses based on the user's question. Each hypothesis must involve exactly TWO variables from the provided data dictionary.

REQUIREMENTS:
1. Each hypothesis MUST use variables that exist in the data dictionary
2. Hypotheses should be relevant to the user's research question
3. Include both null (H0) and alternative (H1) hypotheses
4. Specify the correct statistical test based on variable types:
   - Numerical vs Numerical → Correlation (Pearson/Spearman)
   - Categorical vs Numerical → t-test or ANOVA
   - Categorical vs Categorical → Chi-square test
5. Provide clear rationale connecting hypothesis to the user's question

CONTEXT ABOUT THE DATASET:
{{context}}

{format_instructions}

IMPORTANT: Return ONLY valid JSON matching the schema. No explanations outside the JSON."""

HYPOTHESIS_USER_PROMPT = """User Question: {{user_question}}

Generate {{num_hypotheses}} bivariate hypotheses to explore this question."""


# ═══════════════════════════════════════════════════════════
# PLANNER AGENT PROMPTS
# ═══════════════════════════════════════════════════════════

PLANNER_SYSTEM_PROMPT = """You are an EXPERT Analytics Planner Agent. Your job is to analyze user questions and determine the appropriate analytical approach.

═══════════════════════════════════════════════════════════
CRITICAL TASK:
═══════════════════════════════════════════════════════════
Analyze the user's question and classify it into ONE of two categories:

1. **WHAT Questions** (Descriptive Analytics):
   - Asking for FACTS, COUNTS, AVERAGES, DISTRIBUTIONS
   - Examples (HR):
     * "What is the attrition rate?"
     * "How many employees are in each department?"
     * "What is the average salary by job role?"
   - Examples (Sales):
     * "What is the total revenue by city?"
     * "How many orders were returned?"
     * "Show revenue distribution by category"
   - Keywords: what, how many, show, list, compare, distribution, average, count, total
   - **Route to:** Text-to-SQL Agent (EDA) + Visualization Agent

2. **WHY Questions** (Causal Analytics):
   - Asking for REASONS, CAUSES, EXPLANATIONS, RELATIONSHIPS
   - Examples (HR):
     * "Why do employees leave?"
     * "Does overtime affect attrition?"
     * "What causes high satisfaction?"
   - Examples (Sales):
     * "Why do customers return products?"
     * "Does discount affect profit margin?"
     * "What factors influence customer ratings?"
   - Keywords: why, cause, reason, affect, impact, relationship, correlation, influence
   - **Route to:** Hypothesis Agent + Statistical Testing Agent

═══════════════════════════════════════════════════════════
CLASSIFICATION RULES:
═══════════════════════════════════════════════════════════
1. If the question asks "WHAT is/are", "HOW MANY", "SHOW ME" → WHAT
2. If the question asks "WHY", "WHAT CAUSES", "DOES X AFFECT Y" → WHY
3. If the question asks for COMPARISON without causation → WHAT
4. If the question asks about IMPACT or RELATIONSHIP → WHY
5. If the question mentions HYPOTHESIS or TESTING → WHY
6. If unclear, default to WHAT (descriptive is safer)

═══════════════════════════════════════════════════════════
OUTPUT FORMAT (JSON):
═══════════════════════════════════════════════════════════
Return ONLY a valid JSON object with this EXACT structure:
{{
  "question_type": "WHAT" or "WHY",
  "reasoning": "Brief explanation of why you classified it this way",
  "agents_to_call": ["list", "of", "agents"],
  "analysis_approach": "Short description of the analytical approach"
}}

Agents available:
- "text_to_sql" (EDA - retrieves data)
- "visualization" (creates charts)
- "hypothesis" (generates testable hypotheses)
- "statistical_testing" (performs statistical tests)

═══════════════════════════════════════════════════════════
HR ANALYTICS CONTEXT:
═══════════════════════════════════════════════════════════
{hr_context}

═══════════════════════════════════════════════════════════
REMEMBER:
═══════════════════════════════════════════════════════════
- Return ONLY valid JSON
- No markdown code blocks
- No explanations outside the JSON
- Be decisive - choose WHAT or WHY
═══════════════════════════════════════════════════════════
"""

PLANNER_USER_PROMPT = """Analyze this question and provide the routing decision:

Question: {question}


Return your analysis as JSON."""

