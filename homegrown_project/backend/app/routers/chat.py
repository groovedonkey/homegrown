from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db
from ..schemas import ChatRequest, ChatResponse
from ..services.chat_service import handle_chat
from .. import models


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    enrollment, ai_text, workspace_update = handle_chat(
        db=db,
        enrollment_id=request.enrollment_id,
        user_message=request.message,
    )

    db.add(models.ChatLog(enrollment_id=enrollment.id, sender="student", content=request.message))
    db.add(models.ChatLog(enrollment_id=enrollment.id, sender="agent", content=ai_text))

    db.commit()

    return {"agent_response": ai_text, "workspace_update": workspace_update}
