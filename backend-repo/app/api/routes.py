from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.llm import LMStudioClient, get_lm_client


class ChatRequest(BaseModel):
    class Config:
        orm_mode = True

    query: str = Field(..., min_length=1, description="User question for the assistant.")


class ChatResponse(BaseModel):
    class Config:
        orm_mode = True

    message: str = Field(..., description="Assistant response content.")


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    client: LMStudioClient = Depends(get_lm_client),
) -> ChatResponse:
  try:
    reply = await client.generate_reply(request.query)
  except RuntimeError as exc:
    raise HTTPException(status_code=502, detail=str(exc)) from exc

  return ChatResponse(message=reply)
