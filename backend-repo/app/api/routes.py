from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

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


router = APIRouter()


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
        return ChatResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
