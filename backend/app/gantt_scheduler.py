"""Parallel-aware Gantt scheduling and critical path analysis."""

from __future__ import annotations

import copy
from datetime import datetime, timedelta
from typing import Any

GATE_KEYWORDS = (
    "approval",
    "sign-off",
    "signoff",
    "sign off",
    "review",
    "closure",
    "handover",
    "gate",
    "validation",
    "commissioning",
    "go/no-go",
    "go live",
)


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def _format_date(value: datetime) -> str:
    return value.strftime("%Y-%m-%d")


def _progress_status(progress: float, status: str | None = None) -> str:
    if status:
        return status
    if progress >= 100:
        return "completed"
    if progress > 0:
        return "in_progress"
    return "not_started"


def _is_gate_task(node: dict, siblings: list, index: int) -> bool:
    if node.get("sequential") or node.get("depends_on_siblings"):
        return True
    name = (node.get("name") or "").lower()
    if any(keyword in name for keyword in GATE_KEYWORDS):
        return True
    if index == len(siblings) - 1 and len(siblings) > 1 and not node.get("children"):
        duration = int(node.get("duration_days") or 0)
        sibling_durations = [int(s.get("duration_days") or 0) for s in siblings[:-1] if not s.get("children")]
        if sibling_durations and duration <= max(max(sibling_durations) * 0.35, 1) and duration <= 7:
            return True
    return False


def _task_lookup(existing_gantt: dict | None) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    if not existing_gantt or not isinstance(existing_gantt, dict):
        return lookup
    for task in existing_gantt.get("tasks") or []:
        for key in (task.get("wbs_code"), task.get("name")):
            if key:
                lookup[str(key).lower()] = task
    return lookup


def _existing_task_state(node: dict, lookup: dict[str, dict], preserve_ids: bool = False) -> dict[str, Any]:
    prev = lookup.get(str(node.get("code", "")).lower()) or lookup.get(str(node.get("name", "")).lower())
    if not prev:
        progress = float(node.get("progress") or 0)
        return {
            "progress": progress,
            "status": node.get("status") or _progress_status(progress),
            "owner": node.get("owner"),
            "task_id": None,
        }
    progress = float(prev.get("progress", node.get("progress", 0)))
    return {
        "progress": progress,
        "status": prev.get("status") or node.get("status") or _progress_status(progress),
        "owner": prev.get("owner") or node.get("owner"),
        "task_id": prev.get("id") if preserve_ids else None,
    }


def _next_task_id(counter: list[int]) -> int:
    value = counter[0]
    counter[0] += 1
    return value


def _task_by_id(tasks: list[dict], task_id: int | None) -> dict | None:
    if task_id is None:
        return None
    for task in tasks:
        if task.get("id") == task_id:
            return task
    return None


def _add_dependency(tasks: list[dict], task_id: int, dep_id: int) -> None:
    task = _task_by_id(tasks, task_id)
    if not task or dep_id == task_id:
        return
    deps = task.setdefault("dependencies", [])
    if dep_id not in deps:
        deps.append(dep_id)


