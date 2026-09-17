"""Apply structured add/update/remove actions to project JSON fields."""

import copy
import logging
import re
import uuid
from typing import Any

logger = logging.getLogger(__name__)

EDITABLE_FIELDS = {"charter", "wbs", "inventory", "risks", "maintenance", "gantt_task"}


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _normalize_inventory(data: Any) -> dict:
    if isinstance(data, dict) and "materials" in data:
        return copy.deepcopy(data)
    materials = data if isinstance(data, list) else []
    return {"materials": copy.deepcopy(materials)}


def _normalize_risks(data: Any) -> list:
    if isinstance(data, dict):
        return copy.deepcopy(data.get("risks", []))
    return copy.deepcopy(data) if isinstance(data, list) else []


def _normalize_maintenance(data: Any) -> dict:
    if isinstance(data, dict) and "machines" in data:
        return copy.deepcopy(data)
    machines = data if isinstance(data, list) else []
    return {"machines": copy.deepcopy(machines)}


def _find_wbs_node(nodes: list, code: str) -> dict | None:
    for node in nodes:
        if node.get("code") == code:
            return node
        if node.get("children"):
            found = _find_wbs_node(node["children"], code)
            if found:
                return found
    return None


def _remove_wbs_node(nodes: list, code: str) -> bool:
    for i, node in enumerate(nodes):
        if node.get("code") == code:
            nodes.pop(i)
            return True
        if node.get("children") and _remove_wbs_node(node["children"], code):
            return True
    return False


