from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, Date,
    ForeignKey, Boolean, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(50), default="project_manager")
    created_at = Column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", back_populates="owner")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="planning")
    priority = Column(String(20), default="medium")
    start_date = Column(Date)
    end_date = Column(Date)
    budget = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)
    owner_id = Column(Integer, ForeignKey("users.id"))
    charter = Column(JSON, default=dict)
    wbs = Column(JSON, default=list)
    gantt = Column(JSON, default=dict)
    resources = Column(JSON, default=list)
    budget_details = Column(JSON, default=dict)
    inventory = Column(JSON, default=list)
    risks = Column(JSON, default=list)
    quality = Column(JSON, default=dict)
    maintenance = Column(JSON, default=list)
    kpis = Column(JSON, default=dict)
    health_score = Column(Float, default=100.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="not_started")
    priority = Column(String(20), default="medium")
    start_date = Column(Date)
    end_date = Column(Date)
    duration_days = Column(Integer, default=1)
    progress = Column(Float, default=0.0)
    assigned_to = Column(String(100))
    dependencies = Column(JSON, default=list)
    wbs_code = Column(String(20))
    estimated_cost = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="tasks")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="chat_messages")


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    availability = Column(Float, default=100.0)
    cost_per_hour = Column(Float, default=0.0)
    skills = Column(JSON, default=list)
    status = Column(String(50), default="available")


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    sku = Column(String(50), unique=True)
    quantity = Column(Float, default=0.0)
    unit = Column(String(20), default="units")
    reorder_level = Column(Float, default=10.0)
    unit_cost = Column(Float, default=0.0)
    supplier = Column(String(100))
    lead_time_days = Column(Integer, default=7)


class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50))
    status = Column(String(50), default="operational")
    last_maintenance = Column(Date)
    next_maintenance = Column(Date)
    health_score = Column(Float, default=100.0)
    failure_probability = Column(Float, default=0.0)
    operating_hours = Column(Float, default=0.0)