def _schedule_node(
    node: dict,
    start: datetime,
    tasks: list[dict],
    counter: list[int],
    lookup: dict[str, dict],
    depth: int,
    parallel: bool,
    phase_predecessor_id: int | None,
) -> tuple[datetime, datetime, int | None]:
    code = node.get("code", "")
    children = node.get("children") or []
    state = _existing_task_state(node, lookup)
    task_id = state["task_id"] or _next_task_id(counter)

    if children:
        summary_idx = len(tasks)
        tasks.append(
            {
                "id": task_id,
                "wbs_code": code,
                "name": node.get("name", "Task"),
                "start": _format_date(start),
                "end": _format_date(start),
                "duration_days": 0,
                "progress": state["progress"],
                "status": state["status"],
                "dependencies": [phase_predecessor_id] if phase_predecessor_id else [],
                "is_summary": True,
                "level": node.get("level", depth),
                "owner": state.get("owner"),
                "parallel_group": None,
            }
        )

        child_start = start
        child_ends: list[datetime] = []
        child_ids: list[int] = []
        parallel_group_ids: list[int] = []
        regular_children: list[tuple[dict, int]] = []
        gate_nodes: list[tuple[dict, int]] = []

        for index, child in enumerate(children):
            if _is_gate_task(child, children, index):
                gate_nodes.append((child, index))
            else:
                regular_children.append((child, index))

        child_entry_pred = phase_predecessor_id if depth == 1 else None

        if len(regular_children) > 1:
            for child, _ in regular_children:
                _, child_end, child_summary_id = _schedule_node(
                    child,
                    child_start,
                    tasks,
                    counter,
                    lookup,
                    depth + 1,
                    parallel=True,
                    phase_predecessor_id=child_entry_pred,
                )
                child_ends.append(child_end)
                resolved_id = child_summary_id or tasks[-1]["id"]
                child_ids.append(resolved_id)
                parallel_group_ids.append(resolved_id)
        else:
            for child, _ in regular_children:
                _, child_end, child_summary_id = _schedule_node(
                    child,
                    child_start,
                    tasks,
                    counter,
                    lookup,
                    depth + 1,
                    parallel=False,
                    phase_predecessor_id=child_entry_pred,
                )
                child_ends.append(child_end)
                child_ids.append(child_summary_id or tasks[-1]["id"])

        branch_end = max(child_ends) if child_ends else start
        for gate_node, _ in gate_nodes:
            gate_start = branch_end + timedelta(days=1)
            _, gate_end, gate_summary_id = _schedule_node(
                gate_node,
                gate_start,
                tasks,
                counter,
                lookup,
                depth + 1,
                parallel=False,
                phase_predecessor_id=None,
            )
            gate_task_id = gate_summary_id or tasks[-1]["id"]
            for dep_id in child_ids:
                for leaf_id in _leaf_descendants(dep_id, tasks):
                    _add_dependency(tasks, gate_task_id, leaf_id)
            child_ends.append(gate_end)
            child_ids.append(gate_task_id)

        summary_end = max(child_ends) if child_ends else start
        tasks[summary_idx]["start"] = _format_date(start)
        tasks[summary_idx]["end"] = _format_date(summary_end)
        tasks[summary_idx]["duration_days"] = (summary_end - start).days + 1
        if len(regular_children) > 1:
            tasks[summary_idx]["parallel_group"] = code
            for tid in parallel_group_ids:
                task = _task_by_id(tasks, tid)
                if task:
                    task["parallel_group"] = code
        return start, summary_end, task_id

    duration = max(int(node.get("duration_days") or 5), 1)
    end = start + timedelta(days=duration - 1)
    dependencies = [phase_predecessor_id] if phase_predecessor_id else []
    tasks.append(
        {
            "id": task_id,
            "wbs_code": code,
            "name": node.get("name", "Task"),
            "start": _format_date(start),
            "end": _format_date(end),
            "duration_days": duration,
            "progress": state["progress"],
            "status": state["status"],
            "dependencies": [d for d in dependencies if d],
            "is_summary": False,
            "level": node.get("level", depth),
            "owner": state.get("owner"),
            "parallel_group": code.rsplit(".", 1)[0] if parallel and "." in code else None,
        }
    )
    return start, end, task_id


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


def _is_top_level_wbs(code: str) -> bool:
    if not code:
        return False
    parts = str(code).split(".")
    return len(parts) == 2 and parts[1] == "0"


def _direct_wbs_children(parent_code: str, tasks: list[dict]) -> list[dict]:
    if not parent_code:
        return []
    parent_depth = len(str(parent_code).split("."))
    results = []
    prefix = parent_code + "."
    for task in tasks:
        code = task.get("wbs_code") or ""
        if not code.startswith(prefix):
            continue
        if len(code.split(".")) == parent_depth + 1:
            results.append(task)
    return sorted(results, key=lambda t: _wbs_code_key(t.get("wbs_code")))


