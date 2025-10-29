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


class QueryResponse(BaseModel):
    success: bool
    question: str
    sql: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    rows: int = 0
    columns: List[str] = []
    visualization: Optional[Dict[str, Any]] = None
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
    Process a natural language query about HR data.
    Returns SQL, data, and optional visualization.
    """
    from app.main import combined_agent
    
    if combined_agent is None:
        raise HTTPException(
            status_code=503,
            detail="Combined Agent not initialized. Please check server logs."
        )
    
    try:
        # Process the query
        result = combined_agent.process_query(
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
    """
    from app.main import combined_agent
    
    if combined_agent is None:
        raise HTTPException(
            status_code=503,
            detail="Combined Agent not initialized. Please check server logs."
        )
    
    try:
        result = combined_agent.get_sql_only(req.question)
        
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
