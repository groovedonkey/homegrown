from fastapi import APIRouter, Depends, HTTPException
from urllib.parse import quote
from sqlalchemy.orm import Session

from ..deps import get_db
from .. import models


router = APIRouter()


def _enrollment_summary(e: models.Enrollment):
    course = e.course
    agent = course.agent if course else None

    curriculum = getattr(course, "curriculum_json", None) if course else None
    modules = curriculum.get("modules") if isinstance(curriculum, dict) else None
    total_modules = len(modules) if isinstance(modules, list) else None
    current_mod = None
    if isinstance(modules, list) and 0 <= e.current_module_index < len(modules):
        current_mod = modules[e.current_module_index]

    return {
        "enrollment_id": e.id,
        "course_id": getattr(course, "id", None),
        "course_title": getattr(course, "title", None),
        "agent_id": getattr(agent, "id", None),
        "agent_name": getattr(agent, "name", None),
        "current_module_index": e.current_module_index,
        "total_modules": total_modules,
        "current_module_title": current_mod.get("title") if isinstance(current_mod, dict) else None,
        "current_module_objective": current_mod.get("objective") if isinstance(current_mod, dict) else None,
    }


@router.get("/enrollments")
def list_enrollments(db: Session = Depends(get_db)):
    enrollments = db.query(models.Enrollment).all()

    results = []
    for e in enrollments:
        results.append(_enrollment_summary(e))

    return results


@router.get("/instructors")
def list_instructors(db: Session = Depends(get_db)):
    agents = db.query(models.Agent).order_by(models.Agent.name).all()
    results = []
    for a in agents:
        avatar_url = f"/api/avatars/{quote(a.name)}.png"
        results.append({"agent_id": a.id, "agent_name": a.name, "avatar_url": avatar_url})
    return results


@router.get("/instructors/{agent_id}/courses")
def list_courses_for_instructor(agent_id: str, db: Session = Depends(get_db)):
    courses = db.query(models.Course).filter(models.Course.agent_id == agent_id).order_by(models.Course.title).all()
    return [{"course_id": c.id, "course_title": c.title, "agent_id": agent_id} for c in courses]


@router.get("/instructors/{agent_id}/intro")
def instructor_intro(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Instructor not found")

    # Try to load a custom intro from the Teacher Intros folder.
    from ..services.teacherbots_service import _find_teacherbots_root
    root = _find_teacherbots_root()
    if root:
        intro_file = root / "Teacher Intros" / f"{agent.name}.txt"
        if intro_file.exists() and intro_file.is_file():
            return {"intro": intro_file.read_text(encoding="utf-8", errors="ignore").strip()}

    # Fallback placeholder for instructors without a custom intro yet.
    return {"intro": f"Hi! I'm {agent.name}. My introduction is coming soon — stay tuned!"}


@router.post("/classroom/enter")
def enter_classroom(agent_id: str, course_id: str, db: Session = Depends(get_db)):
    # Prototype auth: use the first student.
    student = db.query(models.User).filter(models.User.role == "student").order_by(models.User.id.asc()).first()
    if not student:
        raise HTTPException(status_code=400, detail="No student exists. Seed the database first.")

    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course or course.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Course not found for instructor")

    enrollment = (
        db.query(models.Enrollment)
        .filter(models.Enrollment.student_id == student.id, models.Enrollment.course_id == course_id)
        .first()
    )
    if not enrollment:
        enrollment = models.Enrollment(student=student, course=course, current_module_index=0)
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)

    return _enrollment_summary(enrollment)
