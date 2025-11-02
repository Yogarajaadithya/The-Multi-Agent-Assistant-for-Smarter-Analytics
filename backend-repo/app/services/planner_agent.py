"""
Planner Agent for Multi-Agent HR Analytics System
==================================================
Routes user questions to appropriate agents based on question type (WHAT vs WHY).

Author: Yogarajaadithya
Date: October 31, 2025
"""

import json
import re
from typing import Dict, Any, Literal
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# HR Analytics Domain Context
HR_CONTEXT = """
DOMAIN: HR Employee Attrition Analytics

================================================================================
AVAILABLE DATA FIELDS (hr_employee_attrition table):
================================================================================

DEMOGRAPHIC INFORMATION:
- age: Employee's age in years (int)
- gender: Employee's gender (Male/Female) - used for diversity analysis
- maritalstatus: Marital status (Single/Married/Divorced) - affects work-life balance
- education: Education level (1-5 scale)
- educationfield: Field of study (Life Sciences, Medical, Marketing, Technical, Other)

JOB INFORMATION:
- department: Department (Sales, Research & Development, Human Resources)
- jobrole: Specific job title (Sales Executive, Research Scientist, Manager, etc.)
- joblevel: Position level within organization (1-5)
- monthlyincome: Monthly salary
- dailyrate: Daily salary rate
- hourlyrate: Hourly wage rate
- monthlyrate: Monthly billing rate
- percentsalaryhike: Percentage increase in salary

WORK-LIFE FACTORS:
- overtime: Works overtime (Yes/No) - impacts performance and attrition
- businesstravel: Frequency of travel (Non-Travel, Travel_Rarely, Travel_Frequently)
- distancefromhome: Distance between home and workplace
- worklifebalance: Work-life balance rating (1-4 scale)

SATISFACTION METRICS:
- jobsatisfaction: Job satisfaction level (1-4 scale)
- environmentsatisfaction: Satisfaction with work environment (1-4 scale)
- relationshipsatisfaction: Satisfaction with workplace relationships (1-4 scale)
- jobinvolvement: Level of job involvement (1-4 scale)

CAREER PROGRESSION:
- yearsatcompany: Years spent at the company - employee tenure
- yearsincurrentrole: Years spent in current role - role stability
- yearssincelastpromotion: Years since last promotion - promotion trends
- yearswithcurrmanager: Years with current manager - manager relationships
- totalworkingyears: Total work experience
- numcompaniesworked: Number of previous companies - career mobility
- trainingtimeslastyear: Training sessions attended last year

PERFORMANCE & COMPENSATION:
- performancerating: Employee performance rating (1-4 scale)
- stockoptionlevel: Stock option level (0-3)

TARGET VARIABLE:
- attrition: Whether employee left the company (Yes/No) - PRIMARY OUTCOME

================================================================================
KEY HR METRICS & KPIs:
================================================================================

1. Attrition Rate = (Employees who left / Total employees) * 100%
2. Turnover Rate = (Total separations / Average employees) * 100%
3. Average Tenure = Sum of tenures / Total employees
4. Gender Pay Gap = ((Avg Male Salary - Avg Female Salary) / Avg Male Salary) * 100%
5. Overtime Work Rate = (Overtime hours / Total hours) * 100%
6. Promotion Rate = (Number of promotions / Total employees) * 100%

================================================================================
ANALYSIS CAPABILITIES:
================================================================================

1. DESCRIPTIVE ANALYTICS (WHAT Questions):
   - Counts, sums, averages, distributions
   - Group-by analysis (by department, role, gender, etc.)
   - Cross-tabulations and comparisons
   - Trend analysis over time
   - KPI calculations (attrition rate, average salary, etc.)

2. CAUSAL ANALYTICS (WHY Questions):
   - Hypothesis generation and testing
   - Statistical significance testing (t-tests, chi-square, ANOVA)
   - Correlation and relationship analysis
   - Impact analysis (effect of overtime, satisfaction, etc.)
   - Root cause analysis for attrition

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


class PlannerAgent:
    """
    Planner Agent for Multi-Agent HR Analytics System.
    
    Analyzes user questions and routes to appropriate agents:
    - WHAT questions → Text-to-SQL + Visualization
    - WHY questions → Hypothesis + Statistical Testing
    """
    
    def __init__(self, llm: ChatOpenAI):
        """
        Initialize the Planner Agent.
        
        Args:
            llm: LangChain ChatOpenAI instance
        """
        self.llm = llm
        self._setup_prompt()
    
    def _setup_prompt(self):
        """Setup the planning prompt for question classification."""
        self.prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an EXPERT HR Analytics Planner Agent. Your job is to analyze user questions and "
             "determine the appropriate analytical approach.\n\n"
             
             "═══════════════════════════════════════════════════════════\n"
             "CRITICAL TASK:\n"
             "═══════════════════════════════════════════════════════════\n"
             "Analyze the user's question and classify it into ONE of two categories:\n\n"
             
             "1. **WHAT Questions** (Descriptive Analytics):\n"
             "   - Asking for FACTS, COUNTS, AVERAGES, DISTRIBUTIONS\n"
             "   - Examples:\n"
             "     * \"What is the attrition rate?\"\n"
             "     * \"How many employees are in each department?\"\n"
             "     * \"What is the average salary by job role?\"\n"
             "     * \"Show me the distribution of overtime workers\"\n"
             "     * \"Compare attrition rates between departments\"\n"
             "   - Keywords: what, how many, show, list, compare, distribution, average, count\n"
             "   - **Route to:** Text-to-SQL Agent (EDA) + Visualization Agent\n\n"
             
             "2. **WHY Questions** (Causal Analytics):\n"
             "   - Asking for REASONS, CAUSES, EXPLANATIONS, RELATIONSHIPS\n"
             "   - Examples:\n"
             "     * \"Why do employees leave?\"\n"
             "     * \"What causes high attrition?\"\n"
             "     * \"Does overtime affect attrition?\"\n"
             "     * \"Is there a relationship between satisfaction and turnover?\"\n"
             "     * \"Why do male employees have higher attrition?\"\n"
             "   - Keywords: why, cause, reason, affect, impact, relationship, correlation, influence\n"
             "   - **Route to:** Hypothesis Agent + Statistical Testing Agent\n\n"
             
             "═══════════════════════════════════════════════════════════\n"
             "CLASSIFICATION RULES:\n"
             "═══════════════════════════════════════════════════════════\n"
             "1. If the question asks \"WHAT is/are\", \"HOW MANY\", \"SHOW ME\" → WHAT\n"
             "2. If the question asks \"WHY\", \"WHAT CAUSES\", \"DOES X AFFECT Y\" → WHY\n"
             "3. If the question asks for COMPARISON without causation → WHAT\n"
             "4. If the question asks about IMPACT or RELATIONSHIP → WHY\n"
             "5. If the question mentions HYPOTHESIS or TESTING → WHY\n"
             "6. If unclear, default to WHAT (descriptive is safer)\n\n"
             
             "═══════════════════════════════════════════════════════════\n"
             "OUTPUT FORMAT (JSON):\n"
             "═══════════════════════════════════════════════════════════\n"
             "Return ONLY a valid JSON object with this EXACT structure:\n"
             "{{\n"
             "  \"question_type\": \"WHAT\" or \"WHY\",\n"
             "  \"reasoning\": \"Brief explanation of why you classified it this way\",\n"
             "  \"agents_to_call\": [\"list\", \"of\", \"agents\"],\n"
             "  \"analysis_approach\": \"Short description of the analytical approach\"\n"
             "}}\n\n"
             
             "Agents available:\n"
             "- \"text_to_sql\" (EDA - retrieves data)\n"
             "- \"visualization\" (creates charts)\n"
             "- \"hypothesis\" (generates testable hypotheses)\n"
             "- \"statistical_testing\" (performs statistical tests)\n\n"
             
             "═══════════════════════════════════════════════════════════\n"
             "HR ANALYTICS CONTEXT:\n"
             "═══════════════════════════════════════════════════════════\n"
             "{hr_context}\n\n"
             
             "═══════════════════════════════════════════════════════════\n"
             "REMEMBER:\n"
             "═══════════════════════════════════════════════════════════\n"
             "- Return ONLY valid JSON\n"
             "- No markdown code blocks\n"
             "- No explanations outside the JSON\n"
             "- Be decisive - choose WHAT or WHY\n"
             "═══════════════════════════════════════════════════════════\n"),
            ("user",
             "Analyze this question and provide the routing decision:\n\n"
             "Question: {question}\n\n"
             "Return your analysis as JSON.")
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Try to extract from ```json ... ``` blocks
        json_block = re.search(r"```json\s*(.*?)```", response, re.IGNORECASE | re.DOTALL)
        if json_block:
            json_str = json_block.group(1)
        else:
            # Try generic ``` ... ``` blocks
            code_block = re.search(r"```\s*(.*?)```", response, re.DOTALL)
            json_str = code_block.group(1) if code_block else response
        
        # Remove thinking tags if present
        json_str = re.sub(r'<think>.*?</think>', '', json_str, flags=re.DOTALL | re.IGNORECASE)
        
        # Parse JSON
        try:
            return json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}\n\nResponse: {response}")
    
    def analyze_question(self, question: str) -> Dict[str, Any]:
        """
        Analyze user question and determine routing.
        
        Args:
            question: User's natural language question
            
        Returns:
            Dictionary with routing decision:
            {
                'question_type': 'WHAT' or 'WHY',
                'reasoning': 'explanation',
                'agents_to_call': ['agent1', 'agent2'],
                'analysis_approach': 'description'
            }
        """
        # Get LLM response
        response = self.chain.invoke({
            "hr_context": HR_CONTEXT,
            "question": question
        })
        
        # Parse JSON
        decision = self._parse_json_response(response)
        
        return decision
    
    def route_question(self, question: str) -> Literal["WHAT", "WHY"]:
        """
        Simple routing function that returns the question type.
        
        Args:
            question: User's question
            
        Returns:
            'WHAT' or 'WHY'
        """
        decision = self.analyze_question(question)
        return decision.get('question_type', 'WHAT')