def _leaf_descendants(task_id: int, tasks: list[dict]) -> list[int]:
    task = _task_by_id(tasks, task_id)
    if not task:
        return []
    if not task.get("is_summary"):
        return [task_id]
    prefix = (task.get("wbs_code") or "") + "."
    leaves = [
        t["id"]
        for t in tasks
        if (t.get("wbs_code") or "").startswith(prefix) and not t.get("is_summary")
    ]
    return leaves if leaves else [task_id]


def _phase_leaves(phase_summary: dict, tasks: list[dict]) -> list[dict]:
    phase_code = phase_summary.get("wbs_code") or ""
    base = phase_code.split(".")[0]
    return [
        t for t in tasks
        if not t.get("is_summary")
        and (t.get("wbs_code") or "").startswith(f"{base}.")
        and (t.get("wbs_code") or "") != phase_code
    ]


def _phase_exit_task_ids(phase_summary: dict, tasks: list[dict]) -> list[int]:
    """Identify the task(s) that must finish before the next phase can start."""
    leaves = _phase_leaves(phase_summary, tasks)
    if not leaves:
        return [phase_summary["id"]]

    gates = [
        t for t in leaves
        if any(k in (t.get("name") or "").lower() for k in GATE_KEYWORDS)
        or len(t.get("dependencies") or []) > 1
    ]
    if gates:
        latest_gate = max(gates, key=lambda t: (t.get("end") or "", t.get("duration_days") or 0))
        return [latest_gate["id"]]

    latest = max(leaves, key=lambda t: (t.get("end") or "", t.get("duration_days") or 0))
    return [latest["id"]]


def _wire_phase_dependencies(tasks: list[dict]) -> None:
    """Connect phases end-to-start through each phase's exit milestone."""
    top_phases = sorted(
        [t for t in tasks if t.get("is_summary") and _is_top_level_wbs(t.get("wbs_code"))],
        key=lambda t: _wbs_code_key(t.get("wbs_code")),
    )
    top_phase_ids = {p["id"] for p in top_phases}
    for index, phase in enumerate(top_phases):
        if index == 0:
            continue
        prev_phase = top_phases[index - 1]
        exit_ids = _phase_exit_task_ids(prev_phase, tasks)
        prefix = (phase.get("wbs_code") or "").split(".")[0] + "."
        for task in tasks:
            code = task.get("wbs_code") or ""
            if not code.startswith(prefix) or task.get("is_summary") or _is_top_level_wbs(code):
                continue
            task["dependencies"] = [
                d for d in (task.get("dependencies") or []) if d not in top_phase_ids
            ]
            for exit_id in exit_ids:
                _add_dependency(tasks, task["id"], exit_id)


def _resolve_predecessors(task: dict, by_id: dict[int, dict], tasks: list[dict]) -> list[int]:
    """Expand summary dependencies to the leaf tasks that must finish first."""
    all_by_id = {t["id"]: t for t in tasks}
    resolved: list[int] = []
    for dep in task.get("dependencies") or []:
        if dep not in all_by_id:
            continue
        dep_task = all_by_id[dep]
        if dep_task.get("is_summary"):
            leaves = [
                leaf_id for leaf_id in _leaf_descendants(dep, tasks)
                if leaf_id in all_by_id and not all_by_id[leaf_id].get("is_summary")
            ]
            resolved.extend(leaves)
        else:
            resolved.append(dep)
    return list(dict.fromkeys(resolved))


def _day_offset(project_start: datetime, date_value: datetime) -> int:
    return (date_value - project_start).days


def _topological_order(tasks: list[dict]) -> list[dict]:
    by_id = {t["id"]: t for t in tasks}
    indegree = {t["id"]: 0 for t in tasks}
    graph: dict[int, list[int]] = {t["id"]: [] for t in tasks}

    for task in tasks:
        for dep in task.get("dependencies") or []:
            if dep in by_id:
                graph[dep].append(task["id"])
                indegree[task["id"]] += 1

    queue = [tid for tid, deg in indegree.items() if deg == 0]
    ordered = []
    while queue:
        current = queue.pop(0)
        ordered.append(by_id[current])
        for nxt in graph[current]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if len(ordered) != len(tasks):
        return tasks
    return ordered


