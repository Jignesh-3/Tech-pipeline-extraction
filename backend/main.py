from typing import Optional
from fastapi import FastAPI, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db, query_jobs, get_db_connection, get_top_skills
from backend.schemas import PaginatedJobResponse, JobResponse, TopSkillsResponse
from backend.pipeline import run_pipeline

from pathlib import Path
from fastapi.staticfiles import StaticFiles

from backend.scheduler import start_scheduler, shutdown_scheduler, scheduler

app = FastAPI(
    title="Tech Job Intelligence Pipeline API",
    description="Automated ingestion, deduplicated storage, and high-performance querying of engineering job postings.",
    version="1.0.0",
)

# Enable CORS for future frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """Ensure database tables and indexes exist on application boot."""
    init_db()
    start_scheduler(interval_hours=1) #Runs every hour keeping updated 

@app.on_event("shutdown")
def shutdown_event():
    """Ensure background threads are cleanly released on server stop."""
    shutdown_scheduler()


@app.get("/health", tags=["System"])
def health_check():
    """System health check and scheduler status."""
    return {
        "status": "ok",
        "service": "job-intelligence-pipeline",
        "scheduler_running": scheduler.running if 'scheduler' in globals() else False
    }


@app.get(
    "/jobs",
    response_model=PaginatedJobResponse,
    tags=["Jobs"],
    summary="Query and filter jobs with pagination"
)
def get_jobs(
    skill: Optional[str] = Query(
        None, 
        description="Filter by tech stack keyword (e.g. Python, FastAPI, Docker, SQL)"
    ),
    experience_level: Optional[str] = Query(
        None, 
        description="Filter by experience tier (Entry Level, Mid Level, Senior)"
    ),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page (max 100)")
):
    """
    Standout Feature: Parameterized multi-tag filtering with paginated envelopes.
    Keeps database read throughput efficient by utilizing limit/offset pagination.
    """
    total_count, records = query_jobs(
        skill=skill,
        experience_level=experience_level,
        page=page,
        page_size=page_size
    )

    has_next = (page * page_size) < total_count

    return {
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "has_next": has_next,
        "items": records
    }

@app.get(
    "/analytics/top-skills",
    response_model=TopSkillsResponse,
    tags=["Analytics"],
    summary="Get most demanded tech skills across indexed jobs"
)
def get_skill_analytics(
    limit: int = Query(10, ge=1, le=50, description="Top N skills to return")
):
    """
    Standout Feature: Aggregates real-time skill demand using database-native
    JSON unnesting and frequency grouping.
    """
    total_jobs, top_skills = get_top_skills(limit=limit)
    return {
        "total_analyzed_jobs": total_jobs,
        "top_skills": top_skills
    }

@app.get("/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
def get_job_by_id(job_id: int):
    """Fetch a single job posting by primary key."""
    import json
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job record with ID {job_id} not found."
            )
        job_data = dict(row)
        job_data["skills"] = json.loads(job_data["skills"])
        return job_data


@app.post("/pipeline/trigger", tags=["Pipeline"])
def trigger_pipeline():
    """Manually trigger an on-demand scrape, deduplication, and ingestion cycle."""
    metrics = run_pipeline()
    return {"message": "Pipeline cycle complete", "metrics": metrics}

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_DIR.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")