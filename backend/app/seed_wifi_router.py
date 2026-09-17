"""Seed the WiFi 6 Router project from project plan document 2026PGX110."""

from datetime import date

from app.models import Project, User


PROJECT_REF = "2026PGX110"


def get_wifi_router_project_data(owner_id: int) -> dict:
    return {
        "name": "WiFi 6 Router — Designing and Manufacturing",
        "description": (
            "Design, engineer, and validate a home WiFi 6 router — from PCB and enclosure design "
            "through firmware, mobile app, and regulatory certification — and establish feasibility "
            "for mass production. Reference: 2026PGX110. Originator: Anubhav Raj."
        ),
        "status": "planning",
        "priority": "high",
        "start_date": date(2026, 8, 1),
        "end_date": date(2027, 5, 14),
        "budget": 1770000.0,
        "actual_cost": 100000.0,
        "owner_id": owner_id,
        "health_score": 82.0,
        "charter": {
            "project_name": "WiFi 6 Router — Designing and Manufacturing",
            "project_reference": PROJECT_REF,
            "scope": (
                "In Scope: Hardware design & procurement (PCB, chipset, enclosures, EBOM); "
                "firmware/software (router OS, mobile app, GUI, cloud management); "
                "regulatory certification (FCC/EU, WiFi Alliance); prototype production and "
                "mass-production feasibility study. "
                "Out of Scope: Product marketing; hardware changes beyond approved PRD."
            ),
            "objectives": [
                "Design a home router with WiFi 6 capability, 4 LAN ports, 2 VoIP ports, and dual-band antenna",
                "Complete PCB, enclosure, and EBOM design with validated reference board",
                "Deliver boot-ready firmware, feature-complete software, and mobile/cloud management",
                "Achieve regulatory certification and QC sign-off for mass-production go/no-go",
            ],
            "deliverables": [
                "Product Requirement Document (PRD) — features",
                "PCB design document",
                "Electronics schematics",
                "XY coordinate file for production",
                "CAD design of enclosures",
                "EBOM finalization",
                "Reference board (RFB) for software development",
                "Basic software for booting reference board",
                "Software feature development",
                "Testing of software features",
                "Unit, sanity & regression testing for stability",
                "Quality assurance sign-off",
                "Readiness confirmation for mass production",
            ],
            "stakeholders": [
                {"name": "Anubhav Raj", "role": "Project Sponsor / Originator", "interest": "High"},
                {"name": "Product Manager", "role": "PRD Readiness & Go/No-Go Owner", "interest": "High"},
                {"name": "Hardware Designing Team", "role": "EBOM & RFB Lead", "interest": "High"},
                {"name": "Development / R&D Team", "role": "Software & Firmware Lead", "interest": "High"},
                {"name": "Quality Team", "role": "QC Pass & Sign-off", "interest": "High"},
                {"name": "Marketing + Designing Team", "role": "Enclosure CAD Design", "interest": "Medium"},
            ],
            "success_criteria": [
                "WiFi 6 router meets PRD feature set (4 LAN, 2 VoIP, dual-band antenna)",
                "Reference board boots with basic software within schedule",
                "All software features pass unit, sanity, and regression testing",
                "QC sign-off and mass-production readiness confirmed at week 41",
            ],
            "assumptions": [
                "Chipset availability from suppliers is confirmed in line with the EBOM schedule",
                "Manpower — designers and engineers — are available as planned across hardware, software, and QA teams",
                "Quality-passing criteria are agreed upfront and achievable within the planned QC cycle",
            ],
            "constraints": [
                "Total schedule: 41 weeks on critical path",
                "Estimated budget: ₹17,70,000 (order-of-magnitude; refine after EBOM/vendor quotes)",
                "Regulatory certification must not gate mass-production readiness",
                "No hardware customization beyond approved PRD",
            ],
        },
        "wbs": [
            {
                "code": "1.0",
                "name": "Designing",
                "level": 1,
                "duration_days": 28,
                "children": [
                    {"code": "1.1", "name": "PRD Readiness", "level": 2, "duration_days": 28},
                    {"code": "1.2", "name": "Designing & Documentation", "level": 2, "duration_days": 14},
                ],
            },
            {
                "code": "2.0",
                "name": "Hardware",
                "level": 1,
                "duration_days": 98,
                "children": [
                    {"code": "2.1", "name": "EBOM Finalization", "level": 2, "duration_days": 84},
                    {"code": "2.2", "name": "CAD Design of Enclosures", "level": 2, "duration_days": 14},
                    {"code": "2.3", "name": "PCB Design Document & Schematics", "level": 2, "duration_days": 21},
                    {"code": "2.4", "name": "XY Coordinate File for Production", "level": 2, "duration_days": 7},
                    {"code": "2.5", "name": "RFB (Reference Board) Readiness", "level": 2, "duration_days": 28},
                ],
            },
            {
                "code": "3.0",
                "name": "Software",
                "level": 1,
                "duration_days": 112,
                "children": [
                    {"code": "3.1", "name": "Basic S/W (Boot) Readiness", "level": 2, "duration_days": 28},
                    {"code": "3.2", "name": "Router OS, GUI & Cloud Management", "level": 2, "duration_days": 42},
                    {"code": "3.3", "name": "Mobile App for Management", "level": 2, "duration_days": 28},
                    {"code": "3.4", "name": "Software Feature Testing", "level": 2, "duration_days": 28},
                ],
            },
            {
                "code": "4.0",
                "name": "Mass Production",
                "level": 1,
                "duration_days": 35,
                "children": [
                    {"code": "4.1", "name": "Regulatory Certification (FCC/EU, WiFi Alliance)", "level": 2, "duration_days": 28},
                    {"code": "4.2", "name": "QC Pass", "level": 2, "duration_days": 28},
                    {"code": "4.3", "name": "Unit, Sanity & Regression Testing", "level": 2, "duration_days": 21},
                    {"code": "4.4", "name": "Ready for Mass Production (Go/No-Go)", "level": 2, "duration_days": 7},
                ],
            },
        ],
        "gantt": {
            "tasks": [
                {
                    "id": 1,
                    "wbs_code": "1.1",
                    "name": "PRD Readiness",
                    "start": "2026-08-01",
                    "end": "2026-08-28",
                    "duration_days": 28,
                    "progress": 15,
                    "dependencies": [],
                    "is_summary": False,
                    "level": 2,
                    "owner": "Product Manager",
                    "critical": True,
                },
                {
                    "id": 2,
                    "wbs_code": "2.1",
                    "name": "EBOM Finalization",
                    "start": "2026-08-29",
                    "end": "2026-11-20",
                    "duration_days": 84,
                    "progress": 0,
                    "dependencies": [1],
                    "is_summary": False,
                    "level": 2,
                    "owner": "Hardware Designing Team",
                    "critical": True,
                },
                {
                    "id": 3,
                    "wbs_code": "2.2",
                    "name": "CAD Design of Enclosure",
                    "start": "2026-08-29",
                    "end": "2026-09-11",
                    "duration_days": 14,
                    "progress": 0,
                    "dependencies": [1],
                    "is_summary": False,
                    "level": 2,
                    "owner": "Marketing + Designing Team",
                    "critical": False,
                    "float_weeks": 30,
                },
                {
                    "id": 4,
                    "wbs_code": "2.5",
                    "name": "RFB (Reference Board) Readiness",
                    "start": "2026-11-21",
                    "end": "2026-12-18",
                    "duration_days": 28,
                    "progress": 0,
                    "dependencies": [2],
                    "is_summary": False,
                    "level": 2,
                    "owner": "Hardware Designing Team",
                    "critical": True,
                },
                {
                    "id": 5,
                    "wbs_code": "3.1",
                    "name": "Basic S/W (Boot) Readiness",
                    "start": "2026-12-19",
                    "end": "2027-01-15",
                    "duration_days": 28,
                    "progress": 0,
                    "dependencies": [4],
                    "is_summary": False,
                    "level": 2,
                    "owner": "Development / R&D Team",
                    "critical": True,
                },
                {
                    "id": 6,
                    "wbs_code": "3.2",
                    "name": "Software Feature Dev. & Readiness",
                    "start": "2027-01-16",
                    "end": "2027-04-09",
                    "duration_days": 84,
                    "progress": 0,
                    "dependencies": [5],
                    "is_summary": False,
                    "level": 2,
                    "owner": "Development / R&D Team",
                    "critical": True,
                },
                {
                    "id": 7,
                    "wbs_code": "4.2",
                    "name": "QC Pass",
                    "start": "2027-04-10",
                    "end": "2027-05-07",
                    "duration_days": 28,
                    "progress": 0,
                    "dependencies": [6],
                    "is_summary": False,
                    "level": 2,
                    "owner": "Quality Team",
                    "critical": True,
                },
                {
                    "id": 8,
                    "wbs_code": "4.4",
                    "name": "Ready for Mass Production",
                    "start": "2027-05-08",
                    "end": "2027-05-14",
                    "duration_days": 7,
                    "progress": 0,
                    "dependencies": [7],
                    "is_summary": False,
                    "level": 2,
                    "owner": "Product Manager",
                    "critical": True,
                },
            ],
            "critical_path": [1, 2, 4, 5, 6, 7, 8],
            "total_duration_days": 287,
            "milestones": [
                {"name": "Charter Approval / Project Start", "date": "2026-08-01"},
                {"name": "PRD Sign-off", "date": "2026-08-28"},
                {"name": "EBOM Finalized", "date": "2026-11-20"},
                {"name": "RFB Ready for Software", "date": "2026-12-18"},
                {"name": "Software Feature Complete", "date": "2027-04-09"},
                {"name": "Mass Production Go/No-Go", "date": "2027-05-14"},
            ],
        },
        "resources": {
            "departments": [
                {
                    "department": "Product Management",
                    "type": "department",
                    "task": "PRD Readiness & Go/No-Go",
                    "hours": 320,
                    "utilization": 40,
                    "employees": [
                        {"employee_number": "PM-001", "name": "Product Manager", "designation": "Product Manager"},
                    ],
                },
                {
                    "department": "Hardware Designing Team",
                    "type": "department",
                    "task": "EBOM, PCB, Schematics, RFB",
                    "hours": 1680,
                    "utilization": 75,
                    "employees": [
                        {"employee_number": "HW-001", "name": "Hardware Design Lead", "designation": "Lead Hardware Engineer"},
                        {"employee_number": "HW-002", "name": "PCB Designer", "designation": "Senior PCB Designer"},
                        {"employee_number": "HW-003", "name": "Schematic Engineer", "designation": "Electronics Engineer"},
                    ],
                },
                {
                    "department": "Development / R&D Team",
                    "type": "department",
                    "task": "Firmware, Router OS, Mobile App",
                    "hours": 2240,
                    "utilization": 80,
                    "employees": [
                        {"employee_number": "SW-001", "name": "Software / R&D Lead", "designation": "Engineering Manager"},
                        {"employee_number": "SW-002", "name": "Firmware Engineer", "designation": "Senior Firmware Developer"},
                        {"employee_number": "SW-003", "name": "Mobile App Developer", "designation": "Full Stack Developer"},
                    ],
                },
                {
                    "department": "Quality Team",
                    "type": "department",
                    "task": "QC Pass & Regression Testing",
                    "hours": 560,
                    "utilization": 55,
                    "employees": [
                        {"employee_number": "QA-001", "name": "Quality Lead", "designation": "QA Manager"},
                        {"employee_number": "QA-002", "name": "Test Engineer", "designation": "QA Engineer"},
                    ],
                },
                {
                    "department": "Marketing + Designing Team",
                    "type": "department",
                    "task": "CAD Design of Enclosure",
                    "hours": 160,
                    "utilization": 25,
                    "employees": [
                        {"employee_number": "MD-001", "name": "Industrial Designer", "designation": "CAD Designer"},
                    ],
                },
            ],
            "recommendations": [
                "Confirm resource allocation at charter approval across Hardware and R&D teams",
                "Run enclosure CAD in parallel — it has 30 weeks float and does not extend the critical path",
            ],
            "conflicts": [],
        },
        "budget_details": {
            "planned_budget": 1770000,
            "actual_cost": 100000,
            "variance": 1670000,
            "currency": "INR",
            "categories": [
                {"name": "Designing / Documentation", "planned": 100000, "actual": 100000, "variance": 0},
                {"name": "Raw Material Procurement", "planned": 20000, "actual": 0, "variance": 20000},
                {"name": "CAD Designing / Enclosures", "planned": 50000, "actual": 0, "variance": 50000},
                {"name": "Manpower Resource Costing", "planned": 1500000, "actual": 0, "variance": 1500000},
            ],
            "forecast": {"estimated_final_cost": 1770000, "confidence": "order-of-magnitude"},
        },
        "inventory": {
            "materials": [
                {"name": "WiFi 6 Chipset (Dual-band)", "required": 50, "available": 0, "unit": "units", "status": "Pending EBOM"},
                {"name": "PCB Board (4-layer)", "required": 100, "available": 0, "unit": "boards", "status": "Pending EBOM"},
                {"name": "Router Enclosure (ABS)", "required": 50, "available": 0, "unit": "units", "status": "Pending CAD"},
                {"name": "Dual-band Antenna Assembly", "required": 50, "available": 0, "unit": "units", "status": "Pending EBOM"},
                {"name": "Gigabit LAN Port (x4)", "required": 200, "available": 0, "unit": "connectors", "status": "Pending EBOM"},
                {"name": "VoIP Port Module (x2)", "required": 100, "available": 0, "unit": "modules", "status": "Pending EBOM"},
                {"name": "Power Supply Unit (12V/2A)", "required": 50, "available": 0, "unit": "units", "status": "Pending EBOM"},
                {"name": "Flash Memory (Firmware)", "required": 50, "available": 0, "unit": "units", "status": "Pending EBOM"},
            ],
        },
        "risks": [
            {
                "title": "Chipset availability",
                "category": "Supply Chain",
                "probability": "High",
                "impact": "High",
                "score": 9,
                "mitigation": "Dual-source chipset vendors early; place indicative orders at PRD sign-off",
            },
            {
                "title": "Manpower / designer & engineer availability",
                "category": "Resource",
                "probability": "Medium",
                "impact": "High",
                "score": 6,
                "mitigation": "Confirm resource allocation at charter approval; flag contention across Hardware and R&D teams",
            },
            {
                "title": "Quality-passing criteria",
                "category": "Quality",
                "probability": "Medium",
                "impact": "Medium",
                "score": 4,
                "mitigation": "Agree QC criteria and test plan during PRD phase, not at QC stage",
            },
            {
                "title": "Regulatory certification (FCC/EU, WiFi Alliance)",
                "category": "Compliance",
                "probability": "Medium",
                "impact": "High",
                "score": 6,
                "mitigation": "Start certification pre-work alongside EBOM/procurement rather than after QC",
            },
        ],
        "quality": {
            "defect_rate": 0,
            "target_defect_rate": 1.0,
            "quality_score": 0,
            "first_pass_yield": 0,
            "capa_records": [],
            "test_plan_status": "To be defined during PRD phase",
        },
        "maintenance": {
            "machines": [
                {
                    "name": "SMT Pick-and-Place Line",
                    "health_score": 92,
                    "failure_probability": 0.08,
                    "predicted_failure_date": "2027-02-15",
                    "recommendation": "Schedule preventive maintenance before prototype build",
                },
                {
                    "name": "ICT / Functional Test Bench",
                    "health_score": 88,
                    "failure_probability": 0.12,
                    "predicted_failure_date": "2027-03-01",
                    "recommendation": "Calibrate test fixtures before RFB validation",
                },
                {
                    "name": "RF Chamber (WiFi 6 Testing)",
                    "health_score": 95,
                    "failure_probability": 0.05,
                    "predicted_failure_date": "2027-06-01",
                    "recommendation": "Book RF chamber for certification pre-tests in parallel with EBOM",
                },
            ],
        },
        "kpis": {
            "schedule_performance": {"spi": 1.0, "status": "On Track", "planned_completion": "2027-05-14"},
            "cost_performance": {"cpi": 1.0, "budget_used_pct": 5.6},
            "quality_metrics": {"defect_rate": 0, "first_pass_yield": 0},
            "resource_utilization": {"overall": 55},
            "project_health": {"score": 82, "status": "Planning — Charter Draft"},
            "milestones": {"completed": 0, "total": 8},
        },
    }


def seed_wifi_router_project(db) -> Project | None:
    """Insert WiFi Router project if it does not already exist. Returns the project."""
    existing = db.query(Project).filter(Project.name.like("WiFi 6 Router%")).first()
    if existing:
        return existing

    owner = db.query(User).filter(User.username == "pm_user").first()
    if not owner:
        owner = db.query(User).filter(User.username == "admin").first()
    if not owner:
        return None

    data = get_wifi_router_project_data(owner.id)
    project = Project(**data)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