def compute_critical_path(tasks: list[dict], project_start: datetime) -> dict[str, Any]:
    """Critical Path Method — returns the longest dependent leaf chain from start to finish."""
    if not tasks:
        return {"critical_path": [], "critical_path_duration_days": 0, "task_slack": {}}

    all_by_id = {t["id"]: t for t in tasks}
    schedule_tasks = [t for t in tasks if not t.get("is_summary")]
    if not schedule_tasks:
        schedule_tasks = list(tasks)
    by_id = {t["id"]: t for t in schedule_tasks}
    ordered = _topological_order(schedule_tasks)

    es: dict[int, int] = {}
    ef: dict[int, int] = {}
    for task in ordered:
        duration = max(int(task.get("duration_days") or 1), 1)
        preds = [p for p in _resolve_predecessors(task, all_by_id, tasks) if p in ef]
        if preds:
            start_day = max(ef[p] + 1 for p in preds)
        else:
            start_day = 0
        es[task["id"]] = max(start_day, 0)
        ef[task["id"]] = es[task["id"]] + duration - 1

    project_finish = max(ef.values()) if ef else 0
    ls: dict[int, int] = {}

    successors: dict[int, list[int]] = {tid: [] for tid in by_id}
    for task in schedule_tasks:
        for pred in _resolve_predecessors(task, all_by_id, tasks):
            if pred in successors:
                successors[pred].append(task["id"])

    for task in reversed(ordered):
        duration = max(int(task.get("duration_days") or 1), 1)
        succs = successors.get(task["id"], [])
        if succs:
            valid = [ls[s] - 1 for s in succs if s in ls]
            finish_day = min(valid) if valid else project_finish
        else:
            finish_day = project_finish
        lf = finish_day
        ls[task["id"]] = lf - duration + 1

    slack: dict[int, int] = {}
    critical_set: set[int] = set()
    for task in schedule_tasks:
        task_slack = ls[task["id"]] - es[task["id"]]
        slack[task["id"]] = task_slack
        if task_slack <= 0:
            critical_set.add(task["id"])

    chain = _extract_critical_chain(schedule_tasks, all_by_id, tasks, es, ef, critical_set, project_finish)
    _apply_display_float(tasks, schedule_tasks, es, ef, successors, set(chain))

    critical_duration = sum(
        max(int(all_by_id[tid].get("duration_days") or 1), 1) for tid in chain if tid in by_id
    )

    return {
        "critical_path": chain,
        "critical_path_duration_days": critical_duration,
        "task_slack": slack,
    }


def _extract_critical_chain(
    schedule_tasks: list[dict],
    all_by_id: dict[int, dict],
    tasks: list[dict],
    es: dict[int, int],
    ef: dict[int, int],
    critical_set: set[int],
    project_finish: int,
) -> list[int]:
    """Walk backwards from project end through critical leaf tasks."""
    critical_leaves = [t for t in schedule_tasks if t["id"] in critical_set]
    if not critical_leaves:
        return []

    end_candidates = [t for t in critical_leaves if ef.get(t["id"]) == project_finish]
    if not end_candidates:
        max_ef = max(ef.get(t["id"], 0) for t in critical_leaves)
        end_candidates = [t for t in critical_leaves if ef.get(t["id"]) == max_ef]

    current = max(end_candidates, key=lambda t: (ef.get(t["id"], 0), -es.get(t["id"], 0)))
    chain = [current["id"]]
    visited = {current["id"]}

    while True:
        preds = [p for p in _resolve_predecessors(current, all_by_id, tasks) if p in critical_set and p not in visited]
        if not preds:
            break
        current = all_by_id[max(preds, key=lambda p: ef.get(p, 0))]
        chain.append(current["id"])
        visited.add(current["id"])

    chain.reverse()
    return chain


