import os
import json
from typing import Optional, List
from groq import Groq
from pydantic import BaseModel, Field


class ResumeFeatures(BaseModel):
    skills: list[str] = Field(description="Technical skills")
    experience: list[str] = Field(description="Work experience highlights")
    projects: list[str] = Field(description="Notable projects")
    domain: list[str] = Field(description="Domain expertise areas")


class JobDescriptionFeatures(BaseModel):
    required_skills: list[str] = Field(description="Required skills")
    responsibilities: list[str] = Field(description="Key responsibilities")
    seniority: str = Field(description="Seniority level (Junior/Mid/Senior/Lead)")
    domain: list[str] = Field(description="Domain/industry")


class FeatureExtractor:
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self._client = None
        self.model = "llama-3.1-8b-instant"

    @property
    def client(self):
        if self._client is None:
            self._client = Groq(api_key=self._api_key)
        return self._client

    def _parse_json_response(self, content: str) -> dict:
        if not content:
            return {}
        content = content.strip()
        import re

        code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
        if code_block_match:
            content = code_block_match.group(1)
        else:
            content = re.sub(r"^.*?(?=\{|\[)", "", content, flags=re.DOTALL)
        content = content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end != 0:
                try:
                    return json.loads(content[start:end])
                except:
                    pass
            start = content.find("[")
            end = content.rfind("]") + 1
            if start != -1 and end != 0:
                try:
                    return {"items": json.loads(content[start:end])}
                except:
                    pass
            return {"items": []}

    def _extract_list_from_response(self, content: str) -> list:
        if not content:
            return []
        data = self._parse_json_response(content)
        if isinstance(data, list):
            return [str(item).strip() for item in data if item and str(item).strip()]
        if isinstance(data, dict):
            for key in data:
                if isinstance(data[key], list):
                    return [
                        str(item).strip()
                        for item in data[key]
                        if item and str(item).strip()
                    ]
        return []

    def extract_resume_features(self, text: str) -> ResumeFeatures:
        truncated = text[:2500]

        skills_response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": f"List all technical skills from this resume as a JSON array of strings: {truncated}",
                }
            ],
        )
        skills = self._extract_list_from_response(
            skills_response.choices[0].message.content
        )

        exp_response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": f"List work experiences with company names and roles from this resume as a JSON array of strings: {truncated}",
                }
            ],
        )
        experience = self._extract_list_from_response(
            exp_response.choices[0].message.content
        )

        proj_response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": f"List notable projects from this resume as a JSON array of strings: {truncated}",
                }
            ],
        )
        projects = self._extract_list_from_response(
            proj_response.choices[0].message.content
        )

        domain_response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": f"List domain expertise areas from this resume as a JSON array of strings: {truncated}",
                }
            ],
        )
        domain = self._extract_list_from_response(
            domain_response.choices[0].message.content
        )

        features = ResumeFeatures(
            skills=skills[:15],
            experience=experience[:5],
            projects=projects[:5],
            domain=domain[:5],
        )

        # Validate extracted features
        if len(features.skills) < 3:
            raise ValueError(
                f"Could not extract sufficient skills from resume (found {len(features.skills)}, need at least 3)"
            )

        return features

    def extract_jd_features(self, text: str) -> JobDescriptionFeatures:
        truncated = text[:2500]

        skills_response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": f"""Extract ONLY discrete technical skills, tools, and technologies from this job description.

Rules:
- ONLY include: Programming languages (Python, Java, SQL, etc.), Tools (Tableau, Spark, Hive, Git), Technologies (AWS, Azure, Docker), ML/AI terms (Machine Learning, Deep Learning, NLP, Neural Networks)
- EXCLUDE: Experience requirements (years of experience, "2-4 years"), Education (B.Tech, PhD, degrees), Soft skills (communication, leadership), Job titles (Data Scientist, Engineer)
- Keep each skill SHORT (max 3 words): "Python" NOT "Strong Python programming skills"
- NO duplicates: "Python" once, not "Python" and "Python programming"
- Return ONLY a JSON array of skill strings

Job Description:
{truncated}

Return JSON: {{"skills": ["Python", "SQL", "Machine Learning", ...]}}
""",
                }
            ],
        )
        required_skills = self._extract_list_from_response(
            skills_response.choices[0].message.content
        )

        resp_response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": f"List key responsibilities from this job description as a JSON array of strings: {truncated}",
                }
            ],
        )
        responsibilities = self._extract_list_from_response(
            resp_response.choices[0].message.content
        )

        seniority_response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": f"What is the seniority level for this job? Reply with just one word: Junior, Mid, Senior, or Lead: {truncated}",
                }
            ],
        )
        seniority = (
            seniority_response.choices[0].message.content.strip()
            if seniority_response.choices[0].message.content
            else "Mid"
        )
        if seniority.lower() not in ["junior", "mid", "senior", "lead"]:
            seniority = "Mid"

        domain_response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": f"List domain/industry areas from this job description as a JSON array of strings: {truncated}",
                }
            ],
        )
        domain = self._extract_list_from_response(
            domain_response.choices[0].message.content
        )

        # Clean and deduplicate skills
        required_skills = self._clean_skills(required_skills)

        return JobDescriptionFeatures(
            required_skills=required_skills[:15],
            responsibilities=responsibilities[:8],
            seniority=seniority,
            domain=domain[:5],
        )

    def _clean_skills(self, skills: List[str]) -> List[str]:
        """Clean and deduplicate skills list."""
        cleaned = []
        seen_lower = set()

        # Normalize similar skills
        normalize_map = {
            "python programming": "Python",
            "py": "Python",
            "pyspark": "Spark",
            "apache spark": "Spark",
            "pytorch": "PyTorch",
            "tensorflow": "TensorFlow",
            "ml": "Machine Learning",
            "dl": "Deep Learning",
            "ai": "Artificial Intelligence",
            "nlp": "NLP",
            "aws": "AWS",
            "amazon web services": "AWS",
            "azure": "Azure",
            "ms azure": "Azure",
            "google cloud": "GCP",
            "gcp": "GCP",
            "docker": "Docker",
            "kubernetes": "Kubernetes",
            "k8s": "Kubernetes",
            "sql": "SQL",
            "mysql": "MySQL",
            "postgresql": "PostgreSQL",
            "mongodb": "MongoDB",
        }

        for skill in skills:
            if not skill:
                continue
            skill_lower = skill.lower().strip()

            # Check if it's a duplicate (exact or normalized)
            if skill_lower in seen_lower:
                continue

            # Normalize if in map
            if skill_lower in normalize_map:
                normalized = normalize_map[skill_lower]
                if normalized.lower() not in seen_lower:
                    cleaned.append(normalized)
                    seen_lower.add(normalized.lower())
            elif len(skill) > 2 and len(skill) < 50:  # Reasonable length
                cleaned.append(skill)
                seen_lower.add(skill_lower)

        return cleaned
