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

print("Seeding Agents & Courses...")

# --- AGENT 1: DAISY (Finance) ---
daisy = models.Agent(
    id="daisy_dollars",
    name="Daisy Dollars", 
    system_prompt_core="You are Daisy Dollars. You are a strict but encouraging finance teacher."
)

daisy_course = models.Course(
    id="finance_101", 
    title="Money 101", 
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

# --- AGENT 2: TERA BYTE (Coding) ---
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
# Enroll Lydia in BOTH classes
enrollment_daisy = models.Enrollment(
    student=student, 
    course=daisy_course, 
    current_module_index=0
)

enrollment_tera = models.Enrollment(
    student=student, 
    course=tera_course, 
    current_module_index=0
)

db.add(daisy)
db.add(daisy_course)
db.add(tera)
db.add(tera_course)
db.add(student)
db.add(enrollment_daisy)
db.add(enrollment_tera)

db.commit()

print("Seed Complete! Daisy AND Tera are ready.")
db.close()