"""Cascade task progress/status updates across project modules."""

"""Cascade task progress/status updates across project modules."""

from app.gantt_scheduler import reschedule_gantt_from_wbs, enrich_gantt_schedule

import copy
from datetime import datetime
from typing import Any


STATUS_PROGRESS = {
    "not_started": 0,
    "in_progress": 50,
    "on_hold": None,
    "blocked": None,
    "completed": 100,
}


def normalize_status(status: str | None, progress: float | None) -> str:
    if status in STATUS_PROGRESS:
        return status
    p = float(progress or 0)
    if p >= 100:
        return "completed"
    if p > 0:
        return "in_progress"
    return "not_started"


def status_to_progress(status: str, current_progress: float = 0) -> float:
    if status == "completed":
        return 100.0
    if status == "not_started":
        return 0.0
    if status in ("on_hold", "blocked"):
        return float(current_progress or 0)
    if status == "in_progress":
        return float(current_progress or 25) if current_progress <= 0 else float(current_progress)
    return float(current_progress or 0)


def _leaf_tasks(tasks: list) -> list:
    return [t for t in tasks if not t.get("is_summary")]


def _avg_progress(tasks: list) -> float:
    leaves = _leaf_tasks(tasks)
    if not leaves:
        return 0.0
    return sum(float(t.get("progress") or 0) for t in leaves) / len(leaves)


def _count_by_status(tasks: list) -> dict:
    counts = {k: 0 for k in STATUS_PROGRESS}
    for t in _leaf_tasks(tasks):
        st = normalize_status(t.get("status"), t.get("progress"))
        counts[st] = counts.get(st, 0) + 1
    return counts


def _rollup_status(statuses: list, progresses: list) -> str:
    statuses = [s for s in statuses if s]
    progresses = [float(p or 0) for p in progresses]
    if not progresses:
        return "not_started"
    if all(p >= 100 for p in progresses):
        return "completed"
    if any(s == "blocked" for s in statuses):
        return "blocked"
    if any(s == "on_hold" for s in statuses):
        return "on_hold"
    if any(p > 0 for p in progresses) or any(s == "in_progress" for s in statuses):
        return "in_progress"
    return "not_started"


def _wbs_code_key(code: str) -> tuple:
    if not code:
        return (float("inf"),)
    parts = []
    for part in str(code).split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(part)
    return tuple(parts)


def sort_wbs_by_code(nodes: list) -> list:
    """Sort WBS nodes numerically by code (e.g. 4.0 before 10.0)."""
    nodes = copy.deepcopy(nodes or [])
    nodes.sort(key=lambda n: _wbs_code_key(n.get("code")))
    for n in nodes:
        children = n.get("children") or []
        if children:
            n["children"] = sort_wbs_by_code(children)
    return nodes


def rollup_wbs(nodes: list) -> list:
    """Bottom-up rollup of duration, progress, and status from children to parents."""

    def walk(node: dict) -> dict:
        n = copy.deepcopy(node)
        children = n.get("children") or []
        if not children:
            n.setdefault("progress", float(n.get("progress") or 0))
            n.setdefault("status", normalize_status(n.get("status"), n.get("progress")))
            return n

        rolled_children = [walk(c) for c in children]
        n["children"] = rolled_children
        n["duration_days"] = sum(max(int(c.get("duration_days") or 0), 0) for c in rolled_children)
        progresses = [float(c.get("progress") or 0) for c in rolled_children]
        statuses = [c.get("status") or normalize_status(None, c.get("progress")) for c in rolled_children]
        n["progress"] = round(sum(progresses) / len(progresses), 1)
        n["status"] = _rollup_status(statuses, progresses)
        return n

    return [walk(n) for n in (nodes or [])]


def _wbs_code_depth(code: str) -> int:
    if not code:
        return 0
    return len(str(code).split("."))


def _is_direct_wbs_child(parent_code: str, child_code: str) -> bool:
    if not parent_code or not child_code:
        return False
    if not str(child_code).startswith(str(parent_code) + "."):
        return False
    return _wbs_code_depth(child_code) == _wbs_code_depth(parent_code) + 1


