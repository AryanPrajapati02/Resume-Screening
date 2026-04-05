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

app.include_router(resumes.router)
app.include_router(jobs.router)
app.include_router(match.router)
app.include_router(rank.router)


# Frontend static files path - built during deployment
frontend_dist = project_root / "backend" / "static"


@app.get("/api")
async def api_root():
    return {
        "message": "Resume Screening Platform API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/")
async def root():
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        with open(index_file, "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    return {"message": "Resume Screening Platform API", "version": "1.0.0"}


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
