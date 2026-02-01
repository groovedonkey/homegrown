from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db
from .. import models


router = APIRouter()


@router.get("/enrollments")
def list_enrollments(db: Session = Depends(get_db)):
    enrollments = db.query(models.Enrollment).all()

    results = []
    for e in enrollments:
        course = e.course
        agent = course.agent if course else None

        curriculum = getattr(course, "curriculum_json", None) if course else None
        modules = curriculum.get("modules") if isinstance(curriculum, dict) else None
        total_modules = len(modules) if isinstance(modules, list) else None
        current_mod = None
        if isinstance(modules, list) and 0 <= e.current_module_index < len(modules):
            current_mod = modules[e.current_module_index]

        results.append(
            {
                "enrollment_id": e.id,
                "course_id": getattr(course, "id", None),
                "course_title": getattr(course, "title", None),
                "agent_name": getattr(agent, "name", None),
                "current_module_index": e.current_module_index,
                "total_modules": total_modules,
                "current_module_title": current_mod.get("title") if isinstance(current_mod, dict) else None,
                "current_module_objective": current_mod.get("objective") if isinstance(current_mod, dict) else None,
            }
        )

    return results