def _rollup_gantt_summaries(gantt: dict) -> dict:
    """Roll up progress/status into summary (parent) gantt tasks."""
    gantt = copy.deepcopy(gantt or {})
    tasks = gantt.get("tasks") or []
    if not tasks:
        return gantt

    by_code = {t.get("wbs_code"): t for t in tasks if t.get("wbs_code")}
    # Process deepest codes first so multi-level rollup works
    ordered = sorted(tasks, key=lambda t: _wbs_code_depth(t.get("wbs_code", "")), reverse=True)

    for task in ordered:
        code = task.get("wbs_code")
        if not code:
            continue
        children = [t for t in tasks if _is_direct_wbs_child(code, t.get("wbs_code", ""))]
        if not children and not task.get("is_summary"):
            continue
        if not children:
            # Summary flag but no direct children — match by prefix one level
            children = [
                t for t in tasks
                if t.get("wbs_code") and str(t["wbs_code"]).startswith(code + ".")
                and _is_direct_wbs_child(code, t["wbs_code"])
            ]
        if not children:
            continue

        progresses = [float(c.get("progress") or 0) for c in children]
        statuses = [c.get("status") or normalize_status(None, c.get("progress")) for c in children]
        task["progress"] = round(sum(progresses) / len(progresses), 1)
        task["status"] = _rollup_status(statuses, progresses)
        task["is_summary"] = True

    gantt["tasks"] = tasks
    return gantt


def _sync_gantt_from_wbs(wbs: list, gantt: dict) -> dict:
    """Push rolled-up WBS progress/duration into matching gantt tasks (including parents)."""
    gantt = copy.deepcopy(gantt or {})
    tasks = gantt.get("tasks") or []
    if not tasks or not wbs:
        return gantt

    flat = {}

    def flatten(nodes):
        for n in nodes or []:
            if n.get("code"):
                flat[n["code"]] = n
            flatten(n.get("children"))

    flatten(rollup_wbs(wbs))

    for task in tasks:
        code = task.get("wbs_code")
        if code and code in flat:
            w = flat[code]
            if w.get("progress") is not None:
                task["progress"] = float(w["progress"])
            if w.get("status"):
                task["status"] = w["status"]
            if w.get("duration_days") is not None and task.get("is_summary"):
                task["duration_days"] = int(w["duration_days"])

    gantt["tasks"] = tasks
    return _rollup_gantt_summaries(gantt)


def _sync_wbs_from_gantt(wbs: list, tasks: list) -> list:
    if not isinstance(wbs, list):
        return wbs
    by_code = {t.get("wbs_code"): t for t in tasks if t.get("wbs_code")}

    def walk(nodes):
        out = []
        for node in nodes:
            n = copy.deepcopy(node)
            code = n.get("code")
            if code and code in by_code:
                gt = by_code[code]
                n["progress"] = gt.get("progress", n.get("progress", 0))
                n["status"] = gt.get("status", normalize_status(None, n.get("progress")))
            if n.get("children"):
                n["children"] = walk(n["children"])
            out.append(n)
        return out

    return rollup_wbs(walk(wbs))


def _update_task_in_gantt(gantt: dict, task_id: Any, wbs_code: str | None, status: str | None, progress: float | None) -> dict:
    gantt = copy.deepcopy(gantt or {})
    tasks = gantt.get("tasks") or []
    for task in tasks:
        match = (task_id is not None and task.get("id") == task_id) or (
            wbs_code and (
                task.get("wbs_code") == wbs_code
                or str(task.get("name", "")).lower() == str(wbs_code).lower()
            )
        )
        if not match:
            continue
        if status:
            task["status"] = status
            task["progress"] = status_to_progress(status, task.get("progress", 0))
        if progress is not None:
            task["progress"] = max(0.0, min(100.0, float(progress)))
            task["status"] = normalize_status(task.get("status"), task["progress"])
        break
    gantt["tasks"] = tasks
    return gantt


