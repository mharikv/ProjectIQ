import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, Project, ChatMessage, Task
from app.schemas import ChatRequest, ChatResponse, AIGenerateRequest
from app.auth import get_current_user
from app.ai_service import ai_service
from app.project_editor import parse_chat_actions, apply_actions
from app.data_merge import (
    merge_charter, merge_wbs, merge_gantt, merge_resources, merge_budget,
    merge_inventory, merge_risks, merge_maintenance, merge_quality,
)
from app.project_sync import sync_project_from_tasks

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["AI Features"])


def _get_project_or_404(project_id: int, user: User, db: Session) -> Project:
    query = db.query(Project).filter(Project.id == project_id)
    if user.role != "admin":
        query = query.filter(Project.owner_id == user.id)
    project = query.first()
    if not project:
        logger.warning("Project id=%s not found for user id=%s", project_id, user.id)
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project_context = {}
    history = []

    if request.project_id:
        project = _get_project_or_404(request.project_id, current_user, db)
        project_context = {
            "name": project.name,
            "status": project.status,
            "budget": project.budget,
            "actual_cost": project.actual_cost,
            "health_score": project.health_score,
            "charter": project.charter,
            "wbs": project.wbs,
            "inventory": project.inventory,
            "risks": project.risks,
            "maintenance": project.maintenance,
            "kpis": project.kpis,
        }
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.project_id == request.project_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(10)
            .all()
        )
        history = [{"role": m.role, "content": m.content} for m in reversed(messages)]

    user_msg = ChatMessage(
        project_id=request.project_id or 0,
        user_id=current_user.id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)

    chat_result = ai_service.chat(request.message, project_context, history)
    response_content = chat_result.get("reply", chat_result) if isinstance(chat_result, dict) else chat_result
    actions = chat_result.get("actions", []) if isinstance(chat_result, dict) else []

    # Rule-based fallback for edit commands
    if request.project_id and not actions:
        actions = parse_chat_actions(request.message, project_context)

    fields_updated = []
    if request.project_id and actions:
        project = _get_project_or_404(request.project_id, current_user, db)
        applied, errors = apply_actions(project, actions)
        if applied:
            db.commit()
            fields_updated = list({a.split()[1] if " " in a else a for a in applied})
            summary = "\n\n**Changes applied:**\n" + "\n".join(f"- {a}" for a in applied)
            if errors:
                summary += "\n\n**Could not apply:**\n" + "\n".join(f"- {e}" for e in errors)
            response_content = response_content + summary
            logger.info("Chat applied %s actions on project id=%s", len(applied), request.project_id)

    assistant_msg = ChatMessage(
        project_id=request.project_id or 0,
        user_id=current_user.id,
        role="assistant",
        content=response_content,
    )
    db.add(assistant_msg)
    db.commit()

    return ChatResponse(
        role="assistant",
        content=response_content,
        created_at=datetime.utcnow(),
        fields_updated=fields_updated or None,
    )


