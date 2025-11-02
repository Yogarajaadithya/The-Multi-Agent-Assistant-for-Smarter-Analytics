"""
Hypothesis Generation and Statistical Testing Agents
====================================================
Generates testable hypotheses and performs statistical tests for HR analytics.

Author: Yogarajaadithya
Date: October 31, 2025
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Literal
from scipy.stats import chi2_contingency, pearsonr, spearmanr, f_oneway, ttest_ind
from sqlalchemy import create_engine
from urllib.parse import quote_plus

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════
# SCHEMA DEFINITIONS
# ═══════════════════════════════════════════════════════════

class BivariateHypothesis(BaseModel):
    """Single bivariate hypothesis with all required fields."""
    
    hypothesis_id: int = Field(description="Unique identifier for the hypothesis (1, 2, 3, ...)")
    null_hypothesis: str = Field(description="The null hypothesis (H0) stating no relationship or effect exists")
    alternative_hypothesis: str = Field(description="The alternative hypothesis (H1) stating the expected relationship or effect")
    variable_1: str = Field(description="First variable name (must exist in data dictionary)")
    variable_2: str = Field(description="Second variable name (must exist in data dictionary)")
    variable_1_type: Literal["categorical", "numerical"] = Field(description="Data type of variable 1")
    variable_2_type: Literal["categorical", "numerical"] = Field(description="Data type of variable 2")
    recommended_test: str = Field(description="Statistical test to use (e.g., 't-test', 'chi-square', 'ANOVA', 'correlation')")
    rationale: str = Field(description="Brief explanation of why this hypothesis is relevant to the user's question")


class HypothesisList(BaseModel):
    """List of bivariate hypotheses."""
    hypotheses: List[BivariateHypothesis] = Field(description="List of generated bivariate hypotheses")


# ═══════════════════════════════════════════════════════════
# DATA DICTIONARY
# ═══════════════════════════════════════════════════════════

DATASET_CONTEXT = """
HR EMPLOYEE ATTRITION DATASET OVERVIEW:

Dataset: employee_attrition
Total Records: 1,470 employees
Purpose: HR analytics data collection for employee attrition analysis

AVAILABLE VARIABLES (35 columns):
- Demographics: age, gender, maritalstatus, education, educationfield
- Job Information: department, jobrole, joblevel, businesstravel, overtime
- Compensation: monthlyincome, dailyrate, hourlyrate, monthlyrate, percentsalaryhike, stockoptionlevel
- Work Experience: totalworkingyears, yearsatcompany, yearsincurrentrole, yearssincelastpromotion, yearswithcurrmanager, numcompaniesworked
- Satisfaction Metrics: jobsatisfaction, environmentsatisfaction, relationshipsatisfaction, worklifebalance
- Performance & Engagement: performancerating, jobinvolvement, trainingtimeslastyear
- Attrition: attrition (Target variable: Yes/No)
- Other: distancefromhome

VARIABLE TYPES:
- Categorical: attrition, businesstravel, department, education, educationfield, environmentsatisfaction, 
  gender, jobinvolvement, joblevel, jobrole, jobsatisfaction, maritalstatus, overtime, performancerating, 
  relationshipsatisfaction, stockoptionlevel, worklifebalance
  
- Numerical: age, dailyrate, distancefromhome, hourlyrate, monthlyincome, monthlyrate, numcompaniesworked, 
  percentsalaryhike, totalworkingyears, trainingtimeslastyear, yearsatcompany, yearsincurrentrole, 
  yearssincelastpromotion, yearswithcurrmanager