def sync_project_from_tasks(project) -> dict:
    """Recalculate derived fields from gantt task progress. Mutates project in place."""
    gantt = project.gantt or {}
    tasks = gantt.get("tasks") or []
    if not tasks:
        return {"overall_progress": 0}

    overall = _avg_progress(tasks)
    status_counts = _count_by_status(tasks)
    completed = status_counts.get("completed", 0)
    total_leaves = len(_leaf_tasks(tasks))
    delayed = 0
    today = datetime.utcnow().date()
    for t in _leaf_tasks(tasks):
        end = t.get("end")
        prog = float(t.get("progress") or 0)
        if end and prog < 100:
            try:
                end_dt = datetime.strptime(end[:10], "%Y-%m-%d").date()
                if end_dt < today:
                    delayed += 1
            except ValueError:
                pass

    # WBS sync
    if project.wbs:
        project.wbs = _sync_wbs_from_gantt(project.wbs, tasks)

    # Budget
    budget = float(project.budget or 0)
    earned = budget * (overall / 100.0)
    project.actual_cost = round(earned, 2)
    bd = copy.deepcopy(project.budget_details or {})
    if bd:
        bd["actual_cost"] = project.actual_cost
        bd["variance"] = budget - project.actual_cost
        planned = float(bd.get("planned_budget") or budget)
        for cat in bd.get("categories") or []:
            cat_planned = float(cat.get("planned") or 0)
            cat["actual"] = round(cat_planned * (overall / 100.0), 2)
            cat["variance"] = cat_planned - cat["actual"]
        bd["planned_budget"] = planned
        project.budget_details = bd

    # Resources utilization
    resources = project.resources
    if isinstance(resources, dict):
        depts = resources.get("departments") or resources.get("allocations") or []
        active_ratio = (status_counts.get("in_progress", 0) + completed) / max(total_leaves, 1)
        for d in depts:
            base = float(d.get("utilization") or 50)
            dtype = d.get("type", "department")
            if dtype in ("machine", "equipment"):
                d["utilization"] = round(min(100, base * (0.6 + 0.4 * active_ratio)), 1)
            else:
                d["utilization"] = round(min(100, base * (0.5 + 0.5 * active_ratio)), 1)
        project.resources = {**resources, "departments": depts}

    # Inventory — procurement progress increases available stock
    inv = project.inventory
    materials = inv.get("materials") if isinstance(inv, dict) else (inv if isinstance(inv, list) else [])
    if materials:
        procurement_progress = overall / 100.0
        for m in materials:
            req = float(m.get("required") or 0)
            if req > 0:
                m["available"] = round(min(req, req * (0.3 + 0.7 * procurement_progress)), 1)
                if m["available"] >= req:
                    m["status"] = "In Stock"
                elif m["available"] > 0:
                    m["status"] = "Partial"
                else:
                    m["status"] = m.get("status") or "Pending"
        project.inventory = {"materials": materials} if isinstance(inv, dict) else materials

    # Risks — schedule delays increase open risk scores
    risks = project.risks
    risk_list = risks if isinstance(risks, list) else (risks.get("risks") if isinstance(risks, dict) else [])
    for r in risk_list:
        cat = (r.get("category") or "").lower()
        if delayed > 0 and ("schedule" in cat or "supply" in cat or r.get("title", "").lower().find("delay") >= 0):
            r["score"] = min(10, int(r.get("score") or 4) + delayed)
            r["probability"] = "High" if delayed >= 2 else r.get("probability", "Medium")
    project.risks = risk_list

    # Quality
    quality = copy.deepcopy(project.quality or {})
    if quality:
        quality["quality_score"] = round(min(100, 60 + overall * 0.4), 1)
        quality["defect_rate"] = round(max(0, 2.5 - overall * 0.02), 2)
        if quality.get("target_defect_rate") is None:
            quality["target_defect_rate"] = 1.0
        project.quality = quality

    # Maintenance — higher utilization lowers health slightly
    maint = project.maintenance
    machines = maint.get("machines") if isinstance(maint, dict) else (maint if isinstance(maint, list) else [])
    for m in machines:
        util_factor = overall / 100.0
        base_health = float(m.get("health_score") or 90)
        m["health_score"] = round(max(40, base_health - util_factor * 8), 1)
        m["failure_probability"] = round(min(0.95, float(m.get("failure_probability") or 0.1) + util_factor * 0.05), 2)
    project.maintenance = {"machines": machines} if isinstance(maint, dict) else machines

    # KPIs
    spi = round(overall / 100.0 / max(0.5, (completed / max(total_leaves, 1)) + 0.5), 2) if total_leaves else 1.0
    cpi = round(1.0 + (budget - project.actual_cost) / max(budget, 1) * 0.5, 2) if budget else 1.0
    milestones = gantt.get("milestones") or []
    ms_completed = min(len(milestones), completed)
    kpis = copy.deepcopy(project.kpis or {})
    kpis["schedule_performance"] = {
        "spi": spi,
        "status": "On Track" if spi >= 0.95 else "Slightly Behind" if spi >= 0.85 else "Behind",
        "percent_complete": round(overall, 1),
    }
    kpis["cost_performance"] = {
        "cpi": cpi,
        "status": "Under Budget" if cpi >= 1 else "Over Budget",
        "budget_used_percent": round((project.actual_cost / max(budget, 1)) * 100, 1),
    }
    kpis["quality_metrics"] = {
        "defect_rate": quality.get("defect_rate", 0) if quality else 0,
        "first_pass_yield": round(min(100, 90 + overall * 0.1), 1),
    }
    ru = resources.get("departments") if isinstance(resources, dict) else []
    overall_util = sum(float(d.get("utilization") or 0) for d in ru) / max(len(ru), 1) if ru else 0
    kpis["resource_utilization"] = {"overall": round(overall_util, 1)}
    health = round(min(100, 50 + overall * 0.35 + (10 if delayed == 0 else -delayed * 5) + (5 if cpi >= 1 else -5)), 1)
    kpis["project_health"] = {
        "score": health,
        "status": "Green" if health >= 80 else "Amber" if health >= 60 else "Red",
    }
    kpis["milestones"] = {
        "completed": ms_completed,
        "total": max(len(milestones), total_leaves),
        "on_track": max(0, total_leaves - delayed - completed),
        "delayed": delayed,
    }
    project.kpis = kpis
    project.health_score = health

    if overall >= 100 and project.status == "in_progress":
        project.status = "completed"
    elif overall > 0 and project.status == "planning":
        project.status = "in_progress"

    return {
        "overall_progress": round(overall, 1),
        "completed_tasks": completed,
        "total_tasks": total_leaves,
        "delayed_tasks": delayed,
        "health_score": health,
    }


