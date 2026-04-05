from fastapi import APIRouter, HTTPException
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.services.resume_service import resume_service
from backend.models.schemas import (
    RankRequest,
    RankResponse,
    RankedCandidate,
    ScoreBreakdown,
    CandidateAnalysis,
)

router = APIRouter(prefix="/rank", tags=["Rank"])


@router.get("/latest")
async def get_latest_ranking():
    try:
        result = resume_service.get_latest_ranking()

        if not result:
            return {
                "job_title": "No results",
                "total_candidates": 0,
                "avg_match": 0,
                "candidates": [],
            }

        candidates = [
            {
                "name": c.get("candidate_id", "Unknown"),
                "role": c.get("experience", {}).get("title", "N/A")
                if isinstance(c.get("experience"), dict)
                else "N/A",
                "experience": c.get("experience", "N/A")
                if not isinstance(c.get("experience"), dict)
                else f"{c['experience'].get('years', 0)} years",
                "score": int(c["final_score"]),
                "matched_skills": len(c.get("skills", {}).get("matched", [])),
                "total_skills": len(c.get("skills", {}).get("required", []))
                + len(c.get("skills", {}).get("matched", [])),
                "strong_matches": c.get("skills", {}).get("matched", [])[:5],
                "missing_skills": c.get("skills", {}).get("missing", [])[:5],
                "weak_areas": c.get("analysis", {}).get("weak_areas", [])[:3]
                if c.get("analysis")
                else [],
            }
            for c in result.get("candidates", [])
        ]

        avg_match = (
            sum(c["score"] for c in candidates) / len(candidates) if candidates else 0
        )

        return {
            "job_title": result.get("job_id", "Position"),
            "total_candidates": len(candidates),
            "avg_match": int(avg_match),
            "candidates": candidates,
        }
    except Exception as e:
        return {
            "job_title": "Error",
            "total_candidates": 0,
            "avg_match": 0,
            "candidates": [],
            "error": str(e),
        }


@router.post("", response_model=RankResponse)
async def rank_resumes(request: RankRequest):
    try:
        result = resume_service.rank_resumes(
            request.resume_ids, request.job_id, analyze=request.analyze
        )

        candidates = [
            RankedCandidate(
                candidate_id=c["candidate_id"],
                final_score=c["final_score"],
                breakdown=ScoreBreakdown(**c["breakdown"]),
                skills=c["skills"],
                experience=c["experience"],
                verdict=c["verdict"],
                analysis=CandidateAnalysis(**c["analysis"])
                if c.get("analysis")
                else None,
            )
            for c in result["candidates"]
        ]

        return RankResponse(
            job_id=result["job_id"],
            total_candidates=result["total_candidates"],
            candidates=candidates,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
