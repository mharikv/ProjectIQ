import logging
import re
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, Project, Task
from app.schemas import ProjectCreate, ProjectUpdate, ProjectResponse, TaskCreate, TaskUpdate, TaskResponse, GanttTaskUpdate
from app.auth import get_current_user
from app.report_generator import generate_project_report_pptx
from app.project_sync import apply_task_update, sync_project_from_tasks, sync_wbs_and_gantt, enrich_project_gantt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("/", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Project)
    if current_user.role != "admin":
        query = query.filter(Project.owner_id == current_user.id)
    projects = query.all()
    logger.info("Listed %s projects for user=%s", len(projects), current_user.username)
    return projects


@router.post("/", response_model=ProjectResponse)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        project = Project(**project_data.model_dump(), owner_id=current_user.id)
        db.add(project)
        db.commit()
        db.refresh(project)
        logger.info("Created project id=%s name='%s' for user=%s", project.id, project.name, current_user.username)
        return project
    except Exception as exc:
        logger.exception("Failed to create project for user=%s: %s", current_user.username, exc)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create project: {exc}")


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Project).filter(Project.id == project_id)
    if current_user.role != "admin":
        query = query.filter(Project.owner_id == current_user.id)
    project = query.first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    enrich_project_gantt(project)
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id)
    if current_user.role != "admin":
        project = project.filter(Project.owner_id == current_user.id)
    project = project.first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        updates = project_data.model_dump(exclude_unset=True)
        wbs_updated = "wbs" in updates
        gantt_updated = "gantt" in updates
        for key, value in updates.items():
            setattr(project, key, value)
        if wbs_updated and project.wbs:
            sync_wbs_and_gantt(project)
        elif gantt_updated and project.gantt:
            enrich_project_gantt(project)
            sync_project_from_tasks(project)
        db.commit()
        db.refresh(project)
        logger.info("Updated project id=%s for user=%s", project_id, current_user.username)
        return project
    except Exception as exc:
        logger.exception("Failed to update project id=%s: %s", project_id, exc)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update project: {exc}")


@router.patch("/{project_id}/gantt/task", response_model=ProjectResponse)
def update_gantt_task(
    project_id: int,
    update: GanttTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Project).filter(Project.id == project_id)
    if current_user.role != "admin":
        query = query.filter(Project.owner_id == current_user.id)
    project = query.first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not update.task_id and not update.wbs_code:
        raise HTTPException(status_code=400, detail="task_id or wbs_code required")
    try:
        summary = apply_task_update(
            project,
            task_id=update.task_id,
            wbs_code=update.wbs_code,
            status=update.status,
            progress=update.progress,
        )
        db.commit()
        db.refresh(project)
        logger.info("Updated gantt task on project id=%s: %s", project_id, summary)
        return project
    except Exception as exc:
        logger.exception("Failed to update gantt task: %s", exc)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{project_id}/sync", response_model=ProjectResponse)
def sync_project_metrics(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Project).filter(Project.id == project_id)
    if current_user.role != "admin":
        query = query.filter(Project.owner_id == current_user.id)
    project = query.first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    sync_wbs_and_gantt(project)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    name = project.name
    db.delete(project)
    db.commit()
    logger.info("Deleted project id=%s name='%s' for user=%s", project_id, name, current_user.username)
    return {"message": "Project deleted"}


@router.get("/{project_id}/report/pptx")
def download_project_report_pptx(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        buffer = generate_project_report_pptx(project)
        safe_name = re.sub(r"[^\w\s-]", "", project.name).strip().replace(" ", "_")[:60] or "Project"
        filename = f"{safe_name}_Report.pptx"
        logger.info("Serving PPTX report for project id=%s user=%s", project_id, current_user.username)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        logger.exception("Failed to generate PPTX for project id=%s: %s", project_id, exc)
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {exc}")


@router.get("/{project_id}/tasks", response_model=List[TaskResponse])
def list_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(Task).filter(Task.project_id == project_id).all()


@router.post("/{project_id}/tasks", response_model=TaskResponse)
def create_task(
    project_id: int,
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    task = Task(**task_data.model_dump(), project_id=project_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put("/{project_id}/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    project_id: int,
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for key, value in task_data.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{project_id}/tasks/{task_id}")
def delete_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}
