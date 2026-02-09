from fastapi import HTTPException
import json
from sqlalchemy.orm import Session

from .. import models
from ..instructors import get_persona_for_agent
from .llm_service import generate_ai_text


_GREETING_TOKENS = {"hi", "hello", "hey", "yo", "sup", "hiya"}

_READY_TOKENS = {
    "yes", "y", "yeah", "yep", "sure", "ok", "okay",
    "ready", "im ready", "i'm ready", "lets go", "let's go", "start",
}


def _normalize_token(text: str) -> str:
    if not isinstance(text, str):
        return ""
    s = text.strip().lower()
    if not s:
        return ""
    return "".join(ch for ch in s if ch.isalnum() or ch.isspace()).strip()


def _looks_like_goal(text: str) -> bool:
    s = _normalize_token(text)
    if len(s) < 3:
        return False
    # Avoid treating readiness confirmations as goals.
    if s in _READY_TOKENS:
        return False
    if s in _GREETING_TOKENS:
        return False
    return True


def _get_phase(facts: dict) -> str:
    phase = (facts.get("phase") or "").strip().lower()
    if phase in {"awaiting_name", "awaiting_ready", "awaiting_goal", "in_module"}:
        return phase
    return "awaiting_name"


def _ensure_phase_initialized(enrollment: models.Enrollment) -> None:
    facts = enrollment.student_facts or {}
    if "phase" not in facts:
        facts["phase"] = "awaiting_name"
        enrollment.student_facts = facts


def _maybe_capture_student_name(enrollment: models.Enrollment, user_message: str) -> None:
    facts = enrollment.student_facts or {}
    phase = _get_phase(facts)
    if phase != "awaiting_name":
        return

    # Guard against previously captured "names" that are actually greetings.
    existing_name = (facts.get("student_name") or "").strip().lower()
    if existing_name in _GREETING_TOKENS:
        facts.pop("student_name", None)

    msg = (user_message or "").strip()
    if not msg:
        return

    msg_norm = _normalize_token(msg)
    if msg_norm in _GREETING_TOKENS:
        return

    # Don't treat readiness confirmations as a goal.
    if msg_norm in _READY_TOKENS:
        return

    # Heuristic: treat short, mostly-alphabetic replies as a name (e.g., "Lydia", "Lydia G").
    if len(msg) > 40:
        return

    cleaned = "".join(ch for ch in msg if ch.isalpha() or ch in [" ", "-", "'"]).strip()
    if not cleaned:
        return

    # Never treat greetings as names (handles cases like "hi!" where punctuation was present).
    if _normalize_token(cleaned) in _GREETING_TOKENS:
        return

    alpha_chars = sum(1 for ch in cleaned if ch.isalpha())
    if alpha_chars < 2:
        return

    msg_lower = msg.lower()
    if any(token in msg_lower for token in ["my name is", "i am ", "i'm "]):
        facts["student_name"] = msg
    else:
        facts["student_name"] = cleaned

    facts["phase"] = "awaiting_ready"
    enrollment.student_facts = facts


def _maybe_advance_ready(enrollment: models.Enrollment, user_message: str) -> None:
    facts = enrollment.student_facts or {}
    phase = _get_phase(facts)
    if phase != "awaiting_ready":
        return

    msg = _normalize_token(user_message or "")
    if not msg:
        return

    if msg in _READY_TOKENS or any(tok in msg for tok in ["i'm ready", "im ready", "let's", "lets"]):
        facts["phase"] = "awaiting_goal"
        enrollment.student_facts = facts

    # Recovery: if the student answered with a real goal while we were still awaiting_ready,
    # accept it and move forward.
    if facts.get("phase") == "awaiting_ready" and _looks_like_goal(user_message):
        facts["financial_goal"] = (user_message or "").strip()
        facts["phase"] = "in_module"
        enrollment.student_facts = facts


def _maybe_capture_goal(enrollment: models.Enrollment, user_message: str) -> None:
    facts = enrollment.student_facts or {}
    phase = _get_phase(facts)
    if phase != "awaiting_goal":
        return

    msg = (user_message or "").strip()
    if not msg:
        return

    # Treat any non-trivial response as the student's goal.
    if not _looks_like_goal(msg):
        return
    facts["financial_goal"] = msg
    facts["phase"] = "in_module"
    enrollment.student_facts = facts


def _render_state_block(enrollment: models.Enrollment) -> str:
    facts = enrollment.student_facts or {}
    phase = _get_phase(facts)
    intro_complete = phase in {"awaiting_goal", "in_module"}
    student_name = facts.get("student_name")
    financial_goal = facts.get("financial_goal")

    lines = [
        "STATE (authoritative; do not contradict):",
        f"- phase: {phase}",
        f"- intro_complete: {str(intro_complete).lower()}",
        f"- student_name: {student_name if student_name else '(unknown)'}",
        f"- financial_goal: {financial_goal if financial_goal else '(unknown)'}",
        "RULES:",
        "- If intro_complete=true, DO NOT repeat the full intro / onboarding script.",
        "- If student_name is known, address the student by name.",
        "PHASE RULES (non-negotiable):",
        "- If phase=awaiting_name: ask ONLY for the student's name. Do NOT ask if they are ready. Do NOT ask their goal. Do NOT start Module 1.",
        "- If phase=awaiting_ready: ask ONLY if they are ready to begin. Do NOT ask their goal. Do NOT start Module 1.",
        "- If phase=awaiting_goal: ask ONLY for their biggest financial goal right now. Do NOT start Module 1 until they answer.",
        "- If phase=in_module: continue the lesson flow and avoid onboarding questions.",
    ]
    return "\n".join(lines)