def _parallel_group_key(task: dict) -> str:
    if task.get("parallel_group"):
        return f"pg:{task['parallel_group']}"
    code = task.get("wbs_code") or ""
    parent = code.rsplit(".", 1)[0] if "." in code else code
    return f"ps:{parent}@{task.get('start')}"


def _apply_display_float(
    tasks: list[dict],
    schedule_tasks: list[dict],
    es: dict[int, int],
    ef: dict[int, int],
    successors: dict[int, list[int]],
    critical_chain_ids: set[int],
) -> None:
    """
    Set float_days for UI: slack vs the critical parallel sibling in the same group,
    not total project-wide CPM float.
    """
    groups: dict[str, list[dict]] = {}
    for task in schedule_tasks:
        groups.setdefault(_parallel_group_key(task), []).append(task)

    grouped_ids: set[int] = set()
    for members in groups.values():
        if len(members) < 2:
            continue
        dated = [t for t in members if t.get("end")]
        if not dated:
            continue
        critical_members = [t for t in dated if t["id"] in critical_chain_ids]
        if critical_members:
            reference_end = max(_parse_date(t["end"]) for t in critical_members)
        else:
            reference_end = max(_parse_date(t["end"]) for t in dated)
        for task in dated:
            grouped_ids.add(task["id"])
            if task["id"] in critical_chain_ids:
                task["float_days"] = 0
            else:
                task_end = _parse_date(task["end"])
                task["float_days"] = max(0, (reference_end - task_end).days)

    for task in schedule_tasks:
        if task["id"] in grouped_ids:
            continue
        if task["id"] in critical_chain_ids:
            task["float_days"] = 0
            continue
        succs = successors.get(task["id"], [])
        if succs:
            task["float_days"] = min(
                max(0, es[s] - ef[task["id"]] - 1) for s in succs if s in es
            )
        else:
            task["float_days"] = 0

    for task in tasks:
        if task.get("is_summary"):
            prefix = (task.get("wbs_code") or "") + "."
            task["critical"] = any(
                t["id"] in critical_chain_ids
                for t in schedule_tasks
                if (t.get("wbs_code") or "").startswith(prefix)
            )
            task["float_days"] = 0
        else:
            task["critical"] = task["id"] in critical_chain_ids
            if task["id"] in critical_chain_ids:
                task["float_days"] = 0


def _detect_parallel_groups(tasks: list[dict]) -> list[dict]:
    groups: dict[str, dict] = {}
    for task in tasks:
        group_code = task.get("parallel_group")
        if not group_code or task.get("is_summary"):
            continue
        entry = groups.setdefault(
            group_code,
            {"group_code": group_code, "name": group_code, "task_ids": [], "task_names": []},
        )
        entry["task_ids"].append(task["id"])
        entry["task_names"].append(task.get("name"))
    return list(groups.values())


