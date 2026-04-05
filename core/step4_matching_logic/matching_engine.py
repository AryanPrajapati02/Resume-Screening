import os
import json
from typing import Dict, Any, List, Optional
from core.step2_semantic_understanding import SemanticEmbedder, get_semantic_similarity
from core.step3_feature_extraction import ResumeFeatures, JobDescriptionFeatures
from groq import Groq
from pydantic import BaseModel, Field


class CandidateAnalysis(BaseModel):
    missing_skills: list[str] = Field(
        description="Skills required by JD but missing in resume"
    )
    weak_areas: list[str] = Field(description="Areas where candidate is weak")
    strong_matches: list[str] = Field(
        description="Areas where candidate strongly matches JD"
    )


class CandidateResult(BaseModel):
    candidate_id: str
    final_score: float
    breakdown: Dict[str, float]
    analysis: Optional[Dict[str, Any]] = None


class MatchingEngine:
    def __init__(
        self, embedder: SemanticEmbedder = None, groq_api_key: Optional[str] = None
    ):
        self.embedder = embedder or SemanticEmbedder()
        self._groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY", "")
        self._groq_client = None
        self.groq_model = "llama-3.1-8b-instant"
        self.weights = {
            "semantic": 0.4,
            "skill": 0.3,
            "experience": 0.2,
            "bonus": 0.1,
        }

    @property
    def groq_client(self):
        if self._groq_client is None:
            self._groq_client = Groq(api_key=self._groq_api_key)
        return self._groq_client

    def compute_match(
        self,
        resume_text: str,
        jd_text: str,
        resume_features: ResumeFeatures,
        jd_features: JobDescriptionFeatures,
    ) -> Dict[str, Any]:
        semantic_score = self._semantic_similarity(resume_text, jd_text)
        exact_ratio, semantic_ratio, exact_matched, semantic_matched = (
            self._skill_coverage(resume_features.skills, jd_features.required_skills)
        )
        experience_score = self._experience_alignment(resume_features, jd_features)
        bonus_score = self._bonus_score(resume_features, jd_features)

        final_score = (
            self.weights["semantic"] * semantic_score
            + self.weights["skill"] * semantic_ratio  # Use semantic ratio for scoring
            + self.weights["experience"] * experience_score
            + self.weights["bonus"] * bonus_score
        )

        return {
            "final_score": round(final_score, 4),
            "breakdown": {
                "semantic_similarity": round(semantic_score, 4),
                "exact_skill_match": round(exact_ratio, 4),
                "skill_coverage": round(
                    semantic_ratio, 4
                ),  # Renamed to semantic coverage
                "experience_alignment": round(experience_score, 4),
                "bonus_score": round(bonus_score, 4),
            },
            "exact_matched_skills": exact_matched,
            "semantic_matched_skills": semantic_matched,
        }

    def analyze_candidate(
        self,
        resume_text: str,
        jd_text: str,
        resume_features: ResumeFeatures,
        jd_features: JobDescriptionFeatures,
    ) -> Dict[str, Any]:
        prompt = f"""Compare this resume against the job description. Return ONLY valid JSON.

Resume:
{resume_text[:3000]}

Job Description:
{jd_text}

Analyze and return:
{{
    "missing_skills": ["skills mentioned in JD but clearly MISSING in resume - be specific"],
    "weak_areas": ["genuine deficiencies where candidate LACKS required skills or experience"],
    "strong_matches": ["where candidate EXCEEDS or MEETS requirements"]
}}

IMPORTANT RULES:
- Only flag as WEAK if candidate truly LACKS something required
- If candidate MEETS or EXCEEDS requirements (e.g., has 3.5 years when JD wants 1-4 years), flag as STRONG, not weak
- Do NOT flag positive attributes as weaknesses
- Be specific and honest

Return JSON only."""

        response = self.groq_client.chat.completions.create(
            model=self.groq_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)
        return {
            "missing_skills": data.get("missing_skills", []),
            "weak_areas": data.get("weak_areas", []),
            "strong_matches": data.get("strong_matches", []),
        }

    def rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
        jd_text: str,
        jd_features: JobDescriptionFeatures,
        analyze: bool = False,
    ) -> List[Dict[str, Any]]:
        results = []

        for candidate in candidates:
            resume_text = candidate["text"]
            resume_features = candidate["features"]
            candidate_id = candidate.get(
                "id", candidate.get("name", f"candidate_{len(results)}")
            )

            match_result = self.compute_match(
                resume_text, jd_text, resume_features, jd_features
            )

            result = {
                "candidate_id": candidate_id,
                "final_score": match_result["final_score"],
                "breakdown": match_result["breakdown"],
                "skills": resume_features.skills,
                "experience": resume_features.experience,
                "exact_matched_skills": match_result.get("exact_matched_skills", []),
                "semantic_matched_skills": match_result.get(
                    "semantic_matched_skills", []
                ),
            }

            if analyze:
                result["analysis"] = self.analyze_candidate(
                    resume_text, jd_text, resume_features, jd_features
                )

            results.append(result)

        return sorted(results, key=lambda x: x["final_score"], reverse=True)

    def _semantic_similarity(self, resume_text: str, jd_text: str) -> float:
        return get_semantic_similarity(resume_text, jd_text, self.embedder)

    def _skill_coverage(
        self, resume_skills: List[str], required_skills: List[str]
    ) -> tuple[float, float, List[str], List[str]]:
        """
        Returns (exact_match_ratio, semantic_match_ratio, exact_matched_skills, semantic_matched_skills)
        """
        if not required_skills:
            return 1.0, 1.0, [], []

        resume_skills_lower = [s.lower() for s in resume_skills]
        required_skills_lower = [s.lower() for s in required_skills]

        # Exact matches (simple keyword matching)
        exact_matched = []
        for req in required_skills_lower:
            if any(req in skill or skill in req for skill in resume_skills_lower):
                exact_matched.append(req)

        # Semantic matches (AI-powered)
        semantic_matched = self._semantic_skill_match(resume_skills, required_skills)

        exact_ratio = len(exact_matched) / len(required_skills)
        semantic_ratio = len(semantic_matched) / len(required_skills)

        return exact_ratio, semantic_ratio, exact_matched, semantic_matched

    def _semantic_skill_match(
        self, resume_skills: List[str], required_skills: List[str]
    ) -> List[str]:
        """
        Use AI to determine which required skills are actually demonstrated in the resume.
        """
        if not resume_skills or not required_skills:
            return []

        # Limit to avoid token limits
        skills_to_check = required_skills[:10]

        prompt = f"""You are an expert recruiter. Given a candidate's skills and required job skills, determine which required skills the candidate ACTUALLY HAS.

Candidate Skills: {", ".join(resume_skills[:15])}

Required Job Skills:
{chr(10).join(f"- {skill}" for skill in skills_to_check)}

Return ONLY a JSON array of the required skills that the candidate ACTUALLY DEMONSTRATES (not just mentions):
{{"demonstrated_skills": ["skill1", "skill2", ...]}}

Rules:
- A skill is demonstrated if the candidate has RELEVANT experience with it
- Don't count skills just because similar words appear
- Be strict - only count if the candidate truly has this skill
- If unsure, don't include the skill"""

        try:
            response = self.groq_client.chat.completions.create(
                model=self.groq_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content

            # Parse JSON
            data = json.loads(content)
            demonstrated = data.get("demonstrated_skills", [])

            # Return the original skill names (not lowercased)
            matched = []
            for req in required_skills:
                if req.lower() in [s.lower() for s in demonstrated]:
                    matched.append(req)

            return matched
        except Exception as e:
            print(f"Semantic skill match error: {e}")
            return []

    def _experience_alignment(
        self, resume_features: ResumeFeatures, jd_features: JobDescriptionFeatures
    ) -> float:
        seniority_map = {"junior": 1, "mid": 2, "senior": 3, "lead": 4, "principal": 5}
        jd_level = seniority_map.get(jd_features.seniority.lower(), 2)
        resume_level = seniority_map.get("senior", 3)
        level_diff = abs(resume_level - jd_level)
        role_match = 1.0 if jd_level <= resume_level else 0.7
        return max(0, 1.0 - (level_diff * 0.2)) * role_match

    def _bonus_score(
        self, resume_features: ResumeFeatures, jd_features: JobDescriptionFeatures
    ) -> float:
        domain_exact_ratio, _, _, _ = self._skill_coverage(
            resume_features.domain, jd_features.domain
        )
        project_score = min(1.0, len(resume_features.projects) / 3)
        return (domain_exact_ratio * 0.5) + (project_score * 0.5)
