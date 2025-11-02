import re
import json
from typing import List, Optional, Literal, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
import plotly.io as pio

from app.services.llm import get_lm_client
from app.config import get_settings


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
    client: AsyncOpenAI = Depends(get_lm_client),
    settings = Depends(get_settings),
) -> ChatResponse:
    try:
        completion = await client.chat.completions.create(
            model=settings.lmstudio_model_id,
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
    from app.main import multi_agent_system
    
    if multi_agent_system is None:
        raise HTTPException(
            status_code=503,
            detail="Multi-Agent System not initialized. Please check server logs."
        )
    
    try:
        # Process the query using Text-to-SQL agent directly
        result = multi_agent_system.text_to_sql_viz.process_query(
            question=req.question,
            include_viz=req.include_visualization,
            verbose=False
        )
        
        if not result["success"]:
            return QueryResponse(
                success=False,
                question=req.question,
                error=result["error"]
            )
        
        # Convert DataFrame to list of dicts for JSON serialization
        data_list = result["data"].to_dict(orient="records") if result["data"] is not None else []
        
        # Process visualization if present
        viz_data = None
        if result["visualization"] and result["visualization"]["success"]:
            fig = result["visualization"]["figure"]
            viz_data = {
                "success": True,
                "code": result["visualization"]["code"],
                "plotly_json": json.loads(pio.to_json(fig))  # Convert Plotly figure to JSON
            }
        elif result["visualization"]:
            viz_data = {
                "success": False,
                "error": result["visualization"].get("error", "Unknown error")
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
    from app.main import multi_agent_system
    
    if multi_agent_system is None:
        raise HTTPException(
            status_code=503,
            detail="Multi-Agent System not initialized. Please check server logs."
        )
    
    try:
        result = multi_agent_system.text_to_sql_viz.get_sql_only(req.question)
        
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
    from app.main import multi_agent_system
    
    if multi_agent_system is None:
        raise HTTPException(
            status_code=503,
            detail="Multi-Agent System not initialized. Please check server logs."
        )
    
    try:
        # Process with multi-agent system
        print(f"\n{'='*70}")
        print(f"📝 Processing question: {req.question}")
        print(f"{'='*70}")
        
        result = multi_agent_system.process_question(
            question=req.question,
            num_hypotheses=req.num_hypotheses,
            include_viz=req.include_visualization,
            verbose=True  # Enable verbose logging
        )
        
        print(f"\n🔍 Result summary:")
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
            # Causal analytics response with SQL, data, and visualization
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
                question_type="WHY",
                analysis_type=result.get("analysis_type"),
                planner_decision=result.get("planner_decision"),
                sql=result.get("sql"),
                data=data_list,
                rows=result.get("rows", 0),
                columns=result.get("columns", []),
                visualization=viz_data,
                hypotheses=result.get("hypotheses"),
                statistical_results=result.get("statistical_results"),
                summary=result.get("summary")
            )
        
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
    from app.main import multi_agent_system
    
    if multi_agent_system is None:
        raise HTTPException(
            status_code=503,
            detail="Multi-Agent System not initialized. Please check server logs."
        )
    
    try:
        result = multi_agent_system.get_what_analysis(
            question=req.question,
            include_viz=req.include_visualization,
            verbose=False
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
    from app.main import multi_agent_system
    
    if multi_agent_system is None:
        raise HTTPException(
            status_code=503,
            detail="Multi-Agent System not initialized. Please check server logs."
        )
    
    try:
        result = multi_agent_system.get_why_analysis(
            question=req.question,
            num_hypotheses=req.num_hypotheses,
            verbose=False
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
