from fastapi import APIRouter, HTTPException
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.services.resume_service import resume_service
from backend.models.schemas import (
    MatchRequest,
    MatchResponse,
    ScoreBreakdown,
    CandidateAnalysis,
)

router = APIRouter(prefix="/match", tags=["Match"])


@router.post("/all")
async def match_all_to_latest():
    try:
        result = resume_service.match_all_resumes_to_latest_job(analyze=True)

        # Get job title and features
        from backend.database.db import db
        import json

        jobs = db.get_jobs()
        job_title = "Position"
        jd_required_skills = []
        if jobs:
            latest_job = max(jobs, key=lambda j: j.get("created_at", ""))
            job_title = latest_job.get("title", "Position")
            features = latest_job.get("features")
            if features:
                if isinstance(features, str):
                    features = json.loads(features)
                jd_required_skills = features.get("required_skills", [])

        candidates = []
        for c in result.get("candidates", []):
            candidate_id = c.get("candidate_id", "")

            # Get resume info for filename
            resume = db.get_resume(candidate_id)
            filename = resume.get("filename", "Unknown") if resume else "Unknown"
            # Clean up filename
            name = filename.replace(".pdf", "").replace("_", " ").replace("-", " ")

            # Format experience - only role/position (NOT company)
            experience_list = c.get("experience", []) or []
            formatted_exp = []
            for exp in experience_list[:3]:
                if isinstance(exp, str):
                    import re

                    # Try to extract role from dict format first
                    role = re.search(
                        r"(?:role|position|Role|Position)['\"]?\s*:\s*['\"]?([^'\"]+)",
                        exp,
                    )
                    period = re.search(
                        r"(?:duration|period|Dates)['\"]?\s*:\s*['\"]?([^'\"]+)", exp
                    )

                    if role:
                        # Dict format - extract role and period only
                        role_text = role.group(1).strip()
                        # Remove company name if present in role
                        role_text = re.sub(r"@\s*[^,]+", "", role_text).strip()
                        parts = [role_text]
                        if period:
                            parts.append(f"({period.group(1).strip()})")
                        exp = " - ".join(parts)
                    else:
                        # Simple string format - extract just the role (first part before company/date)
                        # Remove dates like "Jan 2024" or "2024"
                        exp_clean = re.sub(
                            r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s*-\s*(Present|\w+\s+\d{4})?\b",
                            "",
                            exp,
                        )
                        exp_clean = re.sub(
                            r"\b\d{4}\s*-\s*(Present|\d{4})?\b", "", exp_clean
                        )
                        # Remove company indicators
                        exp_clean = re.sub(
                            r"\b(Inc|LLC|Ltd|Corp|Pvt|Private)\b",
                            "",
                            exp_clean,
                            flags=re.IGNORECASE,
                        )
                        # Get just the role (first comma-separated part usually)
                        parts = [p.strip() for p in exp.split(",") if p.strip()]
                        exp = parts[0] if parts else exp
                formatted_exp.append(exp)

            # Primary role is first job
            primary_role = formatted_exp[0] if formatted_exp else "N/A"

            # Get AI-verified semantic matches (from matching engine)
            semantic_matches = c.get("semantic_matched_skills", []) or []
            exact_matches = c.get("exact_matched_skills", []) or []

            # Use semantic matches count for display
            matched_count = len(semantic_matches)

            # Get skills
            skills = c.get("skills", []) or []

            # Create all skills status
            all_skills_status = []
            matched_skill_names = set(semantic_matches)
            
            # If no required skills from job, use matched skills as fallback
            skills_to_check = jd_required_skills if jd_required_skills else semantic_matches
            
            for skill in skills_to_check:
                all_skills_status.append({
                    "skill": skill,
                    "matched": skill in matched_skill_names
                })

            analysis = c.get("analysis", {}) or {}
            candidates.append(
                {
                    "id": candidate_id,
                    "name": name,
                    "filename": filename,
                    "role": primary_role,
                    "experience": formatted_exp,
                    "score": int(c["final_score"] * 100),
                    "matched_skills": matched_count,
                    "exact_matches": len(exact_matches),
                    "required_skills": len(jd_required_skills) if jd_required_skills else len(semantic_matches),
                    "skills": skills[:10],
                    "matched_skills_list": semantic_matches[:5],  # Show top 5 matched
                    "all_skills_status": all_skills_status,
                    "strong_matches": analysis.get("strong_matches", [])[:5],
                    "missing_skills": analysis.get("missing_skills", [])[:5],
                    "weak_areas": analysis.get("weak_areas", [])[:3],
                    "verdict": c.get("verdict", "Unknown"),
                    "breakdown": c.get("breakdown", {}),
                }
            )

        avg_match = (
            sum(c["score"] for c in candidates) / len(candidates) if candidates else 0
        )

        return {
            "job_title": job_title,
            "total_candidates": len(candidates),
            "avg_match": int(avg_match),
            "candidates": candidates,
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {
            "job_title": "Error",
            "total_candidates": 0,
            "avg_match": 0,
            "candidates": [],
            "error": str(e),
        }


@router.post("", response_model=MatchResponse)
async def match_resume_to_job(request: MatchRequest):
    try:
        result = resume_service.match_resume_to_job(
            request.resume_id, request.job_id, analyze=request.analyze
        )

        return MatchResponse(
            resume_id=result["resume_id"],
            job_id=result["job_id"],
            final_score=result["final_score"],
            breakdown=ScoreBreakdown(**result["breakdown"]),
            analysis=CandidateAnalysis(**result["analysis"])
            if result.get("analysis")
            else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
