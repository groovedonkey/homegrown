from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from . import models, database
from .database import SessionLocal
from .routers.chat import router as chat_router
from .routers.enrollments import router as enrollments_router
from .routers.uploads import router as uploads_router

# Init Environment
load_dotenv(override=True)

app = FastAPI(title="Homegrown API")

# --- CORS SETUP ---
cors_allow_origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
allow_origins = ["*"] if cors_allow_origins.strip() == "*" else [o.strip() for o in cors_allow_origins.split(",") if o.strip()]
allow_credentials = False if allow_origins == ["*"] else True
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")
app.include_router(enrollments_router, prefix="/api")
app.include_router(uploads_router, prefix="/api")


@app.get("/api/health")
def healthcheck():
    return {"ok": True}

# --- Initialization ---
@app.on_event("startup")
def startup():
    models.Base.metadata.create_all(bind=database.engine)

    # Idempotent local seed: ensure default instructors/courses exist.
    db = SessionLocal()
    try:
        def upsert_agent(agent_id: str, name: str, system_prompt_core: str):
            agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
            if not agent:
                agent = models.Agent(id=agent_id, name=name, system_prompt_core=system_prompt_core)
                db.add(agent)
            else:
                if not agent.name:
                    agent.name = name
                if not agent.system_prompt_core:
                    agent.system_prompt_core = system_prompt_core
            return agent

        def upsert_course(course_id: str, title: str, agent_id: str, curriculum_json: dict):
            course = db.query(models.Course).filter(models.Course.id == course_id).first()
            if not course:
                course = models.Course(id=course_id, title=title, agent_id=agent_id, curriculum_json=curriculum_json)
                db.add(course)
            else:
                if not course.title:
                    course.title = title
                if not course.agent_id:
                    course.agent_id = agent_id
                if not course.curriculum_json:
                    course.curriculum_json = curriculum_json
            return course

        daisy = upsert_agent(
            "daisy_dollars",
            "Daisy Dollars",
            "You are Daisy Dollars. You are a strict but encouraging finance teacher.",
        )
        barnaby = upsert_agent(
            "bistro_barnaby",
            "Bistro Barnaby",
            "You are Bistro Barnaby, a witty culinary instructor who teaches cooking fundamentals and kitchen safety.",
        )
        tera = upsert_agent(
            "tera_byte",
            "Tera Byte",
            "You are Tera Byte, an energetic and precise coding tutor.",
        )

        daisy_course = upsert_course(
            "finance_101",
            "Personal Finance 101",
            daisy.id,
            {
                "modules": [
                    {
                        "id": "mod_1",
                        "title": "Income",
                        "objective": "Categorize transactions.",
                        "success_criteria": "Identify Rent as fixed.",
                    }
                ]
            },
        )
        barnaby_course = upsert_course(
            "culinary_101",
            "Culinary Basics 101",
            barnaby.id,
            {
                "modules": [
                    {
                        "id": "cook_1",
                        "title": "Kitchen Safety",
                        "objective": "Identify basic kitchen safety rules and safe knife handling.",
                        "success_criteria": "Student lists at least 3 safety rules.",
                    }
                ]
            },
        )
        tera_course = upsert_course(
            "html_hero",
            "HTML Hero: Building the Web",
            tera.id,
            {
                "modules": [
                    {
                        "id": "html_1",
                        "title": "The Skeleton of the Web",
                        "objective": "Write a basic HTML structure with <html>, <head>, and <body> tags.",
                        "success_criteria": "Student writes valid boilerplate.",
                    },
                    {
                        "id": "html_2",
                        "title": "Tags & Elements",
                        "objective": "Create a paragraph <p> and a heading <h1>.",
                        "success_criteria": "Student uses tags correctly.",
                    },
                ]
            },
        )

        student = db.query(models.User).filter(models.User.role == "student").order_by(models.User.id.asc()).first()
        if not student:
            student = models.User(email="student@homegrown.local", role="student", display_name="Student")
            db.add(student)
            db.flush()

        def ensure_enrollment(course: models.Course):
            existing = (
                db.query(models.Enrollment)
                .filter(models.Enrollment.student_id == student.id, models.Enrollment.course_id == course.id)
                .first()
            )
            if not existing:
                db.add(models.Enrollment(student=student, course=course, current_module_index=0))

        ensure_enrollment(daisy_course)
        ensure_enrollment(barnaby_course)
        ensure_enrollment(tera_course)

        db.commit()
    finally:
        db.close()