import sys
import os

# 1. Setup Path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from backend.app.database import SessionLocal, engine, Base
from backend.app import models

# 2. THE NUCLEAR OPTION: Auto-delete the old DB to prevent conflicts
db_path = os.path.join(current_dir, "app", "homegrown.db")
if os.path.exists(db_path):
    print(f"Removing old database at {db_path}...")
    os.remove(db_path)

# 3. Create Tables
print("Creating new database tables...")
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    print("Seeding Agents & Courses...")

    # --- AGENT 1: DAISY (Finance) ---
    daisy = models.Agent(
        id="daisy_dollars",
        name="Daisy Dollars", 
        system_prompt_core="You are Daisy Dollars. You are a strict but encouraging finance teacher."
    )

    daisy_course = models.Course(
        id="finance_101", 
        title="Personal Finance 101", 
        agent_id="daisy_dollars",
        curriculum_json={
            "modules": [{
                "id": "mod_1", 
                "title": "Income", 
                "objective": "Categorize transactions.",
                "success_criteria": "Identify Rent as fixed."
            }]
        }
    )

    # --- AGENT 2: BISTRO BARNABY (Culinary) ---
    barnaby = models.Agent(
        id="bistro_barnaby",
        name="Bistro Barnaby",
        system_prompt_core="You are Bistro Barnaby, a witty culinary instructor who teaches cooking fundamentals and kitchen safety.",
    )

    barnaby_course = models.Course(
        id="culinary_101",
        title="Culinary Basics 101",
        agent_id="bistro_barnaby",
        curriculum_json={
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

    # --- AGENT 3: TERA BYTE (Coding) ---
    tera = models.Agent(
        id="tera_byte",
        name="Tera Byte",
        system_prompt_core="You are Tera Byte, an energetic and precise coding tutor. You love clean code and explaining HTML tags like they are building blocks. You use emojis often 🧱🚀."
    )

    tera_course = models.Course(
        id="html_hero",
        title="HTML Hero: Building the Web",
        agent_id="tera_byte",
        curriculum_json={
            "modules": [
                {
                    "id": "html_1",
                    "title": "The Skeleton of the Web",
                    "objective": "Write a basic HTML structure with <html>, <head>, and <body> tags.",
                    "success_criteria": "Student writes valid boilerplate."
                },
                {
                    "id": "html_2",
                    "title": "Tags & Elements",
                    "objective": "Create a paragraph <p> and a heading <h1>.",
                    "success_criteria": "Student uses tags correctly."
                }
            ]
        }
    )

    # --- STUDENT ---
    student = models.User(
        email="lydia@homegrown.com", 
        role="student", 
        display_name="Lydia"
    )

    # --- ENROLLMENTS ---
    # Enroll Lydia in ALL classes
    enrollment_daisy = models.Enrollment(
        student=student, 
        course=daisy_course, 
        current_module_index=0
    )

    enrollment_barnaby = models.Enrollment(
        student=student,
        course=barnaby_course,
        current_module_index=0
    )

    enrollment_tera = models.Enrollment(
        student=student, 
        course=tera_course, 
        current_module_index=0
    )

    db.add_all([
        daisy, daisy_course,
        barnaby, barnaby_course,
        tera, tera_course,
        student,
        enrollment_daisy, enrollment_barnaby, enrollment_tera,
    ])

    db.commit()
    print("Seed Complete! Daisy, Barnaby, and Tera are ready.")
finally:
    db.close()