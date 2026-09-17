import json
import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Any
from openai import OpenAI

from app.config import settings
from app.gantt_scheduler import build_gantt_from_wbs

logger = logging.getLogger(__name__)


def _parse_json(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _ensure_list(data: Any, label: str) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "wbs", "tasks", "nodes", "data"):
            if key in data and isinstance(data[key], list):
                logger.warning("%s response was wrapped in dict key '%s'; unwrapping", label, key)
                return data[key]
    logger.error("%s response is not a list: %s", label, type(data).__name__)
    raise ValueError(f"{label} must be a JSON array")


def _ensure_dict(data: Any, label: str) -> dict:
    if isinstance(data, dict):
        return data
    logger.error("%s response is not a dict: %s", label, type(data).__name__)
    raise ValueError(f"{label} must be a JSON object")


class AIService:
    def __init__(self):
        api_key = settings.openai_api_key
        self.client = None
        if api_key and not api_key.startswith("your_") and api_key != "sk-your-key-here":
            self.client = OpenAI(api_key=api_key)
            logger.info("AI service initialized with OpenAI")
        else:
            logger.info("AI service running in mock mode (no valid OPENAI_API_KEY)")

    def _call_ai(self, system_prompt: str, user_prompt: str, feature: str) -> str:
        if self.client:
            try:
                logger.info("Calling OpenAI for feature=%s", feature)
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                )
                content = response.choices[0].message.content
                logger.debug("OpenAI response for %s: %s...", feature, content[:200] if content else "")
                return content
            except Exception as exc:
                logger.exception("OpenAI call failed for feature=%s: %s", feature, exc)
        logger.info("Using mock AI response for feature=%s", feature)
        return self._mock_response(feature)

    def _mock_response(self, feature: str) -> str:
        mocks = {
            "charter": {
                "project_name": "Manufacturing Line Upgrade",
                "scope": "Upgrade production line #3 with automated assembly stations, quality inspection systems, and IoT sensors for real-time monitoring.",
                "objectives": [
                    "Increase production throughput by 25%",
                    "Reduce defect rate to below 0.5%",
                    "Achieve ROI within 18 months",
                    "Minimize production downtime during transition",
                ],
                "stakeholders": [
                    {"name": "Operations Director", "role": "Executive Sponsor", "interest": "High"},
                    {"name": "Plant Manager", "role": "Project Owner", "interest": "High"},
                    {"name": "Production Team Lead", "role": "End User", "interest": "High"},
                    {"name": "Quality Assurance Manager", "role": "Quality Lead", "interest": "Medium"},
                    {"name": "Maintenance Supervisor", "role": "Technical Lead", "interest": "Medium"},
                ],
                "deliverables": [
                    "Automated assembly station installation",
                    "Quality inspection system integration",
                    "IoT sensor network deployment",
                    "Staff training program completion",
                    "Performance validation report",
                ],
                "success_criteria": [
                    "25% throughput increase verified",
                    "Defect rate below 0.5%",
                    "Zero safety incidents during installation",
                    "All operators certified on new equipment",
                ],
                "assumptions": [
                    "Equipment delivery within 8 weeks",
                    "No major regulatory changes during project",
                    "Current facility infrastructure supports upgrades",
                ],
                "constraints": [
                    "Maximum 2-week production shutdown allowed",
                    "Budget cap of $2.5M",
                    "Must comply with ISO 9001 standards",
                ],
            },
            "wbs": [
                {"code": "1.0", "name": "Project Initiation", "level": 1, "duration_days": 14, "children": [
                    {"code": "1.1", "name": "Stakeholder Analysis", "level": 2, "duration_days": 5},
                    {"code": "1.2", "name": "Requirements Gathering", "level": 2, "duration_days": 7},
                    {"code": "1.3", "name": "Project Charter Approval", "level": 2, "duration_days": 2},
                ]},
                {"code": "2.0", "name": "Design & Engineering", "level": 1, "duration_days": 30, "children": [
                    {"code": "2.1", "name": "Layout Design", "level": 2, "duration_days": 10},
                    {"code": "2.2", "name": "Equipment Specification", "level": 2, "duration_days": 12},
                    {"code": "2.3", "name": "Safety Assessment", "level": 2, "duration_days": 8},
                ]},
                {"code": "3.0", "name": "Procurement", "level": 1, "duration_days": 45, "children": [
                    {"code": "3.1", "name": "Vendor Selection", "level": 2, "duration_days": 15},
                    {"code": "3.2", "name": "Equipment Ordering", "level": 2, "duration_days": 5},
                    {"code": "3.3", "name": "Material Procurement", "level": 2, "duration_days": 25},
                ]},
                {"code": "4.0", "name": "Installation & Commissioning", "level": 1, "duration_days": 21, "children": [
                    {"code": "4.1", "name": "Site Preparation", "level": 2, "duration_days": 5},
                    {"code": "4.2", "name": "Equipment Installation", "level": 2, "duration_days": 10},
                    {"code": "4.3", "name": "System Integration", "level": 2, "duration_days": 4},
                    {"code": "4.4", "name": "Testing & Validation", "level": 2, "duration_days": 2},
                ]},
                {"code": "5.0", "name": "Training & Handover", "level": 1, "duration_days": 14, "children": [
                    {"code": "5.1", "name": "Operator Training", "level": 2, "duration_days": 7},
                    {"code": "5.2", "name": "Documentation", "level": 2, "duration_days": 4},
                    {"code": "5.3", "name": "Project Closure", "level": 2, "duration_days": 3},
                ]},
            ],
            "gantt": {
                "tasks": [
                    {"id": 1, "name": "Project Initiation", "start": "2026-02-01", "end": "2026-02-14", "progress": 100, "dependencies": []},
                    {"id": 2, "name": "Design & Engineering", "start": "2026-02-15", "end": "2026-03-16", "progress": 60, "dependencies": [1]},
                    {"id": 3, "name": "Procurement", "start": "2026-03-01", "end": "2026-04-14", "progress": 30, "dependencies": [2]},
                    {"id": 4, "name": "Installation", "start": "2026-04-15", "end": "2026-05-05", "progress": 0, "dependencies": [3]},
                    {"id": 5, "name": "Testing & Validation", "start": "2026-05-06", "end": "2026-05-12", "progress": 0, "dependencies": [4]},
                    {"id": 6, "name": "Training & Handover", "start": "2026-05-13", "end": "2026-05-26", "progress": 0, "dependencies": [5]},
                ],
                "critical_path": [1, 2, 3, 4, 5, 6],
                "total_duration_days": 115,
                "milestones": [
                    {"name": "Charter Approved", "date": "2026-02-14"},
                    {"name": "Design Complete", "date": "2026-03-16"},
                    {"name": "Equipment Delivered", "date": "2026-04-14"},
                    {"name": "Go-Live", "date": "2026-05-26"},
                ],
            },
            "resources": {
                "departments": [
                    {"id": "dept-1", "department": "Production Engineering", "type": "department", "task": "Equipment Installation", "hours": 160, "utilization": 85, "employees": [
                        {"employee_number": "EMP-1001", "name": "John Smith", "designation": "Senior Technician"},
                        {"employee_number": "EMP-1002", "name": "David Lee", "designation": "Installation Engineer"},
                    ]},
                    {"id": "dept-2", "department": "Quality Assurance", "type": "department", "task": "Quality Inspection Setup", "hours": 80, "utilization": 60, "employees": [
                        {"employee_number": "EMP-2001", "name": "Maria Garcia", "designation": "QA Inspector"},
                    ]},
                    {"id": "dept-3", "department": "Maintenance", "type": "department", "task": "Preventive Maintenance", "hours": 64, "utilization": 55, "employees": []},
                    {"id": "res-4", "department": "CNC Machine #4", "type": "machine", "task": "Component Fabrication", "hours": 120, "utilization": 75, "employees": []},
                    {"id": "res-5", "department": "Assembly Robot ARM-01", "type": "machine", "task": "Automated Assembly", "hours": 200, "utilization": 90, "employees": []},
                    {"id": "res-6", "department": "Forklift #2", "type": "equipment", "task": "Material Handling", "hours": 40, "utilization": 45, "employees": []},
                ],
                "recommendations": [
                    "Add second shift in Production Engineering to meet installation deadline",
                    "Cross-train QA staff on installation tasks for flexibility",
                ],
                "conflicts": [
                    {"department": "CNC Machine #4", "issue": "Double-booked on Apr 20-22", "resolution": "Reschedule Task 3.2 to Apr 23"},
                ],
            },
            "budget": {
                "planned_budget": 2500000,
                "actual_cost": 1875000,
                "variance": -625000,
                "variance_percent": -25.0,
                "categories": [
                    {"name": "Equipment", "planned": 1200000, "actual": 950000, "variance": -250000},
                    {"name": "Labor", "planned": 600000, "actual": 520000, "variance": -80000},
                    {"name": "Materials", "planned": 400000, "actual": 280000, "variance": -120000},
                    {"name": "Contingency", "planned": 200000, "actual": 75000, "variance": -125000},
                    {"name": "Overhead", "planned": 100000, "actual": 50000, "variance": -50000},
                ],
                "overruns": [],
                "forecast": {"estimated_final_cost": 2200000, "confidence": "85%"},
            },
            "inventory": {
                "materials": [
                    {"name": "Steel Plates 10mm", "required": 500, "available": 450, "unit": "sheets", "status": "low", "reorder_needed": True},
                    {"name": "Hydraulic Fluid ISO 46", "required": 200, "available": 350, "unit": "liters", "status": "ok", "reorder_needed": False},
                    {"name": "Bearing Assembly SKF-6205", "required": 48, "available": 12, "unit": "units", "status": "critical", "reorder_needed": True},
                ],
                "alerts": [
                    {"material": "Bearing Assembly SKF-6205", "severity": "critical", "message": "Only 12 units available, need 48. Lead time 14 days."},
                ],
                "recommendations": ["Expedite bearing order to prevent production delay"],
            },
            "risks": {
                "risks": [
                    {"id": 1, "title": "Equipment Delivery Delay", "category": "Supply Chain", "probability": "High", "impact": "High", "score": 9, "status": "open",
                     "mitigation": "Identify backup vendors; maintain 2-week buffer in schedule"},
                    {"id": 2, "title": "Skilled Labor Shortage", "category": "Resource", "probability": "Medium", "impact": "High", "score": 6, "status": "open",
                     "mitigation": "Begin contractor engagement now; cross-train existing staff"},
                ],
                "overall_risk_level": "Medium-High",
                "top_priorities": ["Equipment Delivery Delay", "Skilled Labor Shortage"],
            },
            "quality": {
                "defect_rate": 0.8,
                "target_defect_rate": 0.5,
                "inspections": [
                    {"date": "2026-03-01", "type": "Incoming Material", "passed": 45, "failed": 2, "status": "completed"},
                ],
                "capa_records": [
                    {"id": "CAPA-001", "issue": "Surface finish defects on CNC parts", "root_cause": "Worn cutting tool", "action": "Implement tool wear monitoring", "status": "in_progress", "due_date": "2026-03-20"},
                ],
                "quality_score": 82,
                "recommendations": ["Implement statistical process control on CNC operations"],
            },
            "maintenance": {
                "machines": [
                    {"name": "CNC Mill #1", "health_score": 72, "failure_probability": 0.35, "predicted_failure_date": "2026-04-15", "recommendation": "Schedule spindle bearing replacement"},
                    {"name": "Hydraulic Press #3", "health_score": 58, "failure_probability": 0.52, "predicted_failure_date": "2026-03-28", "recommendation": "URGENT: Replace hydraulic seals and inspect pump"},
                ],
                "maintenance_schedule": [
                    {"machine": "Hydraulic Press #3", "type": "Emergency", "date": "2026-03-18", "duration_hours": 8},
                ],
                "estimated_downtime_savings": "120 hours/month with predictive maintenance",
            },
            "kpis": {
                "schedule_performance": {"spi": 0.92, "status": "slightly_behind", "percent_complete": 45},
                "cost_performance": {"cpi": 1.08, "status": "under_budget", "budget_used_percent": 75},
                "quality_metrics": {"defect_rate": 0.8, "first_pass_yield": 97.2, "status": "needs_improvement"},
                "resource_utilization": {"overall": 78, "workers": 85, "machines": 72, "equipment": 65},
                "project_health": {"score": 78, "status": "amber", "trend": "stable"},
                "milestones": {"completed": 2, "total": 6, "on_track": 4, "delayed": 0},
            },
        }
        if feature in mocks:
            return json.dumps(mocks[feature])
        logger.warning("No mock defined for feature=%s, returning empty object", feature)
        return json.dumps({})

    def generate_charter(self, project_name: str, description: str, prompt: Optional[str] = None) -> dict:
        system = "You are a manufacturing project management expert. Generate a detailed project charter as JSON with keys: project_name, scope, objectives, stakeholders, deliverables, success_criteria, assumptions, constraints."
        user = f"Project: {project_name}\nDescription: {description}\nAdditional context: {prompt or 'None'}"
        result = self._call_ai(system, user, "charter")
        try:
            return _ensure_dict(_parse_json(result), "charter")
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("Failed to parse charter: %s", exc)
            return {"raw_response": result, "error": str(exc)}

    def generate_wbs(self, project_name: str, charter: dict, prompt: Optional[str] = None) -> list:
        system = "You are a manufacturing WBS expert. Generate a Work Breakdown Structure as a JSON array. Each item must have: code, name, level, duration_days, and optional children array. Return ONLY a JSON array, no wrapper object."
        user = f"Project: {project_name}\nCharter: {json.dumps(charter)}\nContext: {prompt or 'None'}"
        result = self._call_ai(system, user, "wbs")
        try:
            return _ensure_list(_parse_json(result), "WBS")
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("Failed to parse WBS: %s", exc)
            raise ValueError(f"WBS generation failed: {exc}") from exc

    def generate_gantt(self, project_name: str, wbs: list, start_date: str, prompt: Optional[str] = None, existing_gantt: dict = None) -> dict:
        if wbs and isinstance(wbs, list) and len(wbs) > 0:
            logger.info("Building Gantt schedule from WBS (%s top-level items)", len(wbs))
            return build_gantt_from_wbs(wbs, start_date, existing_gantt)

        system = (
            "You are a project scheduling expert. Generate a Gantt chart as JSON with keys: "
            "tasks (include wbs_code, name, start, end, duration_days, progress, dependencies, is_summary), "
            "critical_path (task ids on the longest dependency chain), critical_path_duration_days, "
            "total_duration_days, milestones, scheduling_method, parallel_groups. "
            "Schedule independent tasks in parallel with overlapping dates where possible. "
            "Only sequence tasks when there is a real dependency. Compute critical path using CPM."
        )
        user = f"Project: {project_name}\nWBS: {json.dumps(wbs)}\nStart Date: {start_date}\nContext: {prompt or 'None'}"
        result = self._call_ai(system, user, "gantt")
        try:
            return _ensure_dict(_parse_json(result), "Gantt")
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("Failed to parse Gantt: %s", exc)
            raise ValueError(f"Gantt generation failed: {exc}") from exc

    def optimize_resources(self, project_name: str, tasks: list, resources: list, prompt: Optional[str] = None) -> dict:
        system = "You are a manufacturing resource optimization expert. Generate resource allocation as JSON with keys: departments (array of id, department, type, task, hours, utilization, employees), recommendations, conflicts. Use department names not individual employee names. type is 'department' for labor or 'machine'/'equipment' for assets."
        user = f"Project: {project_name}\nTasks: {json.dumps(tasks)}\nResources: {json.dumps(resources)}\nContext: {prompt or 'None'}"
        result = self._call_ai(system, user, "resources")
        try:
            return _ensure_dict(_parse_json(result), "resources")
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("Failed to parse resources: %s", exc)
            raise ValueError(f"Resource optimization failed: {exc}") from exc

    def analyze_budget(self, project_name: str, budget_data: dict, prompt: Optional[str] = None) -> dict:
        system = "You are a manufacturing cost analyst. Analyze budget vs actual costs as JSON with keys: planned_budget, actual_cost, variance, variance_percent, categories, overruns, forecast."
        user = f"Project: {project_name}\nBudget Data: {json.dumps(budget_data)}\nContext: {prompt or 'None'}"
        result = self._call_ai(system, user, "budget")
        try:
            return _ensure_dict(_parse_json(result), "budget")
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("Failed to parse budget: %s", exc)
            raise ValueError(f"Budget analysis failed: {exc}") from exc

    def plan_inventory(self, project_name: str, materials: list, prompt: Optional[str] = None) -> dict:
        system = "You are a manufacturing inventory planner. Generate material planning analysis as JSON with keys: materials, alerts, recommendations."
        user = f"Project: {project_name}\nMaterials: {json.dumps(materials)}\nContext: {prompt or 'None'}"
        result = self._call_ai(system, user, "inventory")
        try:
            return _ensure_dict(_parse_json(result), "inventory")
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("Failed to parse inventory: %s", exc)
            raise ValueError(f"Inventory planning failed: {exc}") from exc

    def analyze_risks(self, project_name: str, project_data: dict, prompt: Optional[str] = None) -> dict:
        system = "You are a manufacturing risk management expert. Generate risk analysis as JSON with keys: risks, overall_risk_level, top_priorities."
        user = f"Project: {project_name}\nProject Data: {json.dumps(project_data)}\nContext: {prompt or 'None'}"
        result = self._call_ai(system, user, "risks")
        try:
            data = _ensure_dict(_parse_json(result), "risks")
            if "risks" not in data and isinstance(data.get("items"), list):
                data["risks"] = data["items"]
            return data
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("Failed to parse risks: %s", exc)
            raise ValueError(f"Risk analysis failed: {exc}") from exc

    def analyze_quality(self, project_name: str, quality_data: dict, prompt: Optional[str] = None) -> dict:
        system = "You are a manufacturing quality management expert. Generate quality analysis as JSON with keys: defect_rate, target_defect_rate, inspections, capa_records, quality_score, recommendations."
        user = f"Project: {project_name}\nQuality Data: {json.dumps(quality_data)}\nContext: {prompt or 'None'}"
        result = self._call_ai(system, user, "quality")
        try:
            return _ensure_dict(_parse_json(result), "quality")
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("Failed to parse quality: %s", exc)
            raise ValueError(f"Quality analysis failed: {exc}") from exc

    def predict_maintenance(self, machines: list, prompt: Optional[str] = None) -> dict:
        system = "You are a predictive maintenance expert for manufacturing. Generate maintenance predictions as JSON with keys: machines, maintenance_schedule, estimated_downtime_savings."
        user = f"Machines: {json.dumps(machines)}\nContext: {prompt or 'None'}"
        result = self._call_ai(system, user, "maintenance")
        try:
            return _ensure_dict(_parse_json(result), "maintenance")
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("Failed to parse maintenance: %s", exc)
            raise ValueError(f"Maintenance prediction failed: {exc}") from exc

    def generate_kpis(self, project_name: str, project_data: dict, prompt: Optional[str] = None) -> dict:
        system = "You are a manufacturing KPI analyst. Generate project KPI dashboard data as JSON with keys: schedule_performance, cost_performance, quality_metrics, resource_utilization, project_health, milestones."
        user = f"Project: {project_name}\nProject Data: {json.dumps(project_data)}\nContext: {prompt or 'None'}"
        result = self._call_ai(system, user, "kpis")
        try:
            return _ensure_dict(_parse_json(result), "KPIs")
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("Failed to parse KPIs: %s", exc)
            raise ValueError(f"KPI generation failed: {exc}") from exc

    def chat(self, message: str, project_context: dict, history: list) -> dict:
        system = """You are an AI Project Assistant for manufacturing project management. You help with:
- Project planning, scheduling, and tracking
- Resource allocation and optimization
- Budget and cost analysis
- Risk identification and mitigation
- Quality management and CAPA
- Inventory and material planning
- Predictive maintenance recommendations
- KPI analysis and project health

Provide concise, actionable advice based on manufacturing best practices. Reference specific project data when available.

When the user asks to ADD, UPDATE, or REMOVE items in the charter, WBS, inventory, risks, or maintenance, include a JSON block at the very end of your response:
```json
{"actions": [{"field": "charter|wbs|inventory|risks|maintenance", "action": "add|remove|update", "section": "...", "data": {...}}]}
```
Only include actions when the user clearly wants to modify project data."""

        context = f"\n\nCurrent Project Context:\n{json.dumps(project_context, indent=2, default=str)}" if project_context else ""
        messages = [{"role": "system", "content": system + context}]

        for msg in history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": message})

        if self.client:
            try:
                logger.info("Chat request: %s...", message[:80])
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7,
                )
                content = response.choices[0].message.content
                return self._parse_chat_response(content)
            except Exception as exc:
                logger.exception("Chat OpenAI call failed: %s", exc)

        return self._chat_mock(message, project_context)

    def _parse_chat_response(self, content: str) -> dict:
        actions = []
        reply = content
        match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
        if match:
            try:
                payload = json.loads(match.group(1))
                actions = payload.get("actions", [])
                reply = content[: match.start()].strip()
            except json.JSONDecodeError:
                pass
        return {"reply": reply, "actions": actions}

    def _chat_mock(self, message: str, project_context: dict) -> dict:
        from app.project_editor import parse_chat_actions

        actions = parse_chat_actions(message, project_context)
        if actions:
            return {
                "reply": "I'll apply that change to the project now.",
                "actions": actions,
            }

        msg_lower = message.lower()
        project_name = project_context.get("name", "the project") if project_context else "your project"

        if any(w in msg_lower for w in ["status", "progress", "summary"]):
            return {"reply": f"""**Project Status Summary for {project_name}**

📊 **Overall Progress:** 45% complete
📅 **Schedule:** Slightly behind (SPI: 0.92) — Design phase running 3 days over
💰 **Budget:** Under budget (CPI: 1.08) — $625K remaining of $2.5M
⚠️ **Top Risk:** Equipment delivery delay (High probability, High impact)
🔧 **Maintenance Alert:** Hydraulic Press #3 needs urgent attention (52% failure probability)
📦 **Inventory:** Bearing Assembly SKF-6205 critically low (12/48 units)

**Recommendations:**
1. Expedite bearing procurement to avoid production delay
2. Schedule emergency maintenance for Hydraulic Press #3
3. Consider adding resources to Design phase to recover schedule""", "actions": []}

        if any(w in msg_lower for w in ["risk", "risks"]):
            return {"reply": f"""**Risk Analysis for {project_name}**

🔴 **Critical Risks:**
1. **Equipment Delivery Delay** (Score: 9) — High probability of vendor delays. Mitigation: Identify backup vendors, add 2-week buffer.
2. **Skilled Labor Shortage** (Score: 6) — Medium probability. Mitigation: Engage contractors early, cross-train staff.

**Overall Risk Level:** Medium-High
**Action Required:** Review mitigation plans for top 2 risks this week.""", "actions": []}

        if any(w in msg_lower for w in ["budget", "cost", "spend"]):
            return {"reply": f"""**Budget Analysis for {project_name}**

**Total:** $2.5M planned vs $1.875M actual (-25% under budget)
**Forecast:** Estimated final cost $2.2M (85% confidence)
**Status:** Healthy — no overruns detected""", "actions": []}

        if any(w in msg_lower for w in ["schedule", "timeline", "gantt", "delay"]):
            return {"reply": f"""**Schedule Analysis for {project_name}**

📅 **Timeline:** Feb 1 - May 26, 2026 (115 days total)
⏱️ **Current Phase:** Design & Engineering (60% complete)
🎯 **Next Milestone:** Design Complete — Mar 16, 2026

**Recommendation:** Fast-track safety assessment approval and begin vendor selection in parallel.""", "actions": []}

        return {"reply": f"""I can help you with {project_name}. Ask about status, risks, budget, schedule, quality, inventory, or maintenance.

You can also modify project data, for example:
- "Add deliverable: Final test report"
- "Add risk: Chipset shortage category Supply Chain"
- "Add inventory: WiFi chipset required 50 available 10"
- "Add wbs 2.6 Regulatory Testing 14 days under 2.0"
- "Add machine: RF Test Chamber health 95"
""", "actions": []}


ai_service = AIService()
