import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.services.resume_service import resume_service
from backend.models.schemas import ResumeResponse

router = APIRouter(prefix="/resumes", tags=["Resumes"])

UPLOAD_DIR = Path(__file__).parent.parent.parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/bulk", response_model=List[ResumeResponse])
async def upload_resumes(files: List[UploadFile] = File(...)):
    # Clear all previous resumes first
    resume_service.clear_all_resumes()

    file_paths = []
    for file in files:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=400, detail=f"Only PDF files allowed: {file.filename}"
            )

        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_paths.append((str(file_path), file.filename))

    results = resume_service.process_resumes_bulk(file_paths)

    response_list = []
    for r in results:
        if "error" in r:
            print(f"Error processing {r.get('filename')}: {r.get('error')}")
        elif "id" in r:
            response_list.append(
                ResumeResponse(
                    id=r["id"],
                    filename=r["filename"],
                    text=r["text"][:500] + "..." if len(r["text"]) > 500 else r["text"],
                    created_at=r["created_at"],
                )
            )

    return response_list


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: str):
    resume = resume_service.get_resume(resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return ResumeResponse(
        id=resume["id"],
        filename=resume["filename"],
        text=resume["text"],
        created_at=resume["created_at"],
    )


@router.delete("/{resume_id}")
async def delete_resume(resume_id: str):
    success = resume_service.delete_resume(resume_id)
    if not success:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {"message": "Resume deleted successfully"}


@router.post("/clear")
async def clear_all_resumes():
    result = resume_service.clear_all_resumes()
    return {"message": "All resumes cleared", **result}
