import re
import json
from typing import List, Optional, Literal, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from openai import AsyncAzureOpenAI
import plotly.io as pio

from app.services.llm import get_lm_client
from app.config import get_settings
from app.services.dataset_manager import get_dataset_manager


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.95
    max_tokens: Optional[int] = 4096
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    content: str


class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language query about HR data")
    include_visualization: bool = Field(True, description="Whether to generate visualization")


class AnalysisRequest(BaseModel):
    """Request for intelligent multi-agent analysis."""
    question: str = Field(..., description="Natural language question about HR data")
    num_hypotheses: int = Field(3, ge=1, le=10, description="Number of hypotheses for WHY questions")
    include_visualization: bool = Field(True, description="Generate visualization for WHAT questions")


class QueryResponse(BaseModel):
    success: bool
    question: str
    sql: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    rows: int = 0
    columns: List[str] = []
    visualization: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Response from multi-agent analysis."""
    success: bool
    question: str
    question_type: str  # "WHAT" or "WHY"
    analysis_type: Optional[str] = None  # "descriptive_analytics" or "causal_analytics"
    planner_decision: Optional[Dict[str, Any]] = None
    
    # For WHAT questions
    sql: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    rows: Optional[int] = None
    columns: Optional[List[str]] = None
    visualization: Optional[Dict[str, Any]] = None
    
    # For WHY questions
    sql_queries: Optional[List[str]] = None  # Multiple SQL queries
    visualizations: Optional[List[Dict[str, Any]]] = None  # Multiple visualizations
    hypotheses: Optional[Dict[str, Any]] = None
    statistical_results: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None
    
    error: Optional[str] = None


router = APIRouter()


def strip_think_tags(content: str) -> str:
    """Remove <think>...</think> sections that some models emit."""
    cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    client: AsyncAzureOpenAI = Depends(get_lm_client),
    settings = Depends(get_settings),
) -> ChatResponse:
    try:
        completion = await client.chat.completions.create(
            model=settings.azure_openai_deployment,
            messages=[m.dict() for m in req.messages],  # Changed from model_dump() to dict()
            temperature=req.temperature,
            top_p=req.top_p,
            max_tokens=req.max_tokens,
            stream=False,  # set True only if you implement streaming on frontend
        )
        content = completion.choices[0].message.content or ""
        content = strip_think_tags(content)
        return ChatResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=QueryResponse)
async def process_query(req: QueryRequest) -> QueryResponse:
    """
    Process a natural language query about HR data (WHAT questions only).
    Returns SQL, data, and optional visualization.
    
    Note: For intelligent routing, use /analyze endpoint instead.
    """
    from app.main import llm_instance
    from app.services.text_to_sql_agent import text_to_sql_agent, get_database_connection
    from app.services.visualization_agent import visualization_agent
    
    if llm_instance is None:
        raise HTTPException(
            status_code=503,
            detail="Multi-Agent System not initialized. Please check server logs."
        )
    
    try:
        # Get database connection
        db = get_database_connection()
        
        # Process the query using Text-to-SQL agent directly
        result = await text_to_sql_agent(req.question, llm_instance, db)
        
        if not result.get("success", False):
            return QueryResponse(
                success=False,
                question=req.question,
                error=result.get("error")
            )
        
        # Convert DataFrame to list of dicts for JSON serialization
        data_list = result["data"].to_dict(orient="records") if result["data"] is not None else []
        
        # Process visualization if requested
        viz_data = None
        if req.include_visualization and result["data"] is not None and len(result["data"]) > 0:
            viz_result = await visualization_agent(result["data"], llm_instance, req.question)
            if viz_result.get("success"):
                fig = viz_result["figure"]
                viz_data = {
                    "success": True,
                    "code": viz_result["code"],
                    "plotly_json": json.loads(pio.to_json(fig))
                }
            else:
                viz_data = {
                    "success": False,
                    "error": viz_result.get("error", "Visualization generation failed")
                }
        
        return QueryResponse(
            success=True,
            question=req.question,
            sql=result["sql"],
            data=data_list,
            rows=result["rows"],
            columns=result["columns"],
            visualization=viz_data,
            error=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@router.post("/sql-only")
async def get_sql_data(req: QueryRequest) -> QueryResponse:
    """
    Get SQL and data without generating visualization.
    Faster endpoint for data-only requests.
    
    Note: For intelligent routing, use /analyze endpoint instead.
    """
    from app.main import llm_instance
    from app.services.text_to_sql_agent import text_to_sql_agent, get_database_connection
    
    if llm_instance is None:
        raise HTTPException(
            status_code=503,
            detail="Multi-Agent System not initialized. Please check server logs."
        )
    
    try:
        db = get_database_connection()
        result = await text_to_sql_agent(req.question, llm_instance, db)
        
        if not result["success"]:
            return QueryResponse(
                success=False,
                question=req.question,
                error=result["error"]
            )
        
        # Convert DataFrame to list of dicts
        data_list = result["data"].to_dict(orient="records") if result["data"] is not None else []
        
        return QueryResponse(
            success=True,
            question=req.question,
            sql=result["sql"],
            data=data_list,
            rows=result["rows"],
            columns=result["columns"],
            visualization=None,
            error=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQL query failed: {str(e)}")


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_question(req: AnalysisRequest) -> AnalysisResponse:
    """
    Intelligent multi-agent analysis with automatic routing.
    
    - WHAT questions → Text-to-SQL + Visualization
    - WHY questions → Hypothesis Generation + Statistical Testing
    """
    from app.main import llm_instance
    from app.services.multi_agent_system import process_question
    
    if llm_instance is None:
        raise HTTPException(
            status_code=503,
            detail="Multi-Agent System not initialized. Please check server logs."
        )
    
    try:
        # Process with multi-agent system
        print(f"\n{'='*70}")
        print(f"[INFO] Processing question: {req.question}")
        print(f"{'='*70}")
        
        result = await process_question(
            question=req.question,
            llm=llm_instance,
            num_hypotheses=req.num_hypotheses,
            include_viz=req.include_visualization,
            verbose=True  # Enable verbose logging
        )
        
        print("\n[INFO] Result summary:")
        print(f"  - Success: {result.get('success', False)}")
        print(f"  - Question Type: {result.get('question_type', 'UNKNOWN')}")
        print(f"  - Error: {result.get('error', 'None')}")
        print(f"{'='*70}\n")
        
        if not result.get("success", False):
            return AnalysisResponse(
                success=False,
                question=req.question,
                question_type=result.get("question_type", "UNKNOWN"),
                error=result.get("error", "Unknown error occurred")
            )
        
        # Build response based on question type
        question_type = result.get("question_type", "WHAT")
        
        if question_type == "WHAT":
            # Descriptive analytics response
            data_list = result.get("data")
            if data_list is not None and hasattr(data_list, 'to_dict'):
                data_list = data_list.to_dict(orient="records")
            
            # Process visualization
            viz_data = None
            if result.get("visualization") and result["visualization"].get("success"):
                fig = result["visualization"]["figure"]
                viz_data = {
                    "success": True,
                    "code": result["visualization"]["code"],
                    "plotly_json": json.loads(pio.to_json(fig))
                }
            elif result.get("visualization"):
                viz_data = {
                    "success": False,
                    "error": result["visualization"].get("error", "Visualization generation failed")
                }
            
            return AnalysisResponse(
                success=True,
                question=req.question,
                question_type="WHAT",
                analysis_type=result.get("analysis_type"),
                planner_decision=result.get("planner_decision"),
                sql=result.get("sql"),
                data=data_list,
                rows=result.get("rows", 0),
                columns=result.get("columns", []),
                visualization=viz_data
            )
        
        else:  # WHY question
            # Causal analytics response with multiple SQL queries and visualizations
            
            # Process multiple visualizations
            visualizations_data = []
            if result.get("visualizations"):
                for viz in result["visualizations"]:
                    if viz.get("success") and viz.get("figure"):
                        fig = viz["figure"]
                        visualizations_data.append({
                            "success": True,
                            "code": viz.get("code"),
                            "plotly_json": json.loads(pio.to_json(fig)),
                            "hypothesis_id": viz.get("hypothesis_id")
                        })
                    else:
                        visualizations_data.append({
                            "success": False,
                            "error": viz.get("error", "Visualization generation failed"),
                            "hypothesis_id": viz.get("hypothesis_id")
                        })
            
            # Extract SQL queries
            sql_queries = []
            if result.get("sql_queries"):
                for query in result["sql_queries"]:
                    if isinstance(query, dict):
                        sql_queries.append(query.get("sql") or "")
                    elif query is not None:
                        sql_queries.append(str(query))
                    else:
                        sql_queries.append("")
            
            return {
                "success": True,
                "question": req.question,
                "question_type": "WHY",
                "analysis_type": result.get("analysis_type"),
                "planner_decision": result.get("planner_decision"),
                "sql_queries": sql_queries,
                "visualizations": visualizations_data,
                "hypotheses": result.get("hypotheses"),
                "statistical_results": result.get("statistical_results"),
                "summary": result.get("summary")
            }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Multi-agent analysis failed: {str(e)}")


@router.post("/analyze/what", response_model=AnalysisResponse)
async def analyze_what_question(req: QueryRequest) -> AnalysisResponse:
    """
    Direct endpoint for WHAT questions (Descriptive Analytics).
    Bypasses planner and goes straight to Text-to-SQL + Visualization.
    """
    from app.main import llm_instance
    from app.services.multi_agent_system import _handle_what_question
    
    if llm_instance is None:
        raise HTTPException(
            status_code=503,
            detail="Multi-Agent System not initialized. Please check server logs."
        )
    
    try:
        # Create a mock planner decision for consistency
        planner_decision = {
            "question_type": "WHAT",
            "agents_to_call": ["text_to_sql", "visualization"],
            "reasoning": "Direct WHAT endpoint - bypassed planner"
        }
        
        result = await _handle_what_question(
            question=req.question,
            llm=llm_instance,
            include_viz=req.include_visualization,
            verbose=False,
            planner_decision=planner_decision
        )
        
        if not result.get("success", False):
            return AnalysisResponse(
                success=False,
                question=req.question,
                question_type="WHAT",
                error=result.get("error", "Analysis failed")
            )
        
        # Convert DataFrame to list of dicts
        data_list = result.get("data")
        if data_list is not None and hasattr(data_list, 'to_dict'):
            data_list = data_list.to_dict(orient="records")
        
        # Process visualization
        viz_data = None
        if result.get("visualization") and result["visualization"].get("success"):
            fig = result["visualization"]["figure"]
            viz_data = {
                "success": True,
                "code": result["visualization"]["code"],
                "plotly_json": json.loads(pio.to_json(fig))
            }
        elif result.get("visualization"):
            viz_data = {
                "success": False,
                "error": result["visualization"].get("error", "Visualization failed")
            }
        
        return AnalysisResponse(
            success=True,
            question=req.question,
            question_type="WHAT",
            analysis_type="descriptive_analytics",
            sql=result.get("sql"),
            data=data_list,
            rows=result.get("rows", 0),
            columns=result.get("columns", []),
            visualization=viz_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"WHAT analysis failed: {str(e)}")


@router.post("/analyze/why")
async def analyze_why_question(req: AnalysisRequest) -> Dict[str, Any]:
    """
    Direct endpoint for WHY questions (Causal Analytics).
    Bypasses planner and goes straight to Hypothesis + Statistical Testing.
    """
    from app.main import llm_instance
    from app.services.multi_agent_system import _handle_why_question
    
    if llm_instance is None:
        raise HTTPException(
            status_code=503,
            detail="Multi-Agent System not initialized. Please check server logs."
        )
    
    try:
        # Create a mock planner decision for consistency
        planner_decision = {
            "question_type": "WHY",
            "agents_to_call": ["text_to_sql", "visualization", "hypothesis", "stats"],
            "reasoning": "Direct WHY endpoint - bypassed planner"
        }
        
        result = await _handle_why_question(
            question=req.question,
            llm=llm_instance,
            num_hypotheses=req.num_hypotheses,
            include_viz=True,
            verbose=False,
            planner_decision=planner_decision
        )
        
        if not result.get("success", False):
            return {
                "success": False,
                "question": req.question,
                "question_type": "WHY",
                "error": result.get("error", "Analysis failed")
            }
        
        return {
            "success": True,
            "question": req.question,
            "question_type": "WHY",
            "analysis_type": "causal_analytics",
            "hypotheses": result.get("hypotheses"),
            "statistical_results": result.get("statistical_results")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"WHY analysis failed: {str(e)}")


# ============================================================================
# DATASET MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/datasets")
async def get_datasets():
    """Get list of all available datasets"""
    try:
        dataset_manager = get_dataset_manager()
        datasets = dataset_manager.get_all_datasets()
        return {
            "success": True,
            "datasets": datasets,
            "current_dataset_id": dataset_manager.current_dataset_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get datasets: {str(e)}")


@router.get("/datasets/current")
async def get_current_dataset():
    """Get information about the currently active dataset"""
    try:
        dataset_manager = get_dataset_manager()
        current = dataset_manager.get_current_dataset()
        return {
            "success": True,
            "dataset": {
                "id": current.id,
                "name": current.name,
                "description": current.description,
                "schema_name": current.schema_name,
                "main_table": current.main_table
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current dataset: {str(e)}")


@router.post("/datasets/switch")
async def switch_dataset(dataset_id: str):
    """Switch to a different dataset"""
    try:
        dataset_manager = get_dataset_manager()
        success = dataset_manager.switch_dataset(dataset_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
        
        current = dataset_manager.get_current_dataset()
        return {
            "success": True,
            "message": f"Switched to dataset: {current.name}",
            "dataset": {
                "id": current.id,
                "name": current.name,
                "description": current.description,
                "schema_name": current.schema_name,
                "main_table": current.main_table
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to switch dataset: {str(e)}")


@router.get("/datasets/{dataset_id}")
async def get_dataset_info(dataset_id: str):
    """Get detailed information about a specific dataset"""
    try:
        dataset_manager = get_dataset_manager()
        dataset = dataset_manager.get_dataset(dataset_id)
        
        if dataset is None:
            raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
        
        return {
            "success": True,
            "dataset": {
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "schema_name": dataset.schema_name,
                "main_table": dataset.main_table,
                "data_dictionary_path": dataset.data_dictionary_path,
                "kpi_documentation_path": dataset.kpi_documentation_path
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dataset info: {str(e)}")
