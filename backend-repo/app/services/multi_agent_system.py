"""
Multi-Agent HR Analytics System
================================
Integrates Planner, Text-to-SQL, Visualization, Hypothesis, and Stats agents.

Author: Yogarajaadithya
Date: October 31, 2025
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI

from app.services.TTS_vis import CombinedAgent
from app.services.planner_agent import PlannerAgent
from app.services.hypothesis_stats_agent import HypothesisAgent, StatsAgent, load_hr_data


class MultiAgentSystem:
    """
    Multi-Agent System orchestrator for HR Analytics.
    
    Routes questions to appropriate agents based on question type:
    - WHAT questions → Text-to-SQL + Visualization
    - WHY questions → Hypothesis + Statistical Testing
    """
    
    def __init__(self):
        """Initialize all agents in the system."""
        # Load environment
        load_dotenv(override=True)
        
        # Initialize LLM (shared across all agents)
        self.llm = ChatOpenAI(
            model=os.environ.get("OPENAI_MODEL", "ibm/granite-3.2-8b"),
            base_url=os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:1234/v1"),
            api_key=os.environ.get("OPENAI_API_KEY", "lm-studio"),
            temperature=0.0,
            timeout=120.0,  # 2 minutes timeout
            max_retries=2,  # Retry failed requests
        )
        
        # Initialize agents
        self.planner = PlannerAgent(llm=self.llm)
        self.text_to_sql_viz = CombinedAgent()  # Uses its own LLM internally
        self.hypothesis_agent = HypothesisAgent(llm=self.llm)
        
        # Load data for stats agent (lazy loading)
        self._hr_data = None
        self._stats_agent = None
        
        print("✅ Multi-Agent System initialized successfully!")
    
    @property
    def stats_agent(self) -> StatsAgent:
        """Lazy load stats agent with HR data."""
        if self._stats_agent is None:
            if self._hr_data is None:
                print("📊 Loading HR data for statistical testing...")
                self._hr_data = load_hr_data()
                print(f"✅ Loaded {len(self._hr_data)} employee records")
            self._stats_agent = StatsAgent(self._hr_data)
        return self._stats_agent
    
    def process_question(
        self,
        question: str,
        num_hypotheses: int = 3,
        include_viz: bool = True,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Process user question with intelligent routing.
        
        Args:
            question: User's natural language question
            num_hypotheses: Number of hypotheses to generate for WHY questions
            include_viz: Whether to generate visualizations for WHAT questions
            verbose: Print detailed logs
            
        Returns:
            Dictionary with results based on question type
        """
        try:
            # Step 1: Analyze question with Planner Agent
            if verbose:
                print(f"\n{'='*70}")
                print("🤔 PLANNER AGENT ANALYSIS")
                print(f"{'='*70}")
            
            decision = self.planner.analyze_question(question)
            question_type = decision.get('question_type', 'WHAT')
            
            if verbose:
                print(f"\n📝 Question: {question}")
                print(f"🎯 Type: {question_type}")
                print(f"💭 Reasoning: {decision.get('reasoning')}")
                print(f"🤖 Agents: {', '.join(decision.get('agents_to_call', []))}")
                print(f"\n{'-'*70}\n")
            
            # Step 2: Route to appropriate agents
            if question_type == 'WHAT':
                return self._handle_what_question(question, include_viz, verbose, decision)
            else:  # WHY question
                return self._handle_why_question(question, num_hypotheses, include_viz, verbose, decision)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Multi-agent processing failed: {str(e)}",
                "question": question
            }
    
    def _handle_what_question(
        self,
        question: str,
        include_viz: bool,
        verbose: bool,
        planner_decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle WHAT questions (Descriptive Analytics).
        
        Routes to: Text-to-SQL + Visualization agents
        """
        if verbose:
            print("🔄 Routing to TEXT-TO-SQL + VISUALIZATION AGENTS")
            print(f"{'-'*70}\n")
        
        # Process with Text-to-SQL + Visualization agent
        result = self.text_to_sql_viz.process_query(
            question=question,
            include_viz=include_viz,
            verbose=verbose
        )
        
        # Add planner metadata
        result["question_type"] = "WHAT"
        result["planner_decision"] = planner_decision
        result["analysis_type"] = "descriptive_analytics"
        
        return result
    
    def _handle_why_question(
        self,
        question: str,
        num_hypotheses: int,
        include_viz: bool,
        verbose: bool,
        planner_decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle WHY questions (Causal Analytics).
        
        Routes to: Text-to-SQL + Visualization + Hypothesis + Statistical Testing agents
        """
        if verbose:
            print("🔄 Routing to TEXT-TO-SQL + VISUALIZATION + HYPOTHESIS + STATISTICAL TESTING AGENTS")
            print(f"{'-'*70}\n")
        
        try:
            # Step 1: Generate SQL and fetch data (for visualization and context)
            if verbose:
                print(f"📊 Generating SQL query for data context...")
            
            sql_result = self.text_to_sql_viz.sql_agent.query(question, verbose=verbose)
            
            if not sql_result.get("success", False):
                # Continue without data/viz if SQL fails
                sql_query = None
                data = None
                viz_result = None
                if verbose:
                    print(f"⚠️ SQL generation failed, continuing with hypothesis testing only\n")
            else:
                sql_query = sql_result.get("sql")
                data = sql_result.get("data")
                
                # Step 2: Generate visualization if requested
                viz_result = None
                if include_viz and data is not None and not data.empty:
                    if verbose:
                        print(f"📈 Generating visualization...")
                    
                    viz_result = self.text_to_sql_viz.viz_agent.visualize(
                        df=data,
                        original_question=question,
                        verbose=verbose
                    )
                    
                    if verbose:
                        if viz_result.get("success"):
                            print(f"✅ Visualization generated successfully\n")
                        else:
                            print(f"⚠️ Visualization generation failed\n")
            
            # Step 3: Generate hypotheses
            if verbose:
                print(f"📋 Generating {num_hypotheses} hypotheses...")
            
            hypotheses_result = self.hypothesis_agent.generate_hypotheses(
                user_question=question,
                num_hypotheses=num_hypotheses
            )
            
            if "error" in hypotheses_result:
                error_message = f"Hypothesis generation failed: {hypotheses_result['error']}"
                if verbose:
                    print(f"❌ {error_message}")
                    print(f"🔍 Troubleshooting steps:")
                    print(f"   1. Verify LM Studio is running on http://127.0.0.1:1234")
                    print(f"   2. Check if model is loaded in LM Studio")
                    print(f"   3. Try a simple curl test: curl http://127.0.0.1:1234/v1/models")
                return {
                    "success": False,
                    "question": question,
                    "question_type": "WHY",
                    "error": error_message,
                    "planner_decision": planner_decision
                }
            
            num_generated = len(hypotheses_result.get('hypotheses', []))
            if verbose:
                print(f"✅ Generated {num_generated} hypotheses\n")
            
            # Step 4: Run statistical tests
            if verbose:
                print(f"🧪 Running statistical tests...")
            
            stats_result = self.stats_agent.execute_all_hypotheses(hypotheses_result)
            
            if "error" in stats_result:
                return {
                    "success": False,
                    "question": question,
                    "question_type": "WHY",
                    "hypotheses": hypotheses_result,
                    "sql": sql_query,
                    "data": data,
                    "visualization": viz_result,
                    "error": f"Statistical testing failed: {stats_result['error']}",
                    "planner_decision": planner_decision
                }
            
            if verbose:
                print(f"✅ Completed {stats_result['summary']['total_hypotheses']} statistical tests\n")
            
            # Return combined results with SQL, data, and visualization
            return {
                "success": True,
                "question": question,
                "question_type": "WHY",
                "analysis_type": "causal_analytics",
                "planner_decision": planner_decision,
                "sql": sql_query,
                "data": data,
                "rows": len(data) if data is not None else 0,
                "columns": data.columns.tolist() if data is not None else [],
                "visualization": viz_result,
                "hypotheses": hypotheses_result,
                "statistical_results": stats_result,
                "summary": {
                    "total_hypotheses": num_generated,
                    "tests_completed": stats_result['summary']['total_hypotheses'],
                    "dataset_shape": stats_result['summary']['dataset_shape']
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
    
    def get_what_analysis(
        self,
        question: str,
        include_viz: bool = True,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Direct access to WHAT question analysis (Text-to-SQL + Viz).
        
        Args:
            question: Natural language question
            include_viz: Generate visualization
            verbose: Print logs
            
        Returns:
            Dictionary with SQL, data, and optional visualization
        """
        return self.text_to_sql_viz.process_query(
            question=question,
            include_viz=include_viz,
            verbose=verbose
        )
    
    def get_why_analysis(
        self,
        question: str,
        num_hypotheses: int = 3,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Direct access to WHY question analysis (Hypothesis + Stats).
        
        Args:
            question: Research question
            num_hypotheses: Number of hypotheses to generate
            verbose: Print logs
            
        Returns:
            Dictionary with hypotheses and statistical test results
        """
        # Generate hypotheses
        hypotheses_result = self.hypothesis_agent.generate_hypotheses(
            user_question=question,
            num_hypotheses=num_hypotheses
        )
        
        if "error" in hypotheses_result:
            return {
                "success": False,
                "error": hypotheses_result["error"],
                "hypotheses": []
            }
        
        # Run statistical tests
        stats_result = self.stats_agent.execute_all_hypotheses(hypotheses_result)
        
        return {
            "success": True,
            "question": question,
            "hypotheses": hypotheses_result,
            "statistical_results": stats_result
        }


def initialize_multi_agent_system() -> MultiAgentSystem:
    """
    Initialize and return Multi-Agent System.
    Use this in FastAPI startup event.
    
    Returns:
        MultiAgentSystem instance ready to use
    """
    return MultiAgentSystem()
