from fastapi import APIRouter, Depends, HTTPException, Query
import json
from sqlalchemy.orm import Session

from ..deps import get_db
from ..schemas import (
    ChatHistoryResponse,
    ChatRequest,
    QuizSubmitRequest,
    QuizSubmitResponse,
    UIBlocksResponse,
)
from ..services.chat_service import handle_chat
from .. import models


router = APIRouter()


@router.post("/chat", response_model=UIBlocksResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    enrollment, ai_payload, workspace_update = handle_chat(
        db=db,
        enrollment_id=request.enrollment_id,
        user_message=request.message,
    )

    db.add(models.ChatLog(enrollment_id=enrollment.id, sender="student", content=request.message))
    db.add(models.ChatLog(enrollment_id=enrollment.id, sender="agent", content=json.dumps(ai_payload)))

    db.commit()

    return ai_payload


@router.post("/quiz/submit", response_model=QuizSubmitResponse)
async def quiz_submit_endpoint(request: QuizSubmitRequest, db: Session = Depends(get_db)):
    enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == request.enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    facts = enrollment.student_facts or {}
    active_quiz = facts.get("active_quiz")
    if not isinstance(active_quiz, dict) or active_quiz.get("type") != "mcq_quiz":
        raise HTTPException(status_code=400, detail="No active quiz")

    if active_quiz.get("quiz_id") != request.quiz_id:
        raise HTTPException(status_code=400, detail="Quiz id mismatch")

    questions = active_quiz.get("questions")
    if not isinstance(questions, list) or len(questions) == 0:
        raise HTTPException(status_code=400, detail="Quiz is invalid")

    answer_map = {a.question_id: a.answer_id for a in request.answers}
    results = []
    score = 0
    for q in questions:
        qid = q.get("id")
        correct = q.get("answer_id")
        given = answer_map.get(qid)
        is_correct = bool(qid and correct and given and given == correct)
        if is_correct:
            score += 1
        results.append(
            {
                "question_id": qid or "",
                "correct_answer_id": correct,
                "given_answer_id": given,
                "is_correct": is_correct,
            }
        )

    passing_score = active_quiz.get("passing_score")
    passed = None
    if isinstance(passing_score, int):
        passed = score >= passing_score

    # Persist completion + clear active quiz so refresh doesn't strand the user.
    completed = facts.get("completed_quizzes")
    if not isinstance(completed, dict):
        completed = {}
    completed[str(request.quiz_id)] = {
        "score": score,
        "total": len(questions),
        "passed": passed,
        "passing_score": passing_score if isinstance(passing_score, int) else None,
    }
    facts["completed_quizzes"] = completed
    facts.pop("active_quiz", None)
    enrollment.student_facts = facts

    # Append a follow-up message to chat history.
    summary_line = f"Quiz complete: {score}/{len(questions)}"
    if isinstance(passing_score, int):
        summary_line += f" (pass >= {passing_score})"
    if isinstance(passed, bool):
        summary_line += " — PASSED" if passed else " — NOT PASSED"

    followup = {
        "version": 1,
        "mode": "chat",
        "blocks": [
            {
                "type": "markdown",
                "text": f"{summary_line}\n\nType **continue** when you're ready to move on.",
            }
        ],
        "workspace_update": None,
    }
    db.add(models.ChatLog(enrollment_id=enrollment.id, sender="agent", content=json.dumps(followup)))

    db.commit()

    return {
        "quiz_id": request.quiz_id,
        "score": score,
        "total": len(questions),
        "passing_score": passing_score if isinstance(passing_score, int) else None,
        "passed": passed,
        "results": results,
    }


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


@router.post("/chat/reset")
async def chat_reset_endpoint(
    enrollment_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    db.query(models.ChatLog).filter(models.ChatLog.enrollment_id == enrollment_id).delete()
    enrollment.student_facts = {"phase": "awaiting_name"}
    enrollment.current_module_index = 0
    db.commit()

    return {"ok": True}