def apply_action(project, action: dict) -> tuple[bool, str]:
    """Apply one action dict to project. Returns (success, message)."""
    field = action.get("field")
    op = action.get("action")
    data = action.get("data") or {}

    if field not in EDITABLE_FIELDS:
        return False, f"Unknown field: {field}"

    if op == "set":
        setattr(project, field, data)
        return True, f"Updated {field}"

    if field == "charter":
        charter = copy.deepcopy(project.charter or {})
        if op == "add":
            section = action.get("section")
            if section == "scope":
                charter["scope"] = data.get("value", data.get("scope", ""))
            elif section in ("objectives", "deliverables", "constraints", "assumptions", "success_criteria"):
                items = charter.setdefault(section, [])
                val = data.get("value") or data.get("text") or data.get("name")
                if val and val not in items:
                    items.append(val)
            elif section == "stakeholders":
                charter.setdefault("stakeholders", []).append({
                    "name": data.get("name", ""),
                    "role": data.get("role", ""),
                    "interest": data.get("interest", "Medium"),
                })
            else:
                charter.update(data)
            project.charter = charter
            return True, f"Added to charter {section or 'data'}"
        if op == "remove":
            section = action.get("section")
            index = action.get("index")
            if section and section in charter and isinstance(charter[section], list) and index is not None:
                if 0 <= index < len(charter[section]):
                    removed = charter[section].pop(index)
                    project.charter = charter
                    return True, f"Removed from charter {section}: {removed}"
            return False, "Could not remove charter item"

    if field == "wbs":
        wbs = copy.deepcopy(project.wbs or [])
        if not isinstance(wbs, list):
            wbs = []
        if op == "add":
            node = {
                "code": data.get("code", _new_id("wbs")),
                "name": data.get("name", "New Task"),
                "level": data.get("level", 1),
                "duration_days": int(data.get("duration_days") or 5),
                "children": [],
            }
            parent_code = action.get("parent_code") or data.get("parent_code")
            if parent_code:
                parent = _find_wbs_node(wbs, parent_code)
                if parent:
                    parent.setdefault("children", []).append(node)
                    node["level"] = (parent.get("level") or 1) + 1
                else:
                    wbs.append(node)
            else:
                wbs.append(node)
            project.wbs = wbs
            return True, f"Added WBS item {node['code']} — {node['name']}"
        if op == "remove":
            code = action.get("code") or data.get("code")
            if code and _remove_wbs_node(wbs, code):
                project.wbs = wbs
                return True, f"Removed WBS item {code}"
            return False, f"WBS item {code} not found"
        if op == "update":
            code = action.get("code") or data.get("code")
            node = _find_wbs_node(wbs, code) if code else None
            if node:
                for key in ("name", "code", "duration_days", "level"):
                    if key in data:
                        node[key] = data[key] if key != "duration_days" else int(data[key])
                project.wbs = wbs
                return True, f"Updated WBS item {code}"
            return False, f"WBS item {code} not found"

    if field == "inventory":
        inv = _normalize_inventory(project.inventory)
        materials = inv["materials"]
        if op == "add":
            materials.append({
                "name": data.get("name", "New Material"),
                "required": data.get("required", 0),
                "available": data.get("available", 0),
                "unit": data.get("unit", "units"),
                "status": data.get("status", "Pending"),
            })
            project.inventory = inv
            return True, f"Added inventory item: {data.get('name')}"
        if op == "remove":
            idx = action.get("index")
            name = data.get("name")
            if name:
                materials[:] = [m for m in materials if m.get("name") != name]
            elif idx is not None and 0 <= idx < len(materials):
                materials.pop(idx)
            else:
                return False, "Could not remove inventory item"
            project.inventory = inv
            return True, "Removed inventory item"
        if op == "update":
            name = data.get("name")
            for m in materials:
                if m.get("name") == name or (action.get("index") is not None and materials.index(m) == action["index"]):
                    m.update({k: v for k, v in data.items() if k != "name" or v})
                    project.inventory = inv
                    return True, f"Updated inventory item: {name or m.get('name')}"
            return False, "Inventory item not found"

    if field == "risks":
        risks = _normalize_risks(project.risks)
        if op == "add":
            risks.append({
                "id": data.get("id") or _new_id("risk"),
                "title": data.get("title", "New Risk"),
                "category": data.get("category", "General"),
                "probability": data.get("probability", "Medium"),
                "impact": data.get("impact", "Medium"),
                "score": data.get("score", 4),
                "mitigation": data.get("mitigation", ""),
            })
            project.risks = risks
            return True, f"Added risk: {data.get('title')}"
        if op == "remove":
            rid = data.get("id") or action.get("id")
            title = data.get("title")
            before = len(risks)
            risks[:] = [r for r in risks if r.get("id") != rid and (not title or r.get("title") != title)]
            if len(risks) < before:
                project.risks = risks
                return True, "Removed risk"
            return False, "Risk not found"
        if op == "update":
            rid = data.get("id") or action.get("id")
            for r in risks:
                if r.get("id") == rid or r.get("title") == data.get("title"):
                    r.update(data)
                    project.risks = risks
                    return True, f"Updated risk: {r.get('title')}"
            return False, "Risk not found"

    if field == "maintenance":
        maint = _normalize_maintenance(project.maintenance)
        machines = maint["machines"]
        if op == "add":
            machines.append({
                "name": data.get("name", "New Machine"),
                "health_score": float(data.get("health_score", 100)),
                "failure_probability": float(data.get("failure_probability", 0.05)),
                "predicted_failure_date": data.get("predicted_failure_date", ""),
                "recommendation": data.get("recommendation", ""),
            })
            project.maintenance = maint
            return True, f"Added machine: {data.get('name')}"
        if op == "remove":
            name = data.get("name")
            before = len(machines)
            machines[:] = [m for m in machines if m.get("name") != name]
            if len(machines) < before:
                project.maintenance = maint
                return True, f"Removed machine: {name}"
            return False, "Machine not found"
        if op == "update":
            name = data.get("name")
            for m in machines:
                if m.get("name") == name:
                    m.update(data)
                    project.maintenance = maint
                    return True, f"Updated machine: {name}"
            return False, "Machine not found"

    if field == "gantt_task":
        from app.project_sync import apply_task_update
        apply_task_update(
            project,
            wbs_code=action.get("wbs_code") or data.get("wbs_code"),
            task_id=action.get("task_id") or data.get("task_id"),
            status=action.get("status") or data.get("status"),
            progress=data.get("progress"),
        )
        return True, f"Updated task {action.get('wbs_code') or data.get('name', '')}"

    return False, f"Unsupported operation {op} on {field}"


def apply_actions(project, actions: list) -> tuple[list[str], list[str]]:
    applied, errors = [], []
    wbs_touched = False
    for action in actions:
        ok, msg = apply_action(project, action)
        if ok:
            applied.append(msg)
            if action.get("field") == "wbs":
                wbs_touched = True
        else:
            errors.append(msg)
    if wbs_touched:
        from app.project_sync import sync_wbs_and_gantt
        sync_wbs_and_gantt(project)
    return applied, errors


