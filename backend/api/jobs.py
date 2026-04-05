from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.services.resume_service import resume_service
from backend.models.schemas import JobCreate, JobResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])


class JobCreateRequest(BaseModel):
    title: str
    text: str


@router.post("", response_model=JobResponse)
async def create_job(job: JobCreateRequest):
    # Clear all previous jobs first
    resume_service.clear_all_jobs()

    result = resume_service.process_job(job.title, job.text)
    return JobResponse(
        id=result["id"],
        title=result["title"],
        text=result["text"],
        created_at=result["created_at"],
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    job = resume_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        id=job["id"], title=job["title"], text=job["text"], created_at=job["created_at"]
    )


@router.get("")
async def list_jobs():
    jobs = resume_service.get_jobs()
    return [
        {"id": j["id"], "title": j["title"], "created_at": j["created_at"]}
        for j in jobs
    ]


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    success = resume_service.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted successfully"}


@router.post("/clear")
async def clear_all_jobs():
    result = resume_service.clear_all_jobs()
    return {"message": "All jobs cleared", **result}
