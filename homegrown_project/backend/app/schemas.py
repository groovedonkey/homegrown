from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class ChatRequest(BaseModel):
    enrollment_id: int
    message: str


class ChatResponse(BaseModel):
    agent_response: str
    workspace_update: Optional[dict] = None


class UIBlocksResponse(BaseModel):
    version: int = 1
    mode: str = "chat"
    blocks: List[Dict[str, Any]]
    workspace_update: Optional[dict] = None


class QuizAnswer(BaseModel):
    question_id: str
    answer_id: str


class QuizSubmitRequest(BaseModel):
    enrollment_id: int
    quiz_id: str
    answers: List[QuizAnswer]


class QuizQuestionResult(BaseModel):
    question_id: str
    correct_answer_id: Optional[str] = None
    given_answer_id: Optional[str] = None
    is_correct: bool


class QuizSubmitResponse(BaseModel):
    quiz_id: str
    score: int
    total: int
    passing_score: Optional[int] = None
    passed: Optional[bool] = None
    results: List[QuizQuestionResult]


class ChatHistoryItem(BaseModel):
    id: int
    sender: str
    content: str
    timestamp: str


class ChatHistoryResponse(BaseModel):
    enrollment_id: int
    items: List[ChatHistoryItem]
