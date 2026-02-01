import os
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db
from .. import models


router = APIRouter()


@router.post("/uploads")
async def upload_file(
    enrollment_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    uploads_dir = os.getenv("HOMEGROWN_UPLOADS_DIR")
    if not uploads_dir:
        uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")
        uploads_dir = os.path.abspath(uploads_dir)

    os.makedirs(uploads_dir, exist_ok=True)

    safe_name = os.path.basename(file.filename or "upload")
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    stored_name = f"{enrollment_id}_{timestamp}_{safe_name}"
    stored_path = os.path.join(uploads_dir, stored_name)

    contents = await file.read()
    with open(stored_path, "wb") as f:
        f.write(contents)

    db.add(
        models.ChatLog(
            enrollment_id=enrollment_id,
            sender="system",
            content=f"[FILE_UPLOADED] {stored_name} ({file.content_type}, {len(contents)} bytes)",
        )
    )
    db.commit()

    return {
        "ok": True,
        "enrollment_id": enrollment_id,
        "filename": safe_name,
        "stored_name": stored_name,
        "content_type": file.content_type,
        "bytes": len(contents),
    }
