from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..deps import get_db
from ..schemas import ChatHistoryResponse, ChatRequest, ChatResponse
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


@router.get("/chat/history", response_model=ChatHistoryResponse)
async def chat_history_endpoint(
    enrollment_id: int = Query(..., ge=1),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    logs = (
        db.query(models.ChatLog)
        .filter(models.ChatLog.enrollment_id == enrollment_id)
        .order_by(models.ChatLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    logs.reverse()

    items = [
        {
            "id": log.id,
            "sender": log.sender,
            "content": log.content,
            "timestamp": log.timestamp.isoformat() if log.timestamp else "",
        }
        for log in logs
    ]

    return {"enrollment_id": enrollment_id, "items": items}