def parse_chat_actions(message: str, project_context: dict) -> list[dict]:
    """Rule-based parser for common chat edit commands."""
    msg = message.strip()
    lower = msg.lower()
    actions = []

    # Charter deliverable/objective/constraint/assumption
    for section, keywords in [
        ("deliverables", ["deliverable", "deliverables"]),
        ("objectives", ["objective", "objectives"]),
        ("constraints", ["constraint", "constraints"]),
        ("assumptions", ["assumption", "assumptions"]),
    ]:
        for kw in keywords:
            m = re.search(rf"add\s+{kw}[:\s]+(.+)", lower, re.I)
            if m:
                value = msg[m.start(1):].strip()
                actions.append({"field": "charter", "action": "add", "section": section, "data": {"value": value}})
                return actions

    m = re.search(r"add\s+stakeholder[:\s]+(.+?)(?:\s+role[:\s]+(.+?))?(?:\s+interest[:\s]+(.+))?$", lower, re.I)
    if m:
        name = msg[m.start(1):m.end(1)].strip()
        role = m.group(2).strip() if m.group(2) else ""
        interest = m.group(3).strip().title() if m.group(3) else "Medium"
        actions.append({"field": "charter", "action": "add", "section": "stakeholders", "data": {"name": name, "role": role, "interest": interest}})
        return actions

    m = re.search(r"(?:set|update)\s+scope[:\s]+(.+)", lower, re.I)
    if m:
        actions.append({"field": "charter", "action": "add", "section": "scope", "data": {"value": msg[m.start(1):].strip()}})
        return actions

    # WBS: add wbs 2.1 EBOM Finalization 84 days [under 2.0]
    m = re.search(r"add\s+wbs(?:\s+task)?[:\s]+([\d.]+)\s+(.+?)(?:\s+(\d+)\s*days?)?(?:\s+under\s+([\d.]+))?", lower, re.I)
    if m:
        actions.append({
            "field": "wbs", "action": "add",
            "parent_code": m.group(4),
            "data": {"code": m.group(1), "name": msg[m.start(2):m.end(2)].strip(), "duration_days": int(m.group(3) or 5)},
        })
        return actions

    m = re.search(r"remove\s+wbs[:\s]+([\d.]+)", lower, re.I)
    if m:
        actions.append({"field": "wbs", "action": "remove", "code": m.group(1)})
        return actions

    # Inventory: add inventory/material WiFi chipset required 50 available 10 units
    m = re.search(r"add\s+(?:inventory|material)[:\s]+(.+?)(?:\s+required\s+(\d+))?(?:\s+available\s+(\d+))?(?:\s+unit[s]?\s+(\w+))?", lower, re.I)
    if m:
        actions.append({
            "field": "inventory", "action": "add",
            "data": {
                "name": msg[m.start(1):m.end(1)].strip(),
                "required": int(m.group(2) or 0),
                "available": int(m.group(3) or 0),
                "unit": m.group(4) or "units",
                "status": "Pending",
            },
        })
        return actions

    m = re.search(r"remove\s+(?:inventory|material)[:\s]+(.+)", lower, re.I)
    if m:
        actions.append({"field": "inventory", "action": "remove", "data": {"name": msg[m.start(1):].strip()}})
        return actions

    # Risk: add risk Chipset delay category Supply Chain probability High impact High mitigation ...
    m = re.search(r"add\s+risk[:\s]+(.+?)(?:\s+category[:\s]+(.+?))?(?:\s+mitigation[:\s]+(.+))?$", lower, re.I)
    if m:
        title = msg[m.start(1):m.end(1)].strip()
        prob = "High" if "high" in lower else "Medium" if "medium" in lower else "Low"
        impact = prob
        actions.append({
            "field": "risks", "action": "add",
            "data": {
                "title": title,
                "category": (m.group(2) or "General").strip(),
                "probability": prob,
                "impact": impact,
                "score": 6,
                "mitigation": (m.group(3) or "").strip(),
            },
        })
        return actions

    m = re.search(r"remove\s+risk[:\s]+(.+)", lower, re.I)
    if m:
        actions.append({"field": "risks", "action": "remove", "data": {"title": msg[m.start(1):].strip()}})
        return actions

    # Maintenance: add machine SMT Line health 90
    m = re.search(r"add\s+(?:machine|maintenance)[:\s]+(.+?)(?:\s+health\s+(\d+))?(?:\s+recommendation[:\s]+(.+))?$", lower, re.I)
    if m:
        actions.append({
            "field": "maintenance", "action": "add",
            "data": {
                "name": msg[m.start(1):m.end(1)].strip(),
                "health_score": float(m.group(2) or 100),
                "failure_probability": 0.1,
                "recommendation": (m.group(3) or "").strip(),
            },
        })
        return actions

    m = re.search(r"remove\s+(?:machine|maintenance)[:\s]+(.+)", lower, re.I)
    if m:
        actions.append({"field": "maintenance", "action": "remove", "data": {"name": msg[m.start(1):].strip()}})
        return actions

    m = re.search(r"(?:set|update)\s+task\s+(.+?)\s+(?:to|status)\s+(not_started|in_progress|completed|on_hold|blocked)", msg, re.I)
    if m:
        identifier = msg[m.start(1):m.end(1)].strip()
        status = m.group(2).lower()
        actions.append({
            "field": "gantt_task",
            "action": "update",
            "wbs_code": identifier,
            "data": {"status": status, "name": identifier},
        })
        return actions

    return actions