def _onboarding_payload_for_phase(enrollment: models.Enrollment) -> dict:
    facts = enrollment.student_facts or {}
    phase = _get_phase(facts)
    student_name = facts.get("student_name")

    if phase == "awaiting_name":
        text = "What should I call you?"
    elif phase == "awaiting_ready":
        name_part = f" {student_name}" if student_name else ""
        text = f"Nice to meet you{name_part}. Are you ready to begin?"
    elif phase == "awaiting_goal":
        text = "What's your biggest financial goal right now?"
    else:
        text = ""

    return {
        "version": 1,
        "mode": "chat",
        "blocks": [{"type": "markdown", "text": text}],
        "workspace_update": None,
    }


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


def _extract_json_payload(text: str):
    if not isinstance(text, str):
        return None

    stripped = text.strip()
    if not stripped:
        return None

    # Common case: model wraps JSON in markdown fences.
    if "```" in stripped:
        start = stripped.find("```")
        if start != -1:
            end = stripped.rfind("```")
            if end != -1 and end > start:
                inner = stripped[start + 3 : end].strip()
                if inner.lower().startswith("json"):
                    inner = inner[4:].strip()
                stripped = inner

    # Fallback: try to extract the first JSON object inside the text.
    if not stripped.startswith("{"):
        first = stripped.find("{")
        last = stripped.rfind("}")
        if first != -1 and last != -1 and last > first:
            stripped = stripped[first : last + 1]

    try:
        return json.loads(stripped)
    except Exception:
        return None


def handle_chat(db: Session, enrollment_id: int, user_message: str):
    enrollment, course, agent, modules, current_mod = _get_enrollment_context(db, enrollment_id)

    _ensure_phase_initialized(enrollment)

    # Only allow ONE phase transition per user message to avoid misclassifying
    # short confirmations (e.g., "yes") as a goal.
    phase_before = _get_phase(enrollment.student_facts or {})
    if phase_before == "awaiting_name":
        _maybe_capture_student_name(enrollment=enrollment, user_message=user_message)
    elif phase_before == "awaiting_ready":
        _maybe_advance_ready(enrollment=enrollment, user_message=user_message)
    elif phase_before == "awaiting_goal":
        _maybe_capture_goal(enrollment=enrollment, user_message=user_message)

    # Deterministic onboarding: do not call the model until we are in_module.
    phase_after = _get_phase(enrollment.student_facts or {})
    if phase_after in {"awaiting_name", "awaiting_ready", "awaiting_goal"}:
        payload = _onboarding_payload_for_phase(enrollment)
        return enrollment, payload, None

    persona = get_persona_for_agent(agent.id)
    persona_instructions = persona.system_instructions if persona else ""

    state_block = _render_state_block(enrollment)

    system_instruction = f"""
    {persona_instructions}

    {state_block}

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

    OUTPUT FORMAT (NON-NEGOTIABLE):
    - You MUST output ONLY valid JSON.
    - Top-level JSON object MUST contain: version (number), mode (string), blocks (array).
    - Each block MUST be an object with a "type".
    - For normal text, return a block: {{"type":"markdown","text":"..."}}
    - When you want an interactive quiz, include a block with type "mcq_quiz" and fields:
      quiz_id (string), title (string), passing_score (number), questions (array).
      Each question: id (string), prompt (string), options (array of {{id,text}}), answer_id (string).
    - Do NOT wrap JSON in markdown fences. Do NOT include any other text.
    """

    ai_text = generate_ai_text(system_instruction=system_instruction, user_message=user_message, current_mod=current_mod)

    parsed = _extract_json_payload(ai_text)
    if parsed is None:
        parsed = {
            "version": 1,
            "mode": "chat",
            "blocks": [{"type": "markdown", "text": ai_text}],
        }

    blocks = parsed.get("blocks") if isinstance(parsed, dict) else None
    if not isinstance(blocks, list):
        parsed = {
            "version": 1,
            "mode": "chat",
            "blocks": [{"type": "markdown", "text": ai_text}],
        }
        blocks = parsed["blocks"]

    # Store active quiz (practice) if present.
    active_quiz = None
    for block in blocks:
        if isinstance(block, dict) and block.get("type") == "mcq_quiz":
            active_quiz = block
            break
    if active_quiz:
        facts = enrollment.student_facts or {}
        facts["active_quiz"] = active_quiz
        enrollment.student_facts = facts

    workspace_update = None
    module_complete = False
    for block in blocks:
        if isinstance(block, dict) and block.get("type") == "markdown":
            text = block.get("text") or ""
            if "[MODULE_COMPLETE]" in text:
                module_complete = True
                block["text"] = text.replace("[MODULE_COMPLETE]", "")

    if module_complete:
        next_index = enrollment.current_module_index + 1
        if next_index < len(modules):
            next_mod = modules[next_index]
            workspace_update = {
                "status": "unlocked",
                "next_module": next_mod["title"],
                "objective": next_mod["objective"],
            }
            enrollment.current_module_index = next_index

    parsed["workspace_update"] = workspace_update
    return enrollment, parsed, workspace_update
