"""
Example integration of enhanced logging system with multi-agent system.

This file demonstrates how to integrate the new logging utility into the existing
multi-agent system to provide better error tracking and monitoring.

Usage: Replace relevant sections in multi_agent_system.py with these patterns.
"""

from app.utils.logger import get_agent_logger, system_logger, get_all_logs
from typing import Dict, Any


async def process_question_with_logging(
    question: str,
    llm=None,
    num_hypotheses: int = 3,
    include_viz: bool = True,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Enhanced version of process_question with comprehensive logging.
    """
    # Get system logger
    sys_logger = system_logger.get_agent_logger("System")
    
    try:
        sys_logger.info(f"Received query: '{question}'")
        
        # Initialize LLM if not provided
        if llm is None:
            sys_logger.info("Initializing LLM...")
            llm = initialize_llm()
            sys_logger.success("LLM initialized successfully")
        
        # Step 1: Planner Agent
        planner_logger = get_agent_logger("Planner")
        planner_logger.start_timer()
        planner_logger.info("Routing through Planner Agent...")
        
        try:
            planner_decision = await planner_agent(question, llm)
            duration = planner_logger.stop_timer()
            
            question_type = planner_decision.get('question_type', 'WHAT')
            agents_to_call = planner_decision.get('agents_to_call', [])
            
            planner_logger.success(
                f"Planner routing complete: {question_type} question",
                duration=duration,
                details=f"Agents: {', '.join(agents_to_call)}"
            )
            
        except Exception as e:
            duration = planner_logger.stop_timer()
            planner_logger.error(
                "Planner Agent failed",
                error=e,
                include_trace=True
            )
            raise
        
        # Step 2: Route based on question type
        if question_type == 'WHAT':
            result = await _handle_what_question_with_logging(
                question, llm, include_viz, verbose, planner_decision
            )
        else:
            result = await _handle_why_question_with_logging(
                question, llm, num_hypotheses, include_viz, verbose, planner_decision
            )
        
        # Add all logs to result
        result['logs'] = get_all_logs()
        result['error_summary'] = system_logger.get_error_summary()
        result['agent_performance'] = system_logger.get_agent_performance()
        
        sys_logger.success("Query processing complete")
        
        return result
        
    except Exception as e:
        sys_logger.critical(
            "Multi-agent processing failed",
            error=e,
            include_trace=True
        )
        
        return {
            "success": False,
            "error": str(e),
            "question": question,
            "logs": get_all_logs(),
            "error_summary": system_logger.get_error_summary()
        }


async def _handle_what_question_with_logging(
    question: str,
    llm,
    include_viz: bool,
    verbose: bool,
    planner_decision: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle WHAT questions with enhanced logging."""
    
    sys_logger = get_agent_logger("System")
    sys_logger.info("Processing WHAT question (Descriptive Analytics)")
    
    try:
        # Step 1: Text-to-SQL Agent
        sql_logger = get_agent_logger("Text-to-SQL")
        sql_logger.start_timer()
        sql_logger.info("Generating SQL query...")
        
        try:
            db_connection = get_database_connection()
            sql_result = await text_to_sql_agent(question, llm, db_connection)
            duration = sql_logger.stop_timer()
            
            if not sql_result.get('success'):
                sql_logger.warning(
                    "SQL generation completed with issues",
                    details=sql_result.get('error', 'Unknown error')
                )
            else:
                sql_logger.success(
                    "SQL query executed successfully",
                    duration=duration,
                    details=f"Rows: {len(sql_result.get('data', []))}"
                )
        
        except Exception as e:
            duration = sql_logger.stop_timer()
            sql_logger.error(
                "Text-to-SQL Agent failed",
                error=e,
                include_trace=True
            )
            raise
        
        # Step 2: Visualization Agent (if requested)
        viz_result = {}
        if include_viz and sql_result.get('success'):
            viz_logger = get_agent_logger("Visualization")
            viz_logger.start_timer()
            viz_logger.info("Generating visualization...")
            
            try:
                viz_result = await visualization_agent(
                    question,
                    sql_result.get('data', []),
                    llm
                )
                duration = viz_logger.stop_timer()
                
                if viz_result.get('success'):
                    viz_logger.success(
                        f"Visualization created: {viz_result.get('chart_type')}",
                        duration=duration
                    )
                else:
                    viz_logger.warning(
                        "Visualization generation failed",
                        details=viz_result.get('error')
                    )
            
            except Exception as e:
                duration = viz_logger.stop_timer()
                viz_logger.error(
                    "Visualization Agent failed",
                    error=e,
                    include_trace=True
                )
                # Continue without viz
                viz_result = {"success": False, "error": str(e)}
        
        return {
            "success": True,
            "question_type": "WHAT",
            "sql_result": sql_result,
            "visualization": viz_result,
            "planner_decision": planner_decision
        }
    
    except Exception as e:
        sys_logger.error(
            "WHAT question processing failed",
            error=e,
            include_trace=True
        )
        raise


async def _handle_why_question_with_logging(
    question: str,
    llm,
    num_hypotheses: int,
    include_viz: bool,
    verbose: bool,
    planner_decision: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle WHY questions with enhanced logging."""
    
    sys_logger = get_agent_logger("System")
    sys_logger.info("Processing WHY question (Causal Analytics)")
    
    try:
        # Step 1: Hypothesis Generation
        hyp_logger = get_agent_logger("Hypothesis")
        hyp_logger.start_timer()
        hyp_logger.info(f"Generating {num_hypotheses} hypotheses...")
        
        try:
            db_connection = get_database_connection()
            hypothesis_result = await hypothesis_agent(
                question,
                llm,
                db_connection,
                num_hypotheses
            )
            duration = hyp_logger.stop_timer()
            
            if hypothesis_result.get('success'):
                hyp_count = len(hypothesis_result.get('hypotheses', []))
                hyp_logger.success(
                    f"Generated {hyp_count} hypotheses",
                    duration=duration
                )
            else:
                hyp_logger.error(
                    "Hypothesis generation failed",
                    error=Exception(hypothesis_result.get('error'))
                )
        
        except Exception as e:
            duration = hyp_logger.stop_timer()
            hyp_logger.error(
                "Hypothesis Agent failed",
                error=e,
                include_trace=True
            )
            raise
        
        # Step 2: Statistical Testing
        stats_logger = get_agent_logger("Stats")
        stats_logger.start_timer()
        stats_logger.info("Running statistical tests...")
        
        try:
            stats_results = []
            hypotheses = hypothesis_result.get('hypotheses', [])
            
            for idx, hypothesis in enumerate(hypotheses, 1):
                stats_logger.info(f"Testing hypothesis {idx}/{len(hypotheses)}...")
                
                try:
                    stats_result = await stats_agent(
                        hypothesis,
                        db_connection,
                        llm
                    )
                    
                    if stats_result.get('success'):
                        test_type = stats_result.get('test_type', 'unknown')
                        p_value = stats_result.get('p_value', 'N/A')
                        stats_logger.success(
                            f"Hypothesis {idx} tested ({test_type})",
                            details=f"p-value: {p_value}"
                        )
                    else:
                        stats_logger.warning(
                            f"Hypothesis {idx} test failed",
                            details=stats_result.get('error')
                        )
                    
                    stats_results.append(stats_result)
                
                except Exception as e:
                    stats_logger.error(
                        f"Failed to test hypothesis {idx}",
                        error=e,
                        include_trace=False  # Don't need full trace for each hypothesis
                    )
                    stats_results.append({
                        "success": False,
                        "error": str(e)
                    })
            
            duration = stats_logger.stop_timer()
            successful_tests = len([r for r in stats_results if r.get('success')])
            stats_logger.success(
                f"Statistical testing complete: {successful_tests}/{len(hypotheses)} successful",
                duration=duration
            )
        
        except Exception as e:
            duration = stats_logger.stop_timer()
            stats_logger.error(
                "Statistical testing failed",
                error=e,
                include_trace=True
            )
            raise
        
        return {
            "success": True,
            "question_type": "WHY",
            "hypothesis_result": hypothesis_result,
            "stats_results": stats_results,
            "planner_decision": planner_decision
        }
    
    except Exception as e:
        sys_logger.error(
            "WHY question processing failed",
            error=e,
            include_trace=True
        )
        raise


# Example decorator usage for timing database queries
from app.utils.logger import get_agent_logger

sql_logger = get_agent_logger("Text-to-SQL")

@sql_logger.timed_operation("Database Query Execution")
def execute_sql_query(connection, query):
    """Execute SQL query with automatic timing."""
    with connection.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()


# Example manual timing
async def generate_visualization_example(data, question, llm):
    """Generate visualization with manual timing."""
    viz_logger = get_agent_logger("Visualization")
    
    viz_logger.start_timer()
    viz_logger.info("Analyzing data for visualization...")
    
    try:
        # Analyze data
        chart_type = await determine_chart_type(data, question, llm)
        
        viz_logger.info(f"Creating {chart_type} chart...")
        
        # Generate chart
        chart_config = await create_chart_config(data, chart_type)
        
        duration = viz_logger.stop_timer()
        viz_logger.success(
            f"Visualization created successfully",
            duration=duration,
            details=f"Chart type: {chart_type}"
        )
        
        return {
            "success": True,
            "chart_type": chart_type,
            "config": chart_config
        }
    
    except Exception as e:
        duration = viz_logger.stop_timer()
        viz_logger.error(
            "Visualization generation failed",
            error=e,
            include_trace=True
        )
        
        return {
            "success": False,
            "error": str(e)
        }
