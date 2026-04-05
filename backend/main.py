from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# Load .env if exists
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ensure data directory exists
data_dir = project_root / "data"
data_dir.mkdir(exist_ok=True)

# Frontend static files path - built during deployment
frontend_dist = project_root / "backend" / "static"

from backend.api import resumes, jobs, match, rank

app = FastAPI(
    title="Resume Screening Platform",
    description="AI-powered resume screening and candidate ranking",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resumes.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(match.router, prefix="/api")
app.include_router(rank.router, prefix="/api")

# Mount static files for frontend
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")


@app.get("/api")
async def api_root():
    return {
        "message": "Resume Screening Platform API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) if str(exc) else "Internal server error"},
    )


if frontend_dist.exists():
    app.mount(
        "/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets"
    )
