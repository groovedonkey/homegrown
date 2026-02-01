from pydantic import BaseModel
from typing import List, Optional


class ChatRequest(BaseModel):
    enrollment_id: int
    message: str


class ChatResponse(BaseModel):
    agent_response: str
    workspace_update: Optional[dict] = None


class ChatHistoryItem(BaseModel):
    id: int
    sender: str
    content: str
    timestamp: str


class ChatHistoryResponse(BaseModel):
    enrollment_id: int
    items: List[ChatHistoryItem]