@router.get("/chat/{project_id}/history", response_model=List[ChatResponse])
def chat_history(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project_or_404(project_id, current_user, db)
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.project_id == project_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return [ChatResponse(role=m.role, content=m.content, created_at=m.created_at) for m in messages]


@router.post("/charter/{project_id}")
def generate_charter(
    project_id: int,
    request: AIGenerateRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_or_404(project_id, current_user, db)
    prompt = request.prompt if request else None
    try:
        logger.info("Generating charter for project id=%s user=%s", project_id, current_user.username)
        charter = ai_service.generate_charter(project.name, project.description or "", prompt)
        project.charter = merge_charter(project.charter, charter)
        db.commit()
        return charter
    except Exception as exc:
        logger.exception("Charter generation failed for project id=%s: %s", project_id, exc)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/wbs/{project_id}")
def generate_wbs(
    project_id: int,
    request: AIGenerateRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_or_404(project_id, current_user, db)
    prompt = request.prompt if request else None
    try:
        logger.info("Generating WBS for project id=%s user=%s", project_id, current_user.username)
        wbs = ai_service.generate_wbs(project.name, project.charter or {}, prompt)
        if not isinstance(wbs, list):
            raise ValueError("WBS must be a list")
        project.wbs = merge_wbs(project.wbs, wbs)
        db.commit()
        logger.info("WBS generated successfully for project id=%s (%s items)", project_id, len(wbs))
        return wbs
    except Exception as exc:
        logger.exception("WBS generation failed for project id=%s: %s", project_id, exc)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/gantt/{project_id}")
def generate_gantt(
    project_id: int,
    request: AIGenerateRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_or_404(project_id, current_user, db)
    prompt = request.prompt if request else None
    start = str(project.start_date) if project.start_date else "2026-02-01"
    try:
        logger.info("Generating Gantt for project id=%s", project_id)
        gantt = ai_service.generate_gantt(project.name, project.wbs or [], start, prompt, project.gantt)
        project.gantt = merge_gantt(project.gantt, gantt)
        from app.project_sync import enrich_project_gantt
        enrich_project_gantt(project)
        sync_project_from_tasks(project)
        db.commit()
        return gantt
    except Exception as exc:
        logger.exception("Gantt generation failed for project id=%s: %s", project_id, exc)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/resources/{project_id}")
def optimize_resources(
    project_id: int,
    request: AIGenerateRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_or_404(project_id, current_user, db)
    prompt = request.prompt if request else None
    tasks = [{"name": t.name, "status": t.status} for t in db.query(Task).filter(Task.project_id == project_id).all()]
    try:
        logger.info("Optimizing resources for project id=%s", project_id)
        result = ai_service.optimize_resources(project.name, tasks, project.resources or [], prompt)
        project.resources = merge_resources(project.resources, result)
        db.commit()
        return result
    except Exception as exc:
        logger.exception("Resource optimization failed for project id=%s: %s", project_id, exc)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/budget/{project_id}")
def analyze_budget(
    project_id: int,
    request: AIGenerateRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_or_404(project_id, current_user, db)
    prompt = request.prompt if request else None
    budget_data = {"budget": project.budget, "actual_cost": project.actual_cost, "details": project.budget_details or {}}
    try:
        logger.info("Analyzing budget for project id=%s", project_id)
        result = ai_service.analyze_budget(project.name, budget_data, prompt)
        project.budget_details = merge_budget(project.budget_details, result)
        sync_project_from_tasks(project)
        db.commit()
        return result
    except Exception as exc:
        logger.exception("Budget analysis failed for project id=%s: %s", project_id, exc)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/inventory/{project_id}")
def plan_inventory(
    project_id: int,
    request: AIGenerateRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_or_404(project_id, current_user, db)
    prompt = request.prompt if request else None
    try:
        logger.info("Planning inventory for project id=%s", project_id)
        result = ai_service.plan_inventory(project.name, project.inventory or [], prompt)
        project.inventory = merge_inventory(project.inventory, result)
        sync_project_from_tasks(project)
        db.commit()
        return result
    except Exception as exc:
        logger.exception("Inventory planning failed for project id=%s: %s", project_id, exc)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/risks/{project_id}")
def analyze_risks(
    project_id: int,
    request: AIGenerateRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_or_404(project_id, current_user, db)
    prompt = request.prompt if request else None
    project_data = {"name": project.name, "status": project.status, "budget": project.budget, "charter": project.charter}
    try:
        logger.info("Analyzing risks for project id=%s", project_id)
        result = ai_service.analyze_risks(project.name, project_data, prompt)
        project.risks = merge_risks(project.risks, result)
        sync_project_from_tasks(project)
        db.commit()
        return result
    except Exception as exc:
        logger.exception("Risk analysis failed for project id=%s: %s", project_id, exc)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/quality/{project_id}")
def analyze_quality(
    project_id: int,
    request: AIGenerateRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_or_404(project_id, current_user, db)
    prompt = request.prompt if request else None
    try:
        logger.info("Analyzing quality for project id=%s", project_id)
        result = ai_service.analyze_quality(project.name, project.quality or {}, prompt)
        project.quality = merge_quality(project.quality, result)
        sync_project_from_tasks(project)
        db.commit()
        return result
    except Exception as exc:
        logger.exception("Quality analysis failed for project id=%s: %s", project_id, exc)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/maintenance/{project_id}")
def predict_maintenance(
    project_id: int,
    request: AIGenerateRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_or_404(project_id, current_user, db)
    prompt = request.prompt if request else None
    try:
        logger.info("Predicting maintenance for project id=%s", project_id)
        result = ai_service.predict_maintenance(project.maintenance or [], prompt)
        project.maintenance = merge_maintenance(project.maintenance, result)
        sync_project_from_tasks(project)
        db.commit()
        return result
    except Exception as exc:
        logger.exception("Maintenance prediction failed for project id=%s: %s", project_id, exc)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/kpis/{project_id}")
def generate_kpis(
    project_id: int,
    request: AIGenerateRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_or_404(project_id, current_user, db)
    prompt = request.prompt if request else None
    project_data = {
        "name": project.name, "status": project.status, "budget": project.budget,
        "actual_cost": project.actual_cost, "charter": project.charter, "risks": project.risks,
    }
    try:
        logger.info("Generating KPIs for project id=%s", project_id)
        result = ai_service.generate_kpis(project.name, project_data, prompt)
        sync_project_from_tasks(project)
        merged_kpis = {**result, **(project.kpis or {})}
        project.kpis = merged_kpis
        health = result.get("project_health", {})
        if health.get("score"):
            project.health_score = health["score"]
        db.commit()
        return result
    except Exception as exc:
        logger.exception("KPI generation failed for project id=%s: %s", project_id, exc)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
