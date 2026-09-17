"""Merge AI-generated data with existing user-defined project content."""

import copy
from typing import Any


def _dedupe_strings(items: list) -> list:
    seen = set()
    out = []
    for item in items or []:
        key = str(item).strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def merge_charter(existing: dict | None, generated: dict) -> dict:
    existing = copy.deepcopy(existing or {})
    generated = copy.deepcopy(generated or {})
    merged = {**generated}

    for key in ("objectives", "deliverables", "success_criteria", "constraints", "assumptions"):
        merged[key] = _dedupe_strings((existing.get(key) or []) + (generated.get(key) or []))

    # Keep user scope if it was manually written and AI returns generic scope
    if existing.get("scope") and len(str(existing.get("scope", ""))) > len(str(generated.get("scope", ""))):
        merged["scope"] = existing["scope"]

    existing_stakeholders = {s.get("name", "").lower(): s for s in (existing.get("stakeholders") or []) if s.get("name")}
    for s in generated.get("stakeholders") or []:
        name = (s.get("name") or "").lower()
        if name and name not in existing_stakeholders:
            existing_stakeholders[name] = s
    merged["stakeholders"] = list(existing_stakeholders.values())

    # Preserve user-defined list entries flagged explicitly
    for key in ("objectives", "deliverables", "success_criteria", "constraints", "assumptions"):
        user_items = [x for x in (existing.get(key) or []) if isinstance(x, dict) and x.get("user_defined")]
        if user_items:
            merged[key] = _dedupe_strings(merged.get(key, []) + [x.get("value", x) if isinstance(x, dict) else x for x in user_items])

    return merged


def _merge_wbs_nodes(existing_nodes: list, generated_nodes: list) -> list:
    by_code = {n.get("code"): copy.deepcopy(n) for n in existing_nodes or [] if n.get("code")}
    result = []
    for gen in generated_nodes or []:
        code = gen.get("code")
        if code and code in by_code:
            kept = by_code.pop(code)
            kept_children = kept.get("children") or []
            gen_children = gen.get("children") or []
            kept["name"] = gen.get("name", kept.get("name"))
            kept["duration_days"] = gen.get("duration_days", kept.get("duration_days"))
            kept["level"] = gen.get("level", kept.get("level"))
            kept["children"] = _merge_wbs_nodes(kept_children, gen_children)
            if kept.get("progress") is not None:
                pass  # preserve progress/status
            result.append(kept)
        else:
            result.append(copy.deepcopy(gen))
    # Append user-only nodes not in AI output
    for leftover in by_code.values():
        result.append(leftover)
    return result


def merge_wbs(existing: list | None, generated: list) -> list:
    return _merge_wbs_nodes(existing or [], generated or [])


def _task_key(task: dict) -> str:
    return str(task.get("wbs_code") or task.get("code") or task.get("id") or task.get("name", "")).lower()


def merge_gantt(existing: dict | None, generated: dict) -> dict:
    existing = copy.deepcopy(existing or {})
    generated = copy.deepcopy(generated or {})
    existing_tasks = { _task_key(t): t for t in (existing.get("tasks") or []) }
    merged_tasks = []
    for task in generated.get("tasks") or []:
        key = _task_key(task)
        if key in existing_tasks:
            prev = existing_tasks.pop(key)
            task["progress"] = prev.get("progress", task.get("progress", 0))
            task["status"] = prev.get("status", task.get("status", _progress_to_status(task["progress"])))
            if prev.get("owner"):
                task["owner"] = prev["owner"]
        else:
            task.setdefault("status", _progress_to_status(task.get("progress", 0)))
        merged_tasks.append(task)
    for leftover in existing_tasks.values():
        merged_tasks.append(leftover)
    merged = {**generated, "tasks": merged_tasks}
    for key in ("critical_path", "critical_path_duration_days", "parallel_groups", "scheduling_method"):
        if generated.get(key) is not None:
            merged[key] = generated[key]
    if existing.get("milestones"):
        seen = {m.get("name") for m in merged.get("milestones") or []}
        merged["milestones"] = list(merged.get("milestones") or []) + [
            m for m in existing["milestones"] if m.get("name") not in seen
        ]
    return merged


def _progress_to_status(progress: float) -> str:
    p = float(progress or 0)
    if p >= 100:
        return "completed"
    if p > 0:
        return "in_progress"
    return "not_started"