"""


# ═══════════════════════════════════════════════════════════
# HYPOTHESIS GENERATION AGENT
# ═══════════════════════════════════════════════════════════

class HypothesisAgent:
    """
    Hypothesis Generation Agent for HR Analytics.
    
    Generates testable bivariate hypotheses based on user questions.
    """
    
    def __init__(self, llm: ChatOpenAI):
        """
        Initialize hypothesis generation agent.
        
        Args:
            llm: LangChain ChatOpenAI instance
        """
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=HypothesisList)
        self._setup_prompt()
    
    def _setup_prompt(self):
        """Setup the hypothesis generation prompt."""
        # Get format instructions and escape braces for ChatPromptTemplate
        format_instructions = self.parser.get_format_instructions()
        # Escape all { and } by doubling them for LangChain template
        escaped_format_instructions = format_instructions.replace('{', '{{').replace('}', '}}')
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "You are an expert statistician and data scientist specializing in hypothesis generation "
             "for employee attrition analysis.\n\n"
             
             "TASK:\n"
             "Generate {{num_hypotheses}} testable bivariate hypotheses based on the user's question. "
             "Each hypothesis must involve exactly TWO variables from the provided data dictionary.\n\n"
             
             "REQUIREMENTS:\n"
             "1. Each hypothesis MUST use variables that exist in the data dictionary\n"
             "2. Hypotheses should be relevant to the user's research question\n"
             "3. Include both null (H0) and alternative (H1) hypotheses\n"
             "4. Specify the correct statistical test based on variable types:\n"
             "   - Numerical vs Numerical → Correlation (Pearson/Spearman)\n"
             "   - Categorical vs Numerical → t-test or ANOVA\n"
             "   - Categorical vs Categorical → Chi-square test\n"
             "5. Provide clear rationale connecting hypothesis to the user's question\n\n"
             
             "CONTEXT ABOUT THE DATASET:\n"
             "{{context}}\n\n"
             
             f"{escaped_format_instructions}\n\n"
             
             "IMPORTANT: Return ONLY valid JSON matching the schema. No explanations outside the JSON."),
            
            ("user", 
             "User Question: {{user_question}}\n\n"
             "Generate {{num_hypotheses}} bivariate hypotheses to explore this question.")
        ])
        
        self.chain = self.prompt | self.llm | self.parser
    
    def generate_hypotheses(
        self,
        user_question: str,
        num_hypotheses: int = 3
    ) -> Dict[str, Any]:
        """
        Generate bivariate hypotheses based on user question.
        
        Args:
            user_question: The research question from the user
            num_hypotheses: Number of hypotheses to generate (default: 3)
            
        Returns:
            Dictionary containing list of hypotheses in JSON format
        """
        try:
            print(f"🔬 Generating {num_hypotheses} hypotheses for question: '{user_question}'")
            
            result = self.chain.invoke({
                "user_question": user_question,
                "num_hypotheses": num_hypotheses,
                "context": DATASET_CONTEXT
            })
            
            # Convert Pydantic model to dict
            result_dict = result.dict()
            print(f"✅ Successfully generated {len(result_dict.get('hypotheses', []))} hypotheses")
            return result_dict
            
        except TimeoutError as e:
            error_msg = f"LLM request timed out after 120 seconds: {str(e)}"
            print(f"❌ TIMEOUT ERROR: {error_msg}")
            return {
                "error": error_msg,
                "hypotheses": []
            }
        except ConnectionError as e:
            error_msg = f"Failed to connect to LLM server: {str(e)}"
            print(f"❌ CONNECTION ERROR: {error_msg}")
            return {
                "error": error_msg,
                "hypotheses": []
            }
        except Exception as e:
            error_msg = f"Hypothesis generation failed: {str(e)}"
            print(f"❌ GENERAL ERROR: {error_msg}")
            print(f"📋 Error type: {type(e).__name__}")
            import traceback
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            return {
                "error": error_msg,
                "hypotheses": []
            }


# ═══════════════════════════════════════════════════════════
# STATISTICAL TESTING AGENT
# ═══════════════════════════════════════════════════════════

class StatsAgent:
    """
    Statistical Testing Agent.
    
    Executes appropriate tests based on hypothesis variable types.
    """
    
    def __init__(self, dataframe: pd.DataFrame):
        """
        Initialize the Stats Agent with a dataset.
        
        Args:
            dataframe: The dataset to perform statistical tests on
        """
        self.df = dataframe
        # Normalize column names to lowercase
        self.df.columns = self.df.columns.str.lower()
    
    def chi_square_test(self, var1: str, var2: str) -> dict:
        """Perform Chi-Square test for two categorical variables."""
        try:
            contingency_table = pd.crosstab(self.df[var1], self.df[var2])
            chi2, p_value, dof, expected_freq = chi2_contingency(contingency_table)
            
            n = contingency_table.sum().sum()
            min_dim = min(contingency_table.shape) - 1
            cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0
            
            return {
                "test_name": "Chi-Square Test of Independence",
                "test_type": "categorical_vs_categorical",
                "variable_1": var1,
                "variable_2": var2,
                "chi2_statistic": round(chi2, 4),
                "p_value": round(p_value, 6),
                "degrees_of_freedom": int(dof),
                "cramers_v": round(cramers_v, 4),
                "sample_size": int(n),
                "interpretation": self._interpret_p_value(p_value),
                "effect_size_interpretation": self._interpret_cramers_v(cramers_v)
            }
        except Exception as e:
            return {"error": f"Chi-square test failed: {str(e)}"}
    
    def t_test(self, categorical_var: str, numerical_var: str) -> dict:
        """Perform Independent T-Test for categorical (2 groups) vs numerical variable."""
        try:
            groups = self.df[categorical_var].unique()
            
            if len(groups) != 2:
                return {"error": f"T-test requires exactly 2 groups, found {len(groups)}. Use ANOVA instead."}
            
            group1_data = self.df[self.df[categorical_var] == groups[0]][numerical_var].dropna()
            group2_data = self.df[self.df[categorical_var] == groups[1]][numerical_var].dropna()
            
            t_stat, p_value = ttest_ind(group1_data, group2_data)
            cohens_d = self._calculate_cohens_d(group1_data, group2_data)
            
            return {
                "test_name": "Independent Samples T-Test",
                "test_type": "categorical_vs_numerical",
                "categorical_variable": categorical_var,
                "numerical_variable": numerical_var,
                "group_1": str(groups[0]),
                "group_2": str(groups[1]),
                "group_1_mean": round(group1_data.mean(), 4),
                "group_2_mean": round(group2_data.mean(), 4),
                "group_1_std": round(group1_data.std(), 4),
                "group_2_std": round(group2_data.std(), 4),
                "group_1_n": int(len(group1_data)),
                "group_2_n": int(len(group2_data)),
                "t_statistic": round(t_stat, 4),
                "p_value": round(p_value, 6),
                "cohens_d": round(cohens_d, 4),
                "interpretation": self._interpret_p_value(p_value),
                "effect_size_interpretation": self._interpret_cohens_d(cohens_d)
            }
        except Exception as e:
            return {"error": f"T-test failed: {str(e)}"}
    
    def anova_test(self, categorical_var: str, numerical_var: str) -> dict:
        """Perform One-Way ANOVA for categorical (3+ groups) vs numerical variable."""
        try:
            groups = self.df[categorical_var].unique()
            
            if len(groups) < 2:
                return {"error": "ANOVA requires at least 2 groups"}
            
            group_data = [
                self.df[self.df[categorical_var] == group][numerical_var].dropna()
                for group in groups
            ]
            
            f_stat, p_value = f_oneway(*group_data)
            eta_squared = self._calculate_eta_squared(group_data)
            
            group_stats = {
                str(group): {
                    "mean": round(data.mean(), 4),
                    "std": round(data.std(), 4),
                    "n": int(len(data))
                }
                for group, data in zip(groups, group_data)
            }
            
            return {
                "test_name": "One-Way ANOVA",
                "test_type": "categorical_vs_numerical",
                "categorical_variable": categorical_var,
                "numerical_variable": numerical_var,
                "num_groups": len(groups),
                "groups": [str(g) for g in groups],
                "f_statistic": round(f_stat, 4),
                "p_value": round(p_value, 6),
                "eta_squared": round(eta_squared, 4),
                "group_statistics": group_stats,
                "interpretation": self._interpret_p_value(p_value),
                "effect_size_interpretation": self._interpret_eta_squared(eta_squared)
            }
        except Exception as e:
            return {"error": f"ANOVA test failed: {str(e)}"}
    
    def pearson_correlation(self, var1: str, var2: str) -> dict:
        """Perform Pearson Correlation for two numerical variables."""
        try:
            clean_data = self.df[[var1, var2]].dropna()
            r, p_value = pearsonr(clean_data[var1], clean_data[var2])
            
            return {
                "test_name": "Pearson Correlation",
                "test_type": "numerical_vs_numerical",
                "variable_1": var1,
                "variable_2": var2,
                "correlation_coefficient": round(r, 4),
                "p_value": round(p_value, 6),
                "sample_size": int(len(clean_data)),
                "r_squared": round(r**2, 4),
                "interpretation": self._interpret_p_value(p_value),
                "correlation_strength": self._interpret_correlation(r),
                "direction": "positive" if r > 0 else "negative" if r < 0 else "none"
            }
        except Exception as e:
            return {"error": f"Pearson correlation failed: {str(e)}"}
    
    def spearman_correlation(self, var1: str, var2: str) -> dict:
        """Perform Spearman Correlation for two variables (ranked/ordinal)."""
        try:
            clean_data = self.df[[var1, var2]].dropna()
            rho, p_value = spearmanr(clean_data[var1], clean_data[var2])
            
            return {
                "test_name": "Spearman Correlation",
                "test_type": "numerical_vs_numerical (nonlinear/ordinal)",
                "variable_1": var1,
                "variable_2": var2,
                "spearman_rho": round(rho, 4),
                "p_value": round(p_value, 6),
                "sample_size": int(len(clean_data)),
                "interpretation": self._interpret_p_value(p_value),
                "correlation_strength": self._interpret_correlation(rho),
                "direction": "positive" if rho > 0 else "negative" if rho < 0 else "none"
            }
        except Exception as e:
            return {"error": f"Spearman correlation failed: {str(e)}"}
    
    def execute_hypothesis_test(self, hypothesis: dict) -> dict:
        """Execute the appropriate statistical test based on hypothesis variable types."""
        var1 = hypothesis.get('variable_1', '').lower()
        var2 = hypothesis.get('variable_2', '').lower()
        var1_type = hypothesis.get('variable_1_type', '')
        var2_type = hypothesis.get('variable_2_type', '')
        
        if var1 not in self.df.columns or var2 not in self.df.columns:
            return {
                "error": f"Variables not found in dataset. Available: {list(self.df.columns)}"
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
        
        if var1_type == "categorical" and var2_type == "categorical":
            results["statistical_results"] = self.chi_square_test(var1, var2)
        elif var1_type == "categorical" and var2_type == "numerical":
            num_groups = self.df[var1].nunique()
            results["statistical_results"] = self.t_test(var1, var2) if num_groups == 2 else self.anova_test(var1, var2)
        elif var1_type == "numerical" and var2_type == "categorical":
            num_groups = self.df[var2].nunique()
            results["statistical_results"] = self.t_test(var2, var1) if num_groups == 2 else self.anova_test(var2, var1)
        elif var1_type == "numerical" and var2_type == "numerical":
            results["statistical_results"] = {
                "pearson": self.pearson_correlation(var1, var2),
                "spearman": self.spearman_correlation(var1, var2)
            }
        
        return results
    
    def execute_all_hypotheses(self, hypotheses_result: dict) -> dict:
        """Execute statistical tests for all hypotheses."""
        if "error" in hypotheses_result:
            return {"error": hypotheses_result["error"]}
        
        hypotheses = hypotheses_result.get("hypotheses", [])
        
        if not hypotheses:
            return {"error": "No hypotheses to test"}
        
        all_results = {
            "summary": {
                "total_hypotheses": len(hypotheses),
                "dataset_shape": list(self.df.shape)
            },
            "hypothesis_results": []
        }
        
        for hypothesis in hypotheses:
            result = self.execute_hypothesis_test(hypothesis)
            all_results["hypothesis_results"].append(result)
        
        return all_results
    
    # Helper methods for effect size calculations and interpretations
    
    def _calculate_cohens_d(self, group1, group2):
        """Calculate Cohen's d effect size."""
        n1, n2 = len(group1), len(group2)
        var1, var2 = group1.var(), group2.var()
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        return (group1.mean() - group2.mean()) / pooled_std if pooled_std > 0 else 0
    
    def _calculate_eta_squared(self, group_data):
        """Calculate eta squared effect size for ANOVA."""
        all_data = np.concatenate(group_data)
        grand_mean = all_data.mean()
        ss_between = sum(len(group) * (group.mean() - grand_mean)**2 for group in group_data)
        ss_total = sum((all_data - grand_mean)**2)
        return ss_between / ss_total if ss_total > 0 else 0
    
    def _interpret_p_value(self, p_value, alpha=0.05):
        """Interpret p-value significance."""
        if p_value < 0.001:
            return f"Highly significant (p < 0.001) - Strong evidence against null hypothesis"
        elif p_value < 0.01:
            return f"Very significant (p < 0.01) - Strong evidence against null hypothesis"
        elif p_value < alpha:
            return f"Significant (p < {alpha}) - Reject null hypothesis"
        else:
            return f"Not significant (p >= {alpha}) - Fail to reject null hypothesis"
    
    def _interpret_cohens_d(self, d):
        """Interpret Cohen's d effect size."""
        abs_d = abs(d)
        if abs_d < 0.2:
            return "Negligible effect"
        elif abs_d < 0.5:
            return "Small effect"
        elif abs_d < 0.8:
            return "Medium effect"
        else:
            return "Large effect"
    
    def _interpret_eta_squared(self, eta_sq):
        """Interpret eta squared effect size."""
        if eta_sq < 0.01:
            return "Negligible effect"
        elif eta_sq < 0.06:
            return "Small effect"
        elif eta_sq < 0.14:
            return "Medium effect"
        else:
            return "Large effect"
    
    def _interpret_cramers_v(self, v):
        """Interpret Cramér's V effect size."""
        if v < 0.1:
            return "Negligible association"
        elif v < 0.3:
            return "Weak association"
        elif v < 0.5:
            return "Moderate association"
        else:
            return "Strong association"
    
    def _interpret_correlation(self, r):
        """Interpret correlation coefficient strength."""
        abs_r = abs(r)
        if abs_r < 0.1:
            return "Negligible correlation"
        elif abs_r < 0.3:
            return "Weak correlation"
        elif abs_r < 0.5:
            return "Moderate correlation"
        elif abs_r < 0.7:
            return "Strong correlation"
        else:
            return "Very strong correlation"


# ═══════════════════════════════════════════════════════════
# DATABASE HELPER
# ═══════════════════════════════════════════════════════════

def load_hr_data() -> pd.DataFrame:
    """
    Load HR employee attrition data from PostgreSQL.
    
    Returns:
        pandas DataFrame with employee data
    """
    # Build PostgreSQL connection URL
    encoded_pw = quote_plus(os.getenv("DB_PASSWORD"))
    postgres_url = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{encoded_pw}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    
    # Create database engine
    engine = create_engine(postgres_url)
    
    # Load data
    schema_name = os.getenv('DB_SCHEMA', 'public')
    query = f'SELECT * FROM {schema_name}.employee_attrition'
    df = pd.read_sql_query(query, engine)
    
    # Normalize column names to lowercase
    df.columns = df.columns.str.lower()
    
    return df
