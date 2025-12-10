"""
Multi-Agent Analytics System
================================
Integrates Planner, Text-to-SQL, Visualization, Hypothesis, and Stats agents.

Author: Yogarajaadithya
Date: November 19, 2025
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

from app.services.planner_agent import planner_agent
from app.services.text_to_sql_agent import text_to_sql_agent, get_database_connection
from app.services.visualization_agent import visualization_agent
from app.services.hypothesis_agent import hypothesis_agent
from app.services.stats_agent import stats_agent


async def process_question(
    question: str,
    llm: AzureChatOpenAI = None,
    num_hypotheses: int = 3,
    include_viz: bool = True,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Process user question with intelligent routing through multi-agent system.
    
    Routes questions to appropriate agents based on question type:
    - WHAT questions → Text-to-SQL + Visualization
    - WHY questions → Text-to-SQL + Visualization + Hypothesis + Statistical Testing
    
    Args:
        question (str): User's natural language question
        llm: Language model instance (creates new if None)
        num_hypotheses (int): Number of hypotheses to generate for WHY questions
        include_viz (bool): Whether to generate visualizations
        verbose (bool): Print detailed logs
    
    Returns:
        dict: Results based on question type
    """
    try:
        # Initialize LLM if not provided
        if llm is None:
            llm = initialize_llm()
        
        # Step 1: Analyze question with Planner Agent
        if verbose:
            print(f"\n{'='*70}")
            print("PLANNER AGENT ANALYSIS")
            print(f"{'='*70}")
        
        planner_decision = await planner_agent(question, llm)
        question_type = planner_decision.get('question_type', 'WHAT')
        agents_to_call = planner_decision.get('agents_to_call', [])
        
        if verbose:
            print(f"\nQuestion: {question}")
            print(f"Type: {question_type}")
            print(f"Reasoning: {planner_decision.get('reasoning')}")
            print(f"Agents: {', '.join(agents_to_call)}")
            print(f"\n{'-'*70}\n")
        
        # Step 2: Route to appropriate agents based on planner decision
        if question_type == 'WHAT':
            return await _handle_what_question(
                question, llm, include_viz, verbose, planner_decision
            )
        else:  # WHY question
            return await _handle_why_question(
                question, llm, num_hypotheses, include_viz, verbose, planner_decision
            )
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Multi-agent processing failed: {str(e)}",
            "question": question
        }