def _build_milestones(tasks: list[dict], existing_gantt: dict | None) -> list[dict]:
    if existing_gantt and isinstance(existing_gantt, dict):
        existing = existing_gantt.get("milestones") or []
        user_defined = [m for m in existing if m.get("user_defined")]
        if user_defined:
            auto = [
                {"name": "Project Start", "date": tasks[0]["start"]},
                {"name": "Project Complete", "date": max(t["end"] for t in tasks if t.get("end"))},
            ]
            seen = {m.get("name") for m in user_defined}
            return user_defined + [m for m in auto if m["name"] not in seen]

    if not tasks:
        return []
    finish = max(t["end"] for t in tasks if t.get("end"))
    mids = [t for t in tasks if not t.get("is_summary")]
    mid_date = mids[len(mids) // 2]["end"] if mids else finish
    return [
        {"name": "Project Start", "date": tasks[0]["start"]},
        {"name": "Mid-Project Review", "date": mid_date},
        {"name": "Project Complete", "date": finish},
    ]


def build_gantt_from_wbs(
    wbs: list,
    start_date: str = "2026-02-01",
    existing_gantt: dict | None = None,
) -> dict:
    """
    Build a Gantt schedule from WBS using parallel-aware rules:
    - Top-level phases run sequentially
    - Sibling tasks under the same parent run in parallel
    - Gate / approval tasks wait for sibling branches to finish
    - Critical path computed with CPM
    """
    if not wbs:
        return {
            "tasks": [],
            "critical_path": [],
            "critical_path_duration_days": 0,
            "total_duration_days": 0,
            "milestones": [],
            "scheduling_method": "parallel_aware_cpm",
            "parallel_groups": [],
        }

    lookup = _task_lookup(existing_gantt)
    tasks: list[dict] = []
    counter = [1]
    project_start = _parse_date(start_date)
    phase_cursor = project_start
    phase_predecessor_id: int | None = None

    for node in wbs:
        _, phase_end, phase_summary_id = _schedule_node(
            node,
            phase_cursor,
            tasks,
            counter,
            lookup,
            depth=1,
            parallel=False,
            phase_predecessor_id=phase_predecessor_id,
        )
        phase_predecessor_id = phase_summary_id
        phase_cursor = phase_end + timedelta(days=1)

    _wire_phase_dependencies(tasks)
    cpm = compute_critical_path(tasks, project_start)
    total_days = (
        (_parse_date(max(t["end"] for t in tasks)) - project_start).days + 1 if tasks else 0
    )

    return {
        "tasks": tasks,
        "critical_path": cpm["critical_path"],
        "critical_path_duration_days": cpm["critical_path_duration_days"],
        "total_duration_days": total_days,
        "milestones": _build_milestones(tasks, existing_gantt),
        "scheduling_method": "parallel_aware_cpm",
        "parallel_groups": _detect_parallel_groups(tasks),
    }


def reschedule_gantt_from_wbs(
    wbs: list,
    existing_gantt: dict | None,
    start_date: str,
) -> dict:
    """Rebuild schedule dates from WBS while preserving progress and user milestones."""
    merged = build_gantt_from_wbs(wbs, start_date, existing_gantt)
    if existing_gantt and isinstance(existing_gantt, dict):
        user_milestones = [m for m in (existing_gantt.get("milestones") or []) if m.get("user_defined")]
        if user_milestones:
            auto_names = {m.get("name") for m in merged.get("milestones") or []}
            merged["milestones"] = (merged.get("milestones") or []) + [
                m for m in user_milestones if m.get("name") not in auto_names
            ]
    return merged


def recompute_gantt_cpm(gantt: dict | None, start_date: str) -> dict:
    """Rewire phase dependencies and recompute critical path/float on existing tasks."""
    gantt = copy.deepcopy(gantt or {})
    tasks = gantt.get("tasks") or []
    if not tasks:
        return gantt

    _wire_phase_dependencies(tasks)
    project_start = _parse_date(start_date)
    cpm = compute_critical_path(tasks, project_start)
    gantt["tasks"] = tasks
    gantt["critical_path"] = cpm["critical_path"]
    gantt["critical_path_duration_days"] = cpm["critical_path_duration_days"]
    gantt["scheduling_method"] = gantt.get("scheduling_method") or "parallel_aware_cpm"
    gantt["parallel_groups"] = _detect_parallel_groups(tasks)
    dated = [t for t in tasks if t.get("end")]
    if dated:
        gantt["total_duration_days"] = (
            _parse_date(max(t["end"] for t in dated)) - project_start
        ).days + 1
    return gantt


def enrich_gantt_schedule(gantt: dict | None, wbs: list | None, start_date: str) -> dict:
    """Return gantt with up-to-date schedule, critical path, and float."""
    if wbs:
        return reschedule_gantt_from_wbs(wbs, gantt, start_date)
    return recompute_gantt_cpm(gantt, start_date)
