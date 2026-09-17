from datetime import datetime, date
from typing import Optional, Any
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "project_manager"


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[str] = "planning"
    priority: Optional[str] = "medium"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = 0.0


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = None
    actual_cost: Optional[float] = None
    charter: Optional[dict] = None
    wbs: Optional[list] = None
    gantt: Optional[dict] = None
    resources: Optional[Any] = None
    budget_details: Optional[dict] = None
    inventory: Optional[Any] = None
    risks: Optional[Any] = None
    quality: Optional[dict] = None
    maintenance: Optional[Any] = None
    kpis: Optional[dict] = None
    health_score: Optional[float] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    priority: str
    start_date: Optional[date]
    end_date: Optional[date]
    budget: float
    actual_cost: float
    owner_id: Optional[int]
    charter: Optional[dict]
    wbs: Optional[list]
    gantt: Optional[dict]
    resources: Optional[Any]
    budget_details: Optional[dict]
    inventory: Optional[Any]
    risks: Optional[Any]
    quality: Optional[dict]
    maintenance: Optional[Any]
    kpis: Optional[dict]
    health_score: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[str] = "not_started"
    priority: Optional[str] = "medium"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_days: Optional[int] = 1
    progress: Optional[float] = 0.0
    assigned_to: Optional[str] = None
    dependencies: Optional[list] = None
    wbs_code: Optional[str] = None
    estimated_cost: Optional[float] = 0.0
    actual_cost: Optional[float] = 0.0


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_days: Optional[int] = None
    progress: Optional[float] = None
    assigned_to: Optional[str] = None
    dependencies: Optional[list] = None
    wbs_code: Optional[str] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None


class TaskResponse(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str]
    status: str
    priority: str
    start_date: Optional[date]
    end_date: Optional[date]
    duration_days: int
    progress: float
    assigned_to: Optional[str]
    dependencies: Optional[list]
    wbs_code: Optional[str]
    estimated_cost: float
    actual_cost: float

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    project_id: Optional[int] = None


class ChatResponse(BaseModel):
    role: str
    content: str
    created_at: datetime
    fields_updated: Optional[list[str]] = None


class AIGenerateRequest(BaseModel):
    project_id: int
    prompt: Optional[str] = None
    context: Optional[dict] = None


class GanttTaskUpdate(BaseModel):
    task_id: Optional[int] = None
    wbs_code: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[float] = None
