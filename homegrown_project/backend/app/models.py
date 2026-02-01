from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    role = Column(String) 
    display_name = Column(String) # Ensure this is here!
    
    enrollments = relationship("Enrollment", back_populates="student")

class Agent(Base):
    __tablename__ = "agents"
    id = Column(String, primary_key=True)
    name = Column(String)
    system_prompt_core = Column(Text)
    
    courses = relationship("Course", back_populates="agent")

class Course(Base):
    __tablename__ = "courses"
    id = Column(String, primary_key=True)
    title = Column(String)
    agent_id = Column(String, ForeignKey("agents.id"))
    curriculum_json = Column(JSON)
    
    agent = relationship("Agent", back_populates="courses")

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(String, ForeignKey("courses.id"))
    current_module_index = Column(Integer, default=0)
    student_facts = Column(JSON, default=dict)
    
    # --- THIS WAS THE MISSING LINK ---
    student = relationship("User", back_populates="enrollments")
    course = relationship("Course") # <--- I forgot this line before.
    chat_logs = relationship("ChatLog", back_populates="enrollment")

class ChatLog(Base):
    __tablename__ = "chat_logs"
    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"))
    sender = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    enrollment = relationship("Enrollment", back_populates="chat_logs")