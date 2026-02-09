import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class TeacherBotInstructor:
    instructor_id: str
    instructor_name: str
    main_persona_text: str


@dataclass(frozen=True)
class TeacherBotCourse:
    course_id: str
    course_title: str
    source_path: str


def _slugify(value: str) -> str:
    s = value.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "course"


def _find_teacherbots_root() -> Optional[Path]:
    env = os.getenv("HOMEGROWN_TEACHERBOTS_PATH")
    if env:
        p = Path(env).expanduser().resolve()
        if p.exists() and p.is_dir():
            return p

    here = Path(__file__).resolve()
    for parent in [here] + list(here.parents):
        candidate = parent / "TeacherBots"
        if candidate.exists() and candidate.is_dir():
            return candidate

    return None


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _find_main_persona_file(root: Path, instructor_folder_name: str) -> Optional[Path]:
    main_dir = root / "Main Personas"
    candidates: List[Path] = []

    if main_dir.exists() and main_dir.is_dir():
        stem_lower = instructor_folder_name.strip().lower()
        for p in main_dir.iterdir():
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".txt", ".md"}:
                continue
            if stem_lower in p.stem.lower():
                candidates.append(p)

    if candidates:
        return sorted(candidates, key=lambda x: x.name.lower())[0]

    fallback = root / instructor_folder_name / "Persona.txt"
    if fallback.exists() and fallback.is_file():
        return fallback

    return None


def list_instructors() -> List[TeacherBotInstructor]:
    root = _find_teacherbots_root()
    if not root:
        return []

    results: List[TeacherBotInstructor] = []
    for p in root.iterdir():
        if not p.is_dir():
            continue
        if p.name.startswith("."):
            continue
        if p.name.lower() == "main personas":
            continue

        main_path = _find_main_persona_file(root, p.name)
        main_text = _read_text_file(main_path) if main_path else ""

        instructor_name = p.name
        instructor_id = _slugify(p.name)
        results.append(
            TeacherBotInstructor(
                instructor_id=instructor_id,
                instructor_name=instructor_name,
                main_persona_text=main_text,
            )
        )

    results.sort(key=lambda x: x.instructor_name.lower())
    return results


def get_instructor(instructor_id: str) -> Optional[TeacherBotInstructor]:
    for inst in list_instructors():
        if inst.instructor_id == instructor_id:
            return inst
    return None


def list_courses_for_instructor(instructor_id: str) -> List[TeacherBotCourse]:
    root = _find_teacherbots_root()
    if not root:
        return []

    inst = get_instructor(instructor_id)
    if not inst:
        return []

    instructor_dir = root / inst.instructor_name
    if not instructor_dir.exists() or not instructor_dir.is_dir():
        return []

    courses: List[TeacherBotCourse] = []

    for entry in instructor_dir.iterdir():
        if entry.is_dir():
            if entry.name.startswith("."):
                continue
            course_title = entry.name
            course_id = _slugify(course_title)
            courses.append(
                TeacherBotCourse(
                    course_id=course_id,
                    course_title=course_title,
                    source_path=str(entry),
                )
            )
        elif entry.is_file():
            if entry.name.startswith("."):
                continue
            if entry.suffix.lower() not in {".txt", ".md"}:
                continue
            if "main" in entry.stem.lower():
                continue

            course_title = entry.stem.replace("_", " ").strip()
            course_id = _slugify(entry.stem)
            courses.append(
                TeacherBotCourse(
                    course_id=course_id,
                    course_title=course_title,
                    source_path=str(entry),
                )
            )

    courses.sort(key=lambda x: x.course_title.lower())
    return courses


def get_course(instructor_id: str, course_id: str) -> Optional[TeacherBotCourse]:
    for c in list_courses_for_instructor(instructor_id):
        if c.course_id == course_id:
            return c
    return None


def load_course_text(instructor_id: str, course_id: str) -> str:
    course = get_course(instructor_id, course_id)
    if not course:
        return ""

    p = Path(course.source_path)
    if p.is_file():
        return _read_text_file(p)

    if p.is_dir():
        readme_candidates = [p / "Course.txt", p / "course.txt", p / "README.md", p / "readme.md"]
        for c in readme_candidates:
            if c.exists() and c.is_file():
                return _read_text_file(c)

    return ""


def make_db_agent_and_course_fields(instructor: TeacherBotInstructor, course: TeacherBotCourse) -> Tuple[str, str, str, str]:
    agent_id = instructor.instructor_id
    agent_name = instructor.instructor_name
    db_course_id = f"{agent_id}__{course.course_id}"
    db_course_title = course.course_title
    return agent_id, agent_name, db_course_id, db_course_title
