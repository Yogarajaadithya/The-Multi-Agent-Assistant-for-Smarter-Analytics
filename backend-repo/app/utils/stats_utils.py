"""
Statistical Testing Agent Utility Functions
============================================
Helper functions for statistical tests, effect size calculations, and interpretations.

Author: Yogarajaadithya
Date: November 19, 2025
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, List
from scipy.stats import chi2_contingency, pearsonr, spearmanr, f_oneway, ttest_ind
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)


def load_hr_data() -> pd.DataFrame:
    """
    Load HR employee attrition data from PostgreSQL database.
    Deprecated: Use load_dataset_data() instead for multi-dataset support.
    
    Returns:
        pandas.DataFrame: Employee data with normalized lowercase column names
    
    Example:
        >>> df = load_hr_data()
        >>> print(df.columns[:5])
        Index(['age', 'attrition', 'businesstravel', ...], dtype='object')
    """
    from app.services.dataset_manager import get_dataset_manager
    return load_dataset_data(get_dataset_manager())


def load_dataset_data(dataset_manager) -> pd.DataFrame:
    """
    Load data from the currently selected dataset in PostgreSQL database.
    
    Args:
        dataset_manager: DatasetManager instance to get current dataset info
    
    Returns:
        pandas.DataFrame: Dataset with normalized lowercase column names
    
    Example:
        >>> from app.services.dataset_manager import get_dataset_manager
        >>> df = load_dataset_data(get_dataset_manager())
        >>> print(df.shape)
    """
    encoded_pw = quote_plus(os.getenv("DB_PASSWORD"))
    postgres_url = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{encoded_pw}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    
    engine = create_engine(postgres_url)
    
    # Get current dataset info from dataset_manager
    current_dataset = dataset_manager.get_current_dataset()
    schema_name = current_dataset.schema_name
    table_name = current_dataset.main_table
    
    query = f'SELECT * FROM {schema_name}.{table_name}'
    df = pd.read_sql_query(query, engine)
    
    # Normalize column names to lowercase
    df.columns = df.columns.str.lower()
    
    engine.dispose()
    
    return df


def chi_square_test(df: pd.DataFrame, var1: str, var2: str) -> Dict:
    """
    Perform Chi-Square test for two categorical variables.
    
    Tests independence between two categorical variables using chi-square test
    and calculates Cramér's V effect size.
    
    Args:
        df (pandas.DataFrame): Dataset containing the variables
        var1 (str): First categorical variable name
        var2 (str): Second categorical variable name
    
    Returns:
        dict: Test results with chi2 statistic, p-value, degrees of freedom,
              Cramér's V, and interpretations
    
    Example:
        >>> result = chi_square_test(df, 'gender', 'attrition')
        >>> print(result['p_value'])
    """
    try:
        contingency_table = pd.crosstab(df[var1], df[var2])
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
            "interpretation": interpret_p_value(p_value),
            "effect_size_interpretation": interpret_cramers_v(cramers_v)
        }
    except Exception as e:
        return {"error": f"Chi-square test failed: {str(e)}"}


def t_test(df: pd.DataFrame, categorical_var: str, numerical_var: str) -> Dict:
    """
    Perform Independent Samples T-Test for categorical (2 groups) vs numerical variable.
    
    Compares means between two groups and calculates Cohen's d effect size.
    
    Args:
        df (pandas.DataFrame): Dataset containing the variables
        categorical_var (str): Categorical variable with exactly 2 groups
        numerical_var (str): Numerical variable to compare
    
    Returns:
        dict: Test results with t-statistic, p-value, group means/stds,
              Cohen's d, and interpretations
    
    Example:
        >>> result = t_test(df, 'attrition', 'age')
        >>> print(result['cohens_d'])
    """
    try:
        groups = df[categorical_var].unique()
        
        if len(groups) != 2:
            return {"error": f"T-test requires exactly 2 groups, found {len(groups)}. Use ANOVA instead."}
        
        group1_data = df[df[categorical_var] == groups[0]][numerical_var].dropna()
        group2_data = df[df[categorical_var] == groups[1]][numerical_var].dropna()
        
        t_stat, p_value = ttest_ind(group1_data, group2_data)
        cohens_d = calculate_cohens_d(group1_data, group2_data)
        
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
            "interpretation": interpret_p_value(p_value),
            "effect_size_interpretation": interpret_cohens_d(cohens_d)
        }
    except Exception as e:
        return {"error": f"T-test failed: {str(e)}"}


def anova_test(df: pd.DataFrame, categorical_var: str, numerical_var: str) -> Dict:
    """
    Perform One-Way ANOVA for categorical (3+ groups) vs numerical variable.
    
    Compares means across multiple groups and calculates eta squared effect size.
    
    Args:
        df (pandas.DataFrame): Dataset containing the variables
        categorical_var (str): Categorical variable with 2+ groups
        numerical_var (str): Numerical variable to compare
    
    Returns:
        dict: Test results with F-statistic, p-value, group statistics,
              eta squared, and interpretations
    
    Example:
        >>> result = anova_test(df, 'department', 'monthlyincome')
        >>> print(result['eta_squared'])
    """
    try:
        groups = df[categorical_var].unique()
        
        if len(groups) < 2:
            return {"error": "ANOVA requires at least 2 groups"}
        
        group_data = [
            df[df[categorical_var] == group][numerical_var].dropna()
            for group in groups
        ]
        
        f_stat, p_value = f_oneway(*group_data)
        eta_squared = calculate_eta_squared(group_data)
        
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
            "interpretation": interpret_p_value(p_value),
            "effect_size_interpretation": interpret_eta_squared(eta_squared)
        }
    except Exception as e:
        return {"error": f"ANOVA test failed: {str(e)}"}


def pearson_correlation(df: pd.DataFrame, var1: str, var2: str) -> Dict:
    """
    Perform Pearson Correlation for two numerical variables.
    
    Tests linear relationship between two continuous variables.
    
    Args:
        df (pandas.DataFrame): Dataset containing the variables
        var1 (str): First numerical variable name
        var2 (str): Second numerical variable name
    
    Returns:
        dict: Test results with correlation coefficient, p-value, R-squared,
              and interpretations
    
    Example:
        >>> result = pearson_correlation(df, 'age', 'monthlyincome')
        >>> print(result['correlation_coefficient'])
    """
    try:
        clean_data = df[[var1, var2]].dropna()
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
            "interpretation": interpret_p_value(p_value),
            "correlation_strength": interpret_correlation(r),
            "direction": "positive" if r > 0 else "negative" if r < 0 else "none"
        }
    except Exception as e:
        return {"error": f"Pearson correlation failed: {str(e)}"}


def spearman_correlation(df: pd.DataFrame, var1: str, var2: str) -> Dict:
    """
    Perform Spearman Correlation for two variables (ranked/ordinal).
    
    Tests monotonic relationship between two variables using ranks.
    
    Args:
        df (pandas.DataFrame): Dataset containing the variables
        var1 (str): First variable name
        var2 (str): Second variable name
    
    Returns:
        dict: Test results with Spearman's rho, p-value, and interpretations
    
    Example:
        >>> result = spearman_correlation(df, 'joblevel', 'jobsatisfaction')
        >>> print(result['spearman_rho'])
    """
    try:
        clean_data = df[[var1, var2]].dropna()
        rho, p_value = spearmanr(clean_data[var1], clean_data[var2])
        
        return {
            "test_name": "Spearman Correlation",
            "test_type": "numerical_vs_numerical (nonlinear/ordinal)",
            "variable_1": var1,
            "variable_2": var2,
            "spearman_rho": round(rho, 4),
            "p_value": round(p_value, 6),
            "sample_size": int(len(clean_data)),
            "interpretation": interpret_p_value(p_value),
            "correlation_strength": interpret_correlation(rho),
            "direction": "positive" if rho > 0 else "negative" if rho < 0 else "none"
        }
    except Exception as e:
        return {"error": f"Spearman correlation failed: {str(e)}"}


# Effect size calculation functions

def calculate_cohens_d(group1: pd.Series, group2: pd.Series) -> float:
    """
    Calculate Cohen's d effect size for two groups.
    
    Measures standardized difference between two group means.
    
    Args:
        group1 (pandas.Series): First group data
        group2 (pandas.Series): Second group data
    
    Returns:
        float: Cohen's d effect size
    
    Example:
        >>> cohens_d = calculate_cohens_d(group1, group2)
        >>> print(f"Effect size: {cohens_d:.4f}")
    """
    n1, n2 = len(group1), len(group2)
    var1, var2 = group1.var(), group2.var()
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    return (group1.mean() - group2.mean()) / pooled_std if pooled_std > 0 else 0


def calculate_eta_squared(group_data: List[pd.Series]) -> float:
    """
    Calculate eta squared effect size for ANOVA.
    
    Measures proportion of variance explained by group differences.
    
    Args:
        group_data (list): List of pandas Series for each group
    
    Returns:
        float: Eta squared effect size
    
    Example:
        >>> groups = [df[df['dept']=='Sales']['income'], ...]
        >>> eta_sq = calculate_eta_squared(groups)
        >>> print(f"Variance explained: {eta_sq:.4f}")
    """
    all_data = np.concatenate(group_data)
    grand_mean = all_data.mean()
    ss_between = sum(len(group) * (group.mean() - grand_mean)**2 for group in group_data)
    ss_total = sum((all_data - grand_mean)**2)
    return ss_between / ss_total if ss_total > 0 else 0


# Interpretation functions

def interpret_p_value(p_value: float, alpha: float = 0.05) -> str:
    """
    Interpret p-value significance with standard thresholds.
    
    Args:
        p_value (float): P-value from statistical test
        alpha (float): Significance level (default: 0.05)
    
    Returns:
        str: Human-readable interpretation
    
    Example:
        >>> print(interpret_p_value(0.0001))
        'Highly significant (p < 0.001) - Strong evidence against null hypothesis'
    """
    if p_value < 0.001:
        return "Highly significant (p < 0.001) - Strong evidence against null hypothesis"
    elif p_value < 0.01:
        return "Very significant (p < 0.01) - Strong evidence against null hypothesis"
    elif p_value < alpha:
        return f"Significant (p < {alpha}) - Reject null hypothesis"
    else:
        return f"Not significant (p >= {alpha}) - Fail to reject null hypothesis"


def interpret_cohens_d(d: float) -> str:
    """
    Interpret Cohen's d effect size magnitude.
    
    Args:
        d (float): Cohen's d effect size
    
    Returns:
        str: Effect size interpretation
    
    Example:
        >>> print(interpret_cohens_d(0.6))
        'Medium effect'
    """
    abs_d = abs(d)
    if abs_d < 0.2:
        return "Negligible effect"
    elif abs_d < 0.5:
        return "Small effect"
    elif abs_d < 0.8:
        return "Medium effect"
    else:
        return "Large effect"


def interpret_eta_squared(eta_sq: float) -> str:
    """
    Interpret eta squared effect size magnitude.
    
    Args:
        eta_sq (float): Eta squared effect size
    
    Returns:
        str: Effect size interpretation
    
    Example:
        >>> print(interpret_eta_squared(0.10))
        'Medium effect'
    """
    if eta_sq < 0.01:
        return "Negligible effect"
    elif eta_sq < 0.06:
        return "Small effect"
    elif eta_sq < 0.14:
        return "Medium effect"
    else:
        return "Large effect"


def interpret_cramers_v(v: float) -> str:
    """
    Interpret Cramér's V effect size magnitude.
    
    Args:
        v (float): Cramér's V effect size
    
    Returns:
        str: Association strength interpretation
    
    Example:
        >>> print(interpret_cramers_v(0.35))
        'Moderate association'
    """
    if v < 0.1:
        return "Negligible association"
    elif v < 0.3:
        return "Weak association"
    elif v < 0.5:
        return "Moderate association"
    else:
        return "Strong association"


def interpret_correlation(r: float) -> str:
    """
    Interpret correlation coefficient strength.
    
    Args:
        r (float): Correlation coefficient (Pearson or Spearman)
    
    Returns:
        str: Correlation strength interpretation
    
    Example:
        >>> print(interpret_correlation(0.65))
        'Strong correlation'
    """
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
