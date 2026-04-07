from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from . import models, database
from .database import SessionLocal
from .routers.chat import router as chat_router
from .routers.enrollments import router as enrollments_router
from .routers.uploads import router as uploads_router

# Init Environment
load_dotenv(override=True)


def _find_teacherbot_avatars_dir() -> Optional[Path]:
    here = Path(__file__).resolve()
    for parent in [here] + list(here.parents):
        candidate = parent / "TeacherBots" / "Teacherbot Avatars"
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


# --- Initialization ---
def _run_startup_seed():
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
        lexi = upsert_agent(
            "lexi_lingo",
            "Lexi Lingo",
            "You are Lexi Lingo, a sharp and encouraging language arts teacher who makes grammar and writing feel approachable.",
        )
        coach = upsert_agent(
            "coach_kinetic",
            "Coach Kinetic",
            "You are Coach Kinetic, a tough but motivating sports and physical education coach who pushes students to be their best.",
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
        tera_html_basics = upsert_course(
            "html_basics",
            "HTML Basics",
            tera.id,
            {
                "modules": [
                    {
                        "id": "htmlb_1",
                        "title": "Boot Up (Setup)",
                        "objective": "Install VS Code, Live Server extension, create project folder and index.html.",
                        "success_criteria": "Student has VS Code open with a my-website folder containing index.html.",
                    },
                    {
                        "id": "htmlb_2",
                        "title": "The Skeleton (HTML Boilerplate)",
                        "objective": "Type out the HTML boilerplate and launch Live Server.",
                        "success_criteria": "Student has a valid boilerplate and sees a blank page in the browser.",
                    },
                    {
                        "id": "htmlb_3",
                        "title": "Filling the World (Core HTML Tags)",
                        "objective": "Learn and use headings, paragraphs, strong, em, br, hr, links, images, and lists.",
                        "success_criteria": "Student demonstrates each tag on their page and can explain what it does.",
                    },
                    {
                        "id": "htmlb_4",
                        "title": "Style Power-Ups (Inline Styling)",
                        "objective": "Apply inline styles using color, background-color, font-size, text-align, and font-family.",
                        "success_criteria": "Student has at least 3 inline style properties applied to different elements.",
                    },
                    {
                        "id": "htmlb_5",
                        "title": "Final Boss: Launch Your Page",
                        "objective": "Build a complete About Me page with a heading, bio, list, image, link, and inline styles.",
                        "success_criteria": "Student submits a working About Me page that uses all learned concepts.",
                    },
                ]
            },
        )
        coach_course = upsert_course(
            "sports_101",
            "Sports Fundamentals",
            coach.id,
            {
                "modules": [
                    {
                        "id": "sport_1",
                        "title": "Warm-Up & Safety",
                        "objective": "Understand the importance of warming up and learn proper stretching techniques.",
                        "success_criteria": "Student describes a complete warm-up routine and explains why it prevents injury.",
                    },
                    {
                        "id": "sport_2",
                        "title": "Teamwork & Strategy",
                        "objective": "Learn the basics of team coordination, positioning, and game strategy.",
                        "success_criteria": "Student explains key roles on a team and diagrams a basic play.",
                    },
                ]
            },
        )
        lexi_course = upsert_course(
            "grammar_101",
            "Grammar Fundamentals",
            lexi.id,
            {
                "modules": [
                    {
                        "id": "gram_1",
                        "title": "Parts of Speech",
                        "objective": "Identify and classify nouns, verbs, adjectives, and adverbs in sentences.",
                        "success_criteria": "Student correctly labels parts of speech in sample sentences.",
                    },
                    {
                        "id": "gram_2",
                        "title": "Sentence Structure",
                        "objective": "Construct simple, compound, and complex sentences.",
                        "success_criteria": "Student writes examples of each sentence type.",
                    },
                ]
            },
        )
        lexi_ggb1_course = upsert_course(
            "great_grammar_basic_1",
            "Great Grammar Basic Module 1",
            lexi.id,
            {
                "modules": [
                    {
                        "id": "ggb_1",
                        "title": "The Power Move",
                        "objective": "Master nouns, verbs, and active voice as the foundations of powerful US English writing.",
                        "success_criteria": "Student scores 8/10 or higher on the 10-question Flex Gate quiz covering nouns, verbs, and active voice.",
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
        ensure_enrollment(tera_html_basics)
        ensure_enrollment(lexi_course)
        ensure_enrollment(lexi_ggb1_course)
        ensure_enrollment(coach_course)

        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _run_startup_seed()
    yield


app = FastAPI(title="Homegrown API", lifespan=lifespan)

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

_avatars_dir = _find_teacherbot_avatars_dir()
if _avatars_dir:
    app.mount("/api/avatars", StaticFiles(directory=str(_avatars_dir)), name="avatars")


@app.get("/api/health")
def healthcheck():
    return {"ok": True}