def merge_list_by_name(existing: Any, generated: Any, name_key: str = "name") -> list:
    existing_items = existing if isinstance(existing, list) else (existing or {}).get("materials") or (existing or {}).get("machines") or (existing or {}).get("risks") or []
    if isinstance(generated, dict):
        gen_items = generated.get("materials") or generated.get("machines") or generated.get("risks") or []
    else:
        gen_items = generated or []
    by_name = {(item.get(name_key) or item.get("title") or "").lower(): copy.deepcopy(item) for item in existing_items if item.get(name_key) or item.get("title")}
    merged = []
    for item in gen_items:
        key = (item.get(name_key) or item.get("title") or "").lower()
        if key and key in by_name:
            prev = by_name.pop(key)
            prev.update({k: v for k, v in item.items() if k not in ("progress", "status", "user_defined") or v is not None})
            merged.append(prev)
        else:
            merged.append(copy.deepcopy(item))
    for leftover in by_name.values():
        merged.append(leftover)
    return merged


def merge_resources(existing: Any, generated: dict) -> dict:
    existing = existing if isinstance(existing, dict) else {"departments": existing or []}
    generated = copy.deepcopy(generated or {})
    existing_depts = existing.get("departments") or existing.get("allocations") or []
    gen_depts = generated.get("departments") or generated.get("allocations") or []

    by_key = {}
    for d in existing_depts:
        key = (d.get("department") or d.get("resource") or d.get("id") or "").lower()
        if key:
            by_key[key] = copy.deepcopy(d)

    merged_depts = []
    for d in gen_depts:
        key = (d.get("department") or d.get("resource") or "").lower()
        if key and key in by_key:
            prev = by_key.pop(key)
            employees = prev.get("employees") or []
            prev.update(d)
            if employees and not d.get("employees"):
                prev["employees"] = employees
            merged_depts.append(prev)
        else:
            merged_depts.append(copy.deepcopy(d))

    for leftover in by_key.values():
        merged_depts.append(leftover)

    return {
        "departments": merged_depts,
        "recommendations": _dedupe_strings((existing.get("recommendations") or []) + (generated.get("recommendations") or [])),
        "conflicts": (generated.get("conflicts") or existing.get("conflicts") or []),
    }


def merge_budget(existing: dict | None, generated: dict) -> dict:
    existing = copy.deepcopy(existing or {})
    generated = copy.deepcopy(generated or {})
    merged = {**generated}
    existing_cats = {c.get("name", "").lower(): c for c in (existing.get("categories") or []) if c.get("name")}
    merged_cats = []
    for cat in generated.get("categories") or []:
        name = cat.get("name", "").lower()
        if name in existing_cats:
            prev = existing_cats.pop(name)
            cat["actual"] = prev.get("actual", cat.get("actual"))
            merged_cats.append(cat)
        else:
            merged_cats.append(cat)
    for leftover in existing_cats.values():
        merged_cats.append(leftover)
    merged["categories"] = merged_cats
    merged["actual_cost"] = existing.get("actual_cost", generated.get("actual_cost"))
    return merged


def merge_quality(existing: dict | None, generated: dict) -> dict:
    existing = copy.deepcopy(existing or {})
    generated = copy.deepcopy(generated or {})
    merged = {**generated}
    existing_capa = {c.get("id"): c for c in (existing.get("capa_records") or []) if c.get("id")}
    for capa in generated.get("capa_records") or []:
        cid = capa.get("id")
        if cid in existing_capa:
            existing_capa[cid].update(capa)
    merged["capa_records"] = list({**{c.get("id"): c for c in generated.get("capa_records") or []}, **existing_capa}.values())
    return merged


def merge_inventory(existing: Any, generated: Any) -> dict:
    materials = merge_list_by_name(existing, generated, "name")
    alerts = []
    recs = []
    if isinstance(generated, dict):
        alerts = generated.get("alerts") or []
        recs = generated.get("recommendations") or []
    if isinstance(existing, dict):
        alerts = alerts + [a for a in (existing.get("alerts") or []) if a not in alerts]
        recs = _dedupe_strings((existing.get("recommendations") or []) + recs)
    return {"materials": materials, "alerts": alerts, "recommendations": recs}


def merge_risks(existing: Any, generated: Any) -> list:
    return merge_list_by_name(existing, generated, "title")


def merge_maintenance(existing: Any, generated: Any) -> dict:
    machines = merge_list_by_name(existing, generated, "name")
    extra = {}
    if isinstance(generated, dict):
        extra = {k: v for k, v in generated.items() if k != "machines"}
    if isinstance(existing, dict):
        for k, v in existing.items():
            if k != "machines" and k not in extra:
                extra[k] = v
    return {"machines": machines, **extra}
