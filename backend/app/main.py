import logging
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.config import settings
from app.logging_config import setup_logging, get_logger, LOG_FILE
from app.database import engine, Base, SessionLocal
from app.models import User, Project, Task, Resource, Material, Machine
from app.auth import get_password_hash
from app.routes import auth, projects, ai_features
from app.seed_wifi_router import seed_wifi_router_project

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="ProjectIQ",
    description="AI-powered project management for manufacturing sector",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 1)
    logger.info(
        "%s %s -> %s (%sms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check backend logs for details."},
    )


app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(ai_features.router)


def _repair_project_json_fields(db):
    """Fix corrupted JSON fields that can crash the frontend."""
    repaired = 0
    for project in db.query(Project).all():
        changed = False
        if project.wbs is not None and not isinstance(project.wbs, list):
            logger.warning("Repairing invalid WBS for project id=%s (type=%s)", project.id, type(project.wbs).__name__)
            project.wbs = []
            changed = True
        if project.risks is not None and isinstance(project.risks, dict):
            project.risks = project.risks.get("risks", [])
            changed = True
        if project.resources is not None and isinstance(project.resources, dict) and "allocations" in project.resources:
            pass  # resources tab handles dict shape
        if project.inventory is not None and isinstance(project.inventory, dict) and "materials" in project.inventory:
            pass  # inventory tab handles dict shape
        if changed:
            repaired += 1
    if repaired:
        db.commit()
        logger.info("Repaired JSON fields on %s project(s)", repaired)


def _seed_demo_data(db):
    if db.query(User).filter(User.username == "admin").first():
        return

    logger.info("Seeding demo users and project data")
    admin = User(
        username="admin",
        email="admin@manufacturing.com",
        hashed_password=get_password_hash("admin123"),
        full_name="System Administrator",
        role="admin",
    )
    db.add(admin)

    demo_user = User(
        username="pm_user",
        email="pm@manufacturing.com",
        hashed_password=get_password_hash("pm123"),
        full_name="Project Manager",
        role="project_manager",
    )
    db.add(demo_user)
    db.commit()

    demo_user = db.query(User).filter(User.username == "pm_user").first()

    if not db.query(Project).filter(Project.owner_id == demo_user.id).first():
        demo_project = Project(
            name="Production Line Upgrade - Line #3",
            description="Upgrade production line #3 with automated assembly stations, quality inspection systems, and IoT sensors for real-time monitoring.",
            status="in_progress",
            priority="high",
            budget=2500000.0,
            actual_cost=1875000.0,
            owner_id=demo_user.id,
            health_score=78.0,
        )
        db.add(demo_project)

    if not db.query(Resource).first():
        db.add_all([
            Resource(name="John Smith", type="worker", availability=85, cost_per_hour=45, skills=["installation", "welding"]),
            Resource(name="Maria Garcia", type="worker", availability=60, cost_per_hour=50, skills=["quality", "inspection"]),
            Resource(name="CNC Mill #1", type="machine", availability=72, cost_per_hour=120),
            Resource(name="Assembly Robot ARM-01", type="machine", availability=90, cost_per_hour=200),
            Resource(name="Forklift #2", type="equipment", availability=45, cost_per_hour=35),
        ])

    if not db.query(Material).first():
        db.add_all([
            Material(name="Steel Plates 10mm", sku="STL-10MM", quantity=450, unit="sheets", reorder_level=100, unit_cost=85, supplier="SteelCo Inc"),
            Material(name="Bearing Assembly SKF-6205", sku="BRG-SKF6205", quantity=12, unit="units", reorder_level=20, unit_cost=45, supplier="BearTech Ltd", lead_time_days=14),
            Material(name="Hydraulic Fluid ISO 46", sku="HYD-ISO46", quantity=350, unit="liters", reorder_level=100, unit_cost=12, supplier="FluidPro"),
            Material(name="Welding Electrodes E7018", sku="WLD-E7018", quantity=85, unit="kg", reorder_level=50, unit_cost=8, supplier="WeldSupply Co"),
        ])

    if not db.query(Machine).first():
        db.add_all([
            Machine(name="CNC Mill #1", type="CNC", status="operational", health_score=72, failure_probability=0.35, operating_hours=12500),
            Machine(name="Hydraulic Press #3", type="Press", status="operational", health_score=58, failure_probability=0.52, operating_hours=8900),
            Machine(name="Assembly Robot ARM-01", type="Robot", status="operational", health_score=91, failure_probability=0.08, operating_hours=6200),
            Machine(name="Conveyor System B", type="Conveyor", status="operational", health_score=85, failure_probability=0.15, operating_hours=15000),
        ])

    db.commit()


@app.on_event("startup")
def startup():
    logger.info("Starting ProjectIQ")
    logger.info("Log file: %s", LOG_FILE)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _repair_project_json_fields(db)
        _seed_demo_data(db)
        seeded = seed_wifi_router_project(db)
        if seeded:
            logger.info("WiFi Router project ready: id=%s", seeded.id)
    finally:
        db.close()
    logger.info("Startup complete")


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "ProjectIQ"}


def _mount_frontend(app: FastAPI) -> None:
    static_root = Path(settings.static_dir)
    if not static_root.is_dir():
        logger.warning("Frontend static dir not found: %s", static_root.resolve())
        return

    index_file = static_root / "index.html"
    logger.info("Serving frontend from %s", static_root.resolve())

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(index_file)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        asset = static_root / full_path
        if asset.is_file():
            return FileResponse(asset)
        return FileResponse(index_file)


if settings.serve_frontend:
    _mount_frontend(app)
