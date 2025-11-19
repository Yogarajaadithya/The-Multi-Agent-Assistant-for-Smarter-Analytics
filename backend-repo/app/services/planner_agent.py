"""
Planner Agent for Multi-Agent Analytics System
==================================================
Routes user questions to appropriate agents based on question type (WHAT vs WHY).

Author: Yogarajaadithya
Date: October 31, 2025
"""

import json
import re
from typing import Dict, Any
from langchain_core.prompts import PromptTemplate

from app.prompts.prompts import planner_agent_prompt


async def planner_agent(user_query: str, llm) -> Dict[str, Any]:
    """
    Planner Agent - Analyzes user questions and routes to appropriate agents.
    
    Determines the analytical approach for analytics questions by classifying
    them as either descriptive (WHAT) or causal (WHY) questions.
    
    Args:
        user_query (str): The user's question or prompt
        llm: The language model instance (from llm.py)
    
    Returns:
        dict: The generated plan as a Python dictionary containing:
            - question_type: 'WHAT' or 'WHY'
            - reasoning: Explanation of classification
            - agents_to_call: List of agents to invoke
            - analysis_approach: Description of analytical approach
    
    Example:
        >>> from app.services.llm import get_lm_client
        >>> from langchain_openai import ChatOpenAI
        >>> 
        >>> async_client = get_lm_client()
        >>> llm = ChatOpenAI(
        ...     api_key="lm-studio",
        ...     base_url="http://localhost:1234/v1",
        ...     model="local-model"
        ... )
        >>> plan = await planner_agent(
        ...     "What is the attrition rate by department?", 
        ...     llm
        ... )
        >>> print(plan['question_type'])
        'WHAT'
    """
    try:
        # Create a prompt from the template
        planner_prompt = PromptTemplate.from_template(planner_agent_prompt)
        
        # Create chain using pipe operator
        chain = planner_prompt | llm
        
        # Run the chain to generate the plan
        response = await chain.ainvoke({"user_query": user_query})
        generated_plan = response.content if hasattr(response, 'content') else str(response)
        
        # Remove code block markers if present in the output
        if "```json" in generated_plan:
            plan_data = generated_plan.replace("```json", "").replace("```", "")
        else:
            plan_data = generated_plan
        
        # Remove any thinking tags if present
        plan_data = re.sub(r'<think>.*?</think>', '', plan_data, flags=re.DOTALL | re.IGNORECASE)
        
        # Parse the generated plan JSON string into a Python dictionary
        analysis_plan = json.loads(plan_data.strip())
        
        return analysis_plan
    
    except json.JSONDecodeError as err:
        print(f"Error parsing JSON from LLM response: {err}")
        print(f"Raw response: {generated_plan}")
        # Return default plan on error
        return {
            "question_type": "WHAT",
            "reasoning": "Failed to parse LLM response, defaulting to descriptive analysis",
            "agents_to_call": ["text_to_sql", "visualization"],
            "analysis_approach": "Descriptive analysis with data retrieval and visualization"
        }
    except Exception as err:
        print(f"Error in planner_agent: {err}")
        raise err
