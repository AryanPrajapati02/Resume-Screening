from pathlib import Path
from typing import List, Optional
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.step1_input_processing import (
    parse_resume,
    clean_job_description,
    is_likely_resume,
)
from backend.database.db import db
from backend.database.vector_store import vector_store
from backend.models.schemas import ResumeFeatures, JobDescriptionFeatures


class ResumeService:
    def __init__(self):
        self._embedder = None
        self._feature_extractor = None
        self._matching_engine = None

    @property
    def embedder(self):
        if self._embedder is None:
            from core.step2_semantic_understanding import SemanticEmbedder

            self._embedder = SemanticEmbedder()
        return self._embedder

    @property
    def feature_extractor(self):
        if self._feature_extractor is None:
            from core.step3_feature_extraction import FeatureExtractor

            self._feature_extractor = FeatureExtractor()
        return self._feature_extractor

    @property
    def matching_engine(self):
        if self._matching_engine is None:
            from core.step4_matching_logic import MatchingEngine

            self._matching_engine = MatchingEngine(embedder=self.embedder)
        return self._matching_engine

    def _parse_features(self, features_data):
        if features_data is None:
            return None
        if isinstance(features_data, str):
            return json.loads(features_data)
        return features_data

    def _get_resume_features(self, resume):
        features = self._parse_features(resume.get("features"))
        return ResumeFeatures(**features) if features else None

    def _get_job_features(self, job):
        features = self._parse_features(job.get("features"))
        return JobDescriptionFeatures(**features) if features else None

    def process_resume(self, file_path: str, filename: str) -> dict:
        text = parse_resume(file_path)

        # Validate it's a resume
        is_valid, reason = is_likely_resume(text)
        if not is_valid:
            raise ValueError(f"'{filename}' is not a valid resume: {reason}")

        features = self.feature_extractor.extract_resume_features(text)

        resume = db.create_resume(
            filename=filename, text=text, features=features.model_dump()
        )

        embedding = self.embedder.encode([text])[0]
        vector_store.add_vectors(
            ids=[resume["id"]],
            vectors=[embedding],
            metadata=[{"filename": filename, "text": text}],
        )

        return resume

    def process_resumes_bulk(self, file_paths: List[tuple]) -> List[dict]:
        results = []
        for file_path, filename in file_paths:
            try:
                result = self.process_resume(file_path, filename)
                results.append(result)
            except Exception as e:
                results.append({"filename": filename, "error": str(e)})
        return results

    def get_resume(self, resume_id: str) -> Optional[dict]:
        return db.get_resume(resume_id)

    def get_resumes(self, resume_ids: List[str] = None) -> List[dict]:
        return db.get_resumes(resume_ids)

    def delete_resume(self, resume_id: str) -> bool:
        vector_store.delete_vector(resume_id)
        return db.delete_resume(resume_id)

    def process_job(self, title: str, text: str) -> dict:
        cleaned_text = clean_job_description(text)
        features = self.feature_extractor.extract_jd_features(cleaned_text)

        job = db.create_job(
            title=title, text=cleaned_text, features=features.model_dump()
        )

        embedding = self.embedder.encode([cleaned_text])[0]
        vector_store.add_vectors(
            ids=[job["id"]],
            vectors=[embedding],
            metadata=[{"title": title, "text": cleaned_text}],
        )

        return job

    def get_job(self, job_id: str) -> Optional[dict]:
        return db.get_job(job_id)

    def get_jobs(self) -> List[dict]:
        return db.get_jobs()

    def delete_job(self, job_id: str) -> bool:
        vector_store.delete_vector(job_id)
        return db.delete_job(job_id)

    def match_resume_to_job(
        self, resume_id: str, job_id: str, analyze: bool = False
    ) -> dict:
        resume = db.get_resume(resume_id)
        job = db.get_job(job_id)

        if not resume or not job:
            raise ValueError("Resume or Job not found")

        resume_features = self._get_resume_features(resume)
        job_features = self._get_job_features(job)

        match_result = self.matching_engine.compute_match(
            resume["text"], job["text"], resume_features, job_features
        )

        db.save_match(
            resume_id, job_id, match_result["final_score"], match_result["breakdown"]
        )

        result = {
            "resume_id": resume_id,
            "job_id": job_id,
            "final_score": match_result["final_score"],
            "breakdown": match_result["breakdown"],
        }

        if analyze:
            analysis = self.matching_engine.analyze_candidate(
                resume["text"], job["text"], resume_features, job_features
            )
            result["analysis"] = analysis

        return result

    def rank_resumes(
        self, resume_ids: List[str], job_id: str, analyze: bool = False
    ) -> dict:
        job = db.get_job(job_id)
        if not job:
            raise ValueError("Job not found")

        resumes = db.get_resumes(resume_ids)
        if len(resumes) != len(resume_ids):
            raise ValueError("Some resumes not found")

        candidates = []
        for resume in resumes:
            features = self._get_resume_features(resume)
            candidates.append(
                {"id": resume["id"], "text": resume["text"], "features": features}
            )

        job_features = self._get_job_features(job)

        ranked = self.matching_engine.rank_candidates(
            candidates, job["text"], job_features, analyze=analyze
        )

        for candidate in ranked:
            db.save_match(
                candidate["candidate_id"],
                job_id,
                candidate["final_score"],
                candidate["breakdown"],
            )

            if candidate["final_score"] >= 0.7:
                candidate["verdict"] = "Best"
            elif candidate["final_score"] >= 0.5:
                candidate["verdict"] = "Good"
            else:
                candidate["verdict"] = "Rejected"

        return {"job_id": job_id, "total_candidates": len(ranked), "candidates": ranked}

    def get_latest_ranking(self) -> Optional[dict]:
        return self.match_all_resumes_to_latest_job(analyze=True)

    def match_all_resumes_to_latest_job(self, analyze: bool = False) -> Optional[dict]:
        jobs = db.get_jobs()
        if not jobs:
            return None

        latest_job = max(jobs, key=lambda j: j.get("created_at", ""))

        resumes = db.get_resumes()
        if not resumes:
            return {
                "job_id": latest_job.get("id", "unknown"),
                "total_candidates": 0,
                "candidates": [],
            }

        candidates = []
        for resume in resumes:
            features = self._get_resume_features(resume)
            candidates.append(
                {"id": resume["id"], "text": resume["text"], "features": features}
            )

        job_features = self._get_job_features(latest_job)

        ranked = self.matching_engine.rank_candidates(
            candidates, latest_job["text"], job_features, analyze=analyze
        )

        for candidate in ranked:
            if candidate["final_score"] >= 0.7:
                candidate["verdict"] = "Best"
            elif candidate["final_score"] >= 0.5:
                candidate["verdict"] = "Good"
            else:
                candidate["verdict"] = "Rejected"

        return {
            "job_id": latest_job.get("id", "unknown"),
            "total_candidates": len(ranked),
            "candidates": ranked,
        }

    def clear_all_resumes(self) -> dict:
        vector_store.clear_all_vectors()
        result = db.clear_all_resumes()
        return {"status": "success", "resumes_cleared": True}

    def clear_all_jobs(self) -> dict:
        vector_store.clear_all_vectors()
        result = db.clear_all_jobs()
        return {"status": "success", "jobs_cleared": True}

    def clear_all(self) -> dict:
        vector_store.clear_all_vectors()
        db.clear_all()
        return {"status": "success", "all_cleared": True}


resume_service = ResumeService()
