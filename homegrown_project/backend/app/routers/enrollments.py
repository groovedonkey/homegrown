from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db
from .. import models
from ..services.teacherbots_service import (
    get_instructor,
    get_course,
    list_courses_for_instructor as tb_list_courses_for_instructor,
    list_instructors as tb_list_instructors,
    make_db_agent_and_course_fields,
)
from ..services.llm_service import generate_ai_text


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
    instructors = tb_list_instructors()
    return [{"agent_id": i.instructor_id, "agent_name": i.instructor_name} for i in instructors]


@router.get("/instructors/{agent_id}/courses")
def list_courses_for_instructor(agent_id: str, db: Session = Depends(get_db)):
    courses = tb_list_courses_for_instructor(agent_id)
    results = []
    inst = get_instructor(agent_id)
    for c in courses:
        if inst:
            _, _, db_course_id, _ = make_db_agent_and_course_fields(inst, c)
            results.append({"course_id": db_course_id, "course_title": c.course_title, "agent_id": agent_id})
        else:
            results.append({"course_id": c.course_id, "course_title": c.course_title, "agent_id": agent_id})
    return results


@router.get("/instructors/{agent_id}/intro")
def instructor_intro(agent_id: str):
    inst = get_instructor(agent_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instructor not found")

    system_instruction = (
        "You are generating a short introduction message for a student who just selected an instructor. "
        "Write in the instructor's voice based on the ROLE/PERSONA below. "
        "Keep it to 3-6 sentences. End with one friendly question.\n\n"
        "PERSONA:\n"
        f"{inst.main_persona_text.strip()}\n"
    )
    try:
        text = generate_ai_text(system_instruction, "Introduce yourself to the student.", current_mod={})
        return {"intro": text}
    except Exception:
        # Fallback: derive a short intro from the persona text.
        raw = (inst.main_persona_text or "").strip()
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        role_line = ""
        for ln in lines[:10]:
            if ln.lower().startswith("role") or "role:" in ln.lower():
                role_line = ln
                break
        name = inst.instructor_name
        base = f"Hi! I’m {name}."
        extra = f" {role_line}" if role_line and role_line.lower() != "role" else ""
        return {"intro": f"{base}{extra} Ready to get started?"}


@router.post("/classroom/enter")
def enter_classroom(agent_id: str, course_id: str, db: Session = Depends(get_db)):
    # Prototype auth: use the first student.
    student = db.query(models.User).filter(models.User.role == "student").order_by(models.User.id.asc()).first()
    if not student:
        raise HTTPException(status_code=400, detail="No student exists. Seed the database first.")

    db_course_id = course_id
    if "__" not in course_id:
        inst = get_instructor(agent_id)
        c = get_course(agent_id, course_id)
        if not inst or not c:
            raise HTTPException(status_code=404, detail="Course not found for instructor")
        _, _, db_course_id, _ = make_db_agent_and_course_fields(inst, c)

    course = db.query(models.Course).filter(models.Course.id == db_course_id).first()
    if not course:
        inst = get_instructor(agent_id)
        if not inst:
            raise HTTPException(status_code=404, detail="Instructor not found")

        # Ensure Agent exists
        agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
        if not agent:
            agent = models.Agent(id=agent_id, name=inst.instructor_name, system_prompt_core=inst.main_persona_text)
            db.add(agent)

        # Best-effort course title from TeacherBots
        title = db_course_id
        tb_course_id = course_id.split("__", 1)[1] if "__" in course_id else course_id
        tb_course = get_course(agent_id, tb_course_id)
        if tb_course:
            title = tb_course.course_title

        course = models.Course(
            id=db_course_id,
            title=title,
            agent_id=agent_id,
            curriculum_json={
                "modules": [
                    {
                        "id": "mod_1",
                        "title": "Course Start",
                        "objective": "Review the course introduction and begin your first lesson.",
                        "success_criteria": "Student confirms they are ready to start.",
                    }
                ]
            },
        )
        db.add(course)
        db.commit()
        db.refresh(course)

    if course.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Course not found for instructor")

    enrollment = (
        db.query(models.Enrollment)
        .filter(models.Enrollment.student_id == student.id, models.Enrollment.course_id == db_course_id)
        .first()
    )
    if not enrollment:
        enrollment = models.Enrollment(student=student, course=course, current_module_index=0)
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)

    return _enrollment_summary(enrollment)
