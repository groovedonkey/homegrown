from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    enrollment_id: int
    message: str


class ChatResponse(BaseModel):
    agent_response: str
    workspace_update: Optional[dict] = None