def apply_task_update(project, task_id=None, wbs_code=None, status=None, progress=None) -> dict:
    project.gantt = _update_task_in_gantt(project.gantt, task_id, wbs_code, status, progress)
    project.gantt = _rollup_gantt_summaries(project.gantt)
    enrich_project_gantt(project)
    if project.wbs:
        project.wbs = _sync_wbs_from_gantt(project.wbs, project.gantt.get("tasks") or [])
    return sync_project_from_tasks(project)


def _gantt_start_date(project) -> str:
    if project.start_date:
        return str(project.start_date)
    gantt = project.gantt or {}
    tasks = gantt.get("tasks") or []
    if tasks:
        return min(t["start"] for t in tasks if t.get("start"))
    return "2026-02-01"


def enrich_project_gantt(project) -> None:
    """Ensure gantt has correct critical path and float (mutates project in place)."""
    if not project.gantt or not project.gantt.get("tasks"):
        return
    project.gantt = enrich_gantt_schedule(project.gantt, project.wbs, _gantt_start_date(project))


def refresh_gantt_metrics(gantt: dict, start_date: str, wbs: list | None = None) -> dict:
    return enrich_gantt_schedule(gantt, wbs, start_date)


def _refresh_gantt_cpm(gantt: dict, start_date: str) -> dict:
    return refresh_gantt_metrics(gantt, start_date)


def sync_wbs_and_gantt(project) -> dict:
    """Roll up WBS parents, reschedule gantt with parallel-aware logic, and sync metrics."""
    start_date = _gantt_start_date(project)
    if project.wbs:
        project.wbs = sort_wbs_by_code(project.wbs)
        project.wbs = rollup_wbs(project.wbs)
        project.gantt = reschedule_gantt_from_wbs(project.wbs, project.gantt, start_date)
    elif project.gantt:
        project.gantt = _refresh_gantt_cpm(project.gantt, start_date)
    return sync_project_from_tasks(project)
