import json
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv(Path(__file__).parent.parent / ".env")

from core.step1_input_processing import parse_resume, clean_job_description
from core.step3_feature_extraction import FeatureExtractor

RESUMES = [
    "/Users/apple/practice/Yuvraj Singh Bhadoria Ai_ML_engineer_resume.pdf",
    "/Users/apple/practice/vrinda-cv.pdf",
]


def extract_features(resume_path: str, extractor: FeatureExtractor) -> dict:
    filename = resume_path.split("/")[-1]
    print(f"\n{'=' * 60}")
    print(f"EXTRACTING: {filename}")
    print("=" * 60)

    resume_text = parse_resume(resume_path)
    print(f"Resume: {len(resume_text)} chars")

    features = extractor.extract_resume_features(resume_text)

    print(f"\nSkills ({len(features.skills)}):")
    for skill in features.skills[:8]:
        print(f"  - {skill}")
    if len(features.skills) > 8:
        print(f"  ... and {len(features.skills) - 8} more")

    print(f"\nExperience ({len(features.experience)}):")
    for exp in features.experience[:3]:
        print(f"  - {exp}")

    print(f"\nProjects ({len(features.projects)}):")
    for proj in features.projects[:3]:
        print(f"  - {proj}")

    print(f"\nDomain ({len(features.domain)}):")
    for dom in features.domain[:5]:
        print(f"  - {dom}")

    return {
        "filename": filename,
        "skills_count": len(features.skills),
        "experience_count": len(features.experience),
        "projects_count": len(features.projects),
        "domain_count": len(features.domain),
        "features": features,
    }


if __name__ == "__main__":
    extractor = FeatureExtractor()

    print("=" * 60)
    print("STEP 3: FEATURE EXTRACTION - ALL RESUMES")
    print("=" * 60)

    # Extract JD features once
    with open("/Users/apple/practice/job_description.txt", "r") as f:
        jd_text = clean_job_description(f.read())

    print(f"\n{'=' * 60}")
    print("JD FEATURES")
    print("=" * 60)
    jd_features = extractor.extract_jd_features(jd_text)
    print(f"Required Skills ({len(jd_features.required_skills)}):")
    for skill in jd_features.required_skills[:8]:
        print(f"  - {skill}")
    print(f"\nSeniority: {jd_features.seniority}")
    print(f"Domain: {jd_features.domain[:5]}")

    # Process all resumes
    results = []
    for resume_path in RESUMES:
        result = extract_features(resume_path, extractor)
        results.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results:
        print(f"\n{r['filename']}:")
        print(
            f"  Skills: {r['skills_count']} | Experience: {r['experience_count']} | Projects: {r['projects_count']} | Domain: {r['domain_count']}"
        )
