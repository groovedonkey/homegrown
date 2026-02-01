from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..instructors import get_persona_for_agent
from .llm_service import generate_ai_text


def _get_enrollment_context(db: Session, enrollment_id: int):
    enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    if not enrollment.course:
        raise HTTPException(status_code=500, detail="Course data missing")

    course = enrollment.course
    agent = course.agent

    if not agent:
        raise HTTPException(status_code=500, detail="Agent data missing")

    syllabus = course.curriculum_json
    if not isinstance(syllabus, dict):
        raise HTTPException(status_code=500, detail="Course curriculum is invalid")

    modules = syllabus.get("modules")
    if not isinstance(modules, list) or len(modules) == 0:
        raise HTTPException(status_code=500, detail="Course curriculum has no modules")

    if enrollment.current_module_index < 0 or enrollment.current_module_index >= len(modules):
        raise HTTPException(status_code=500, detail="Enrollment module index is out of range")

    current_mod = modules[enrollment.current_module_index]

    return enrollment, course, agent, modules, current_mod


def handle_chat(db: Session, enrollment_id: int, user_message: str):
    enrollment, course, agent, modules, current_mod = _get_enrollment_context(db, enrollment_id)

    persona = get_persona_for_agent(agent.id)
    persona_instructions = persona.system_instructions if persona else ""

    system_instruction = f"""
    {persona_instructions}

    You are {agent.name}. 
    Your Core Personality: {agent.system_prompt_core}

    CURRENT CONTEXT:
    Student is working on Course: {course.title}
    Current Module: {current_mod['title']}
    Objective: {current_mod['objective']}
    Student Facts: {enrollment.student_facts}

    INSTRUCTIONS:
    - Keep responses short (under 3 sentences) unless explaining a complex concept.
    - If the student completes the objective, add [MODULE_COMPLETE] to your response.
    """

    ai_text = generate_ai_text(system_instruction=system_instruction, user_message=user_message, current_mod=current_mod)

    workspace_update = None
    if "[MODULE_COMPLETE]" in ai_text:
        next_index = enrollment.current_module_index + 1
        if next_index < len(modules):
            next_mod = modules[next_index]
            workspace_update = {
                "status": "unlocked",
                "next_module": next_mod["title"],
                "objective": next_mod["objective"],
            }
            enrollment.current_module_index = next_index

        ai_text = ai_text.replace("[MODULE_COMPLETE]", "")

    return enrollment, ai_text, workspace_update