async def _handle_what_question(
    question: str,
    llm: AzureChatOpenAI,
    include_viz: bool,
    verbose: bool,
    planner_decision: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle WHAT questions (Descriptive Analytics)."""
    if verbose:
        print("[INFO] Routing to TEXT-TO-SQL + VISUALIZATION AGENTS")
        print(f"{'-'*70}\n")
    
    try:
        # Get database connection
        db = get_database_connection()
        
        # Step 1: Generate and execute SQL
        if verbose:
            print("[INFO] Generating SQL query...")
        
        sql_result = await text_to_sql_agent(question, llm, db)
        
        if not sql_result.get("success", False):
            return {
                "success": False,
                "question": question,
                "question_type": "WHAT",
                "planner_decision": planner_decision,
                "sql": None,
                "data": None,
                "visualization": None,
                "error": sql_result.get("error")
            }
        
        if verbose:
            print(f"[SUCCESS] SQL: {sql_result['sql']}")
            print(f"[INFO] Retrieved {sql_result['rows']} rows\n")
        
        # Step 2: Generate visualization
        viz_result = None
        if include_viz and sql_result["data"] is not None and len(sql_result["data"]) > 0:
            if verbose:
                print("[INFO] Generating visualization...")
            
            viz_result = await visualization_agent(
                sql_result["data"],
                llm,
                original_question=question
            )
            
            if verbose:
                if viz_result.get("success"):
                    print("[SUCCESS] Visualization generated successfully")
                    print("\n" + "="*70)
                    print("VISUALIZATION CODE")
                    print("="*70)
                    print(viz_result.get("code", "No code available"))
                    print("="*70 + "\n")
                else:
                    print("[WARNING] Visualization generation failed\n")
        
        return {
            "success": True,
            "question": question,
            "question_type": "WHAT",
            "analysis_type": "descriptive_analytics",
            "planner_decision": planner_decision,
            "sql": sql_result["sql"],
            "data": sql_result["data"],
            "rows": sql_result["rows"],
            "columns": sql_result["columns"],
            "visualization": viz_result,
            "error": None
        }
    
    except Exception as e:
        return {
            "success": False,
            "question": question,
            "question_type": "WHAT",
            "error": f"WHAT question processing failed: {str(e)}",
            "planner_decision": planner_decision
        }


async def _handle_why_question(
    question: str,
    llm: AzureChatOpenAI,
    num_hypotheses: int,
    include_viz: bool,
    verbose: bool,
    planner_decision: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle WHY questions (Causal Analytics)."""
    if verbose:
        print("[INFO] Routing to HYPOTHESIS + TEXT-TO-SQL + VISUALIZATION + STATS AGENTS")
        print(f"{'-'*70}\n")
    
    try:
        db = get_database_connection()
        
        # Step 1: Generate hypotheses FIRST
        if verbose:
            print(f"[INFO] Generating {num_hypotheses} hypotheses...")
        
        hypotheses_result = await hypothesis_agent(question, llm, num_hypotheses)
        
        if "error" in hypotheses_result:
            return {
                "success": False,
                "question": question,
                "question_type": "WHY",
                "error": f"Hypothesis generation failed: {hypotheses_result['error']}",
                "planner_decision": planner_decision,
                "hypotheses": hypotheses_result,
                "sql_queries": [],
                "visualizations": [],
                "statistical_results": None
            }
        
        hypotheses = hypotheses_result.get('hypotheses', [])
        num_generated = len(hypotheses)
        
        if verbose:
            print(f"[SUCCESS] Generated {num_generated} hypotheses")
            for i, hyp in enumerate(hypotheses, 1):
                print(f"  Hypothesis {i}: {hyp.get('alternative_hypothesis', 'N/A')}")
            print()
        
        # Step 2: Generate SQL queries for each hypothesis
        sql_queries = []
        hypothesis_data = []
        
        if verbose:
            print(f"[INFO] Generating SQL queries for {num_generated} hypotheses...")
        
        for i, hypothesis in enumerate(hypotheses, 1):
            var1 = hypothesis.get('variable_1', '')
            var2 = hypothesis.get('variable_2', '')
            
            # Create a targeted question for this specific hypothesis
            hypothesis_question = f"Show the relationship between {var1} and {var2}"
            
            if verbose:
                print(f"  [{i}/{num_generated}] Query for: {var1} vs {var2}")
            
            sql_result = await text_to_sql_agent(hypothesis_question, llm, db)
            
            if sql_result.get("success"):
                sql_queries.append({
                    "hypothesis_id": hypothesis.get('hypothesis_id'),
                    "sql": sql_result.get("sql"),
                    "data": sql_result.get("data"),
                    "rows": sql_result.get("rows", 0),
                    "columns": sql_result.get("columns", [])
                })
                hypothesis_data.append(sql_result.get("data"))
                
                if verbose:
                    print(f"    [SUCCESS] Retrieved {sql_result.get('rows', 0)} rows")
            else:
                sql_queries.append({
                    "hypothesis_id": hypothesis.get('hypothesis_id'),
                    "sql": None,
                    "data": None,
                    "rows": 0,
                    "columns": [],
                    "error": sql_result.get("error")
                })
                hypothesis_data.append(None)
                
                if verbose:
                    print(f"    [WARNING] SQL generation failed: {sql_result.get('error')}")
        
        if verbose:
            print()
        
        # Step 3: Generate visualizations for each hypothesis
        visualizations = []
        
        if include_viz:
            if verbose:
                print(f"[INFO] Generating visualizations for {num_generated} hypotheses...")
            
            for i, (hypothesis, data) in enumerate(zip(hypotheses, hypothesis_data), 1):
                if data is not None and not data.empty:
                    var1 = hypothesis.get('variable_1', '')
                    var2 = hypothesis.get('variable_2', '')
                    viz_question = f"Visualize the relationship between {var1} and {var2}"
                    
                    if verbose:
                        print(f"  [{i}/{num_generated}] Visualization for: {var1} vs {var2}")
                    
                    viz_result = await visualization_agent(data, llm, viz_question)
                    
                    visualizations.append({
                        "hypothesis_id": hypothesis.get('hypothesis_id'),
                        "success": viz_result.get("success"),
                        "code": viz_result.get("code"),
                        "figure": viz_result.get("figure"),
                        "error": viz_result.get("error")
                    })
                    
                    if verbose:
                        if viz_result.get("success"):
                            print("    [SUCCESS] Visualization generated")
                            print("\n" + "="*70)
                            print(f"VISUALIZATION CODE - Hypothesis {i}")
                            print("="*70)
                            print(viz_result.get("code", "No code available"))
                            print("="*70 + "\n")
                        else:
                            print(f"    [WARNING] Visualization failed: {viz_result.get('error')}")
                else:
                    visualizations.append({
                        "hypothesis_id": hypothesis.get('hypothesis_id'),
                        "success": False,
                        "code": None,
                        "figure": None,
                        "error": "No data available for visualization"
                    })
                    
                    if verbose:
                        print(f"  [{i}/{num_generated}] [WARNING] No data for visualization")
            
            if verbose:
                print()
        
        # Step 4: Run statistical tests on all hypotheses
        if verbose:
            print("[INFO] Running statistical tests...")
        
        stats_result = await stats_agent(hypotheses_result)
        
        if "error" in stats_result:
            if verbose:
                print(f"[WARNING] Statistical testing failed: {stats_result['error']}\n")
        else:
            if verbose:
                print(f"[SUCCESS] Completed {stats_result['summary']['total_hypotheses']} statistical tests\n")
        
        # Return combined results with all visualizations
        return {
            "success": True,
            "question": question,
            "question_type": "WHY",
            "analysis_type": "causal_analytics",
            "planner_decision": planner_decision,
            "hypotheses": hypotheses_result,
            "sql_queries": sql_queries,
            "visualizations": visualizations,
            "statistical_results": stats_result,
            "summary": {
                "total_hypotheses": num_generated,
                "sql_queries_generated": len([q for q in sql_queries if q.get("sql")]),
                "visualizations_generated": len([v for v in visualizations if v.get("success")]),
                "tests_completed": stats_result.get('summary', {}).get('total_hypotheses', 0) if "error" not in stats_result else 0,
                "dataset_shape": stats_result.get('summary', {}).get('dataset_shape', [0, 0]) if "error" not in stats_result else [0, 0]
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "question": question,
            "question_type": "WHY",
            "error": f"WHY question processing failed: {str(e)}",
            "planner_decision": planner_decision
        }


def initialize_llm() -> AzureChatOpenAI:
    """
    Initialize and return the LLM instance.
    Use this in FastAPI startup event.
    
    Returns:
        AzureChatOpenAI instance configured for Azure OpenAI
    """
    load_dotenv(override=True)
    
    return AzureChatOpenAI(
        azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", "https://assistant-genai.openai.azure.com/"),
        api_key=os.environ.get("AZURE_OPENAI_API_KEY", ""),
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
        temperature=0.0,
        timeout=120.0,
        max_retries=2,
    )
