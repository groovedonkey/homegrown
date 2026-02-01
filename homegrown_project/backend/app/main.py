from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional  # <--- Added this for Python 3.9 compatibility
import google.generativeai as genai
import os
from dotenv import load_dotenv

from . import models, database

# Init Environment
load_dotenv(override=True)

# Configure the API Key
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

app = FastAPI(title="Homegrown API")

# --- CORS SETUP ---
cors_allow_origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
allow_origins = ["*"] if cors_allow_origins.strip() == "*" else [o.strip() for o in cors_allow_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Schemas (Input/Output) ---
class ChatRequest(BaseModel):
    enrollment_id: int
    message: str

class ChatResponse(BaseModel):
    agent_response: str
    # CHANGED: "dict | None" -> "Optional[dict]" for Python 3.9 support
    workspace_update: Optional[dict] = None 

# --- The Brain ---
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    
    # 1. Fetch Context
    enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == request.enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    if not enrollment.course:
         raise HTTPException(status_code=500, detail="Course data missing")

    course = enrollment.course
    agent = course.agent
    
    if not agent:
         raise HTTPException(status_code=500, detail="Agent data missing")
    
    # 2. Get Current Module Data
    syllabus = course.curriculum_json
    if not isinstance(syllabus, dict):
        raise HTTPException(status_code=500, detail="Course curriculum is invalid")

    modules = syllabus.get("modules")
    if not isinstance(modules, list) or len(modules) == 0:
        raise HTTPException(status_code=500, detail="Course curriculum has no modules")

    if enrollment.current_module_index < 0 or enrollment.current_module_index >= len(modules):
        raise HTTPException(status_code=500, detail="Enrollment module index is out of range")

    current_mod = modules[enrollment.current_module_index]
    
    # 3. Construct the Mega-Prompt
    system_instruction = f"""
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

    def _dev_fallback_response() -> str:
        msg_lower = request.message.strip().lower()
        if any(token in msg_lower for token in ["done", "completed", "finish", "finished", "i did it", "module complete"]):
            return f"Nice work — you met the objective for '{current_mod.get('title', 'this module')}'. [MODULE_COMPLETE]"

        objective = current_mod.get("objective")
        if objective:
            return f"Let's focus on the objective: {objective} What would you like to try next?"
        return "Tell me what you tried, and I'll guide your next step."
    
    # 4. Call Gemini
    try:
        dev_fallback_enabled = os.getenv("HOMEGROWN_DEV_FALLBACK", "0") == "1"
        if dev_fallback_enabled:
            ai_text = _dev_fallback_response()
            raise StopIteration
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        model_name = os.getenv("GEMINI_MODEL", "gemini-pro-latest")
        model = genai.GenerativeModel(model_name)
        full_prompt = f"{system_instruction}\n\nUser: {request.message}"
        response = model.generate_content(full_prompt)
        ai_text = response.text
    except StopIteration:
        pass
    except Exception as e:
        err_text = str(e)
        if "429" in err_text or "quota" in err_text.lower() or "rate" in err_text.lower():
            ai_text = _dev_fallback_response()
        else:
            ai_text = f"I'm having trouble connecting to my brain right now. (Error: {err_text})"

    # 5. Check for State Change
    workspace_update = None
    if "[MODULE_COMPLETE]" in ai_text:
        next_index = enrollment.current_module_index + 1
        if next_index < len(modules):
             next_mod = modules[next_index]
             workspace_update = {
                 "status": "unlocked", 
                 "next_module": next_mod['title'],
                 "objective": next_mod['objective']
             }
             enrollment.current_module_index = next_index
             db.commit()
             
        ai_text = ai_text.replace("[MODULE_COMPLETE]", "")

    return {"agent_response": ai_text, "workspace_update": workspace_update}

# --- Initialization ---
@app.on_event("startup")
def startup():
    models.Base.metadata.create_all(bind=database.engine)