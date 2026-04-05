import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv(Path(__file__).parent.parent / ".env")

from core.step1_input_processing import parse_resume, clean_job_description
from core.step2_semantic_understanding import SemanticEmbedder, get_semantic_similarity
from core.step3_feature_extraction import FeatureExtractor
from core.step4_matching_logic import MatchingEngine

RESUMES = [
    "/Users/apple/practice/Yuvraj Singh Bhadoria Ai_ML_engineer_resume.pdf",
    "/Users/apple/practice/vrinda-cv.pdf",
]


def run_full_pipeline(
    resume_path: str, jd_text: str, embedder, extractor, engine, jd_features
) -> dict:
    filename = resume_path.split("/")[-1]
    print(f"\n{'=' * 60}")
    print(f"Processing: {filename}")
    print("=" * 60)

    # Step 1: Parse
    print("\n[Step 1] Parsing resume...")
    resume_text = parse_resume(resume_path)
    print(f"  Extracted {len(resume_text)} chars")

    # Step 2: Semantic similarity
    print("\n[Step 2] Computing semantic similarity...")
    semantic_score = get_semantic_similarity(resume_text, jd_text, embedder)
    print(f"  Semantic score: {semantic_score:.4f}")

    # Step 3: Feature extraction
    print("\n[Step 3] Extracting features...")
    resume_features = extractor.extract_resume_features(resume_text)
    print(f"  Skills ({len(resume_features.skills)}): {resume_features.skills[:5]}...")
    print(f"  Domain: {resume_features.domain[:3]}")

    # Step 4: Matching
    print("\n[Step 4] Computing match...")
    result = engine.compute_match(resume_text, jd_text, resume_features, jd_features)
    print(f"  Final Score: {result['final_score'] * 100:.1f}%")
    print(f"  Breakdown:")
    for k, v in result["breakdown"].items():
        print(f"    {k}: {v:.4f}")

    return {
        "filename": filename,
        "resume_text": resume_text,
        "resume_features": resume_features,
        "semantic_score": semantic_score,
        "final_score": result["final_score"],
        "breakdown": result["breakdown"],
    }


def main():
    print("=" * 60)
    print("FULL PIPELINE TEST - ALL RESUMES")
    print("=" * 60)

    # Load and clean JD
    with open("/Users/apple/practice/job_description.txt", "r") as f:
        jd_text = clean_job_description(f.read())
    print(f"\nJob Description: {len(jd_text)} chars")

    # Initialize components once
    print("\nInitializing AI components...")
    embedder = SemanticEmbedder()
    extractor = FeatureExtractor()
    engine = MatchingEngine(embedder=embedder)

    # Extract JD features once
    from core.step3_feature_extraction import JobDescriptionFeatures

    jd_features = extractor.extract_jd_features(jd_text)

    print(f"JD Required Skills: {jd_features.required_skills[:5]}...")
    print(f"JD Domain: {jd_features.domain[:3]}")

    # Process all resumes
    results = []
    for resume_path in RESUMES:
        result = run_full_pipeline(
            resume_path, jd_text, embedder, extractor, engine, jd_features
        )
        results.append(result)

    # Summary ranking
    print("\n" + "=" * 60)
    print("FINAL RANKING")
    print("=" * 60)
    results.sort(key=lambda x: x["final_score"], reverse=True)

    for i, r in enumerate(results, 1):
        verdict = (
            "Best"
            if r["final_score"] >= 0.7
            else "Good"
            if r["final_score"] >= 0.5
            else "Rejected"
        )
        print(f"\n{i}. {r['filename']}")
        print(f"   Score: {r['final_score'] * 100:.1f}% | {verdict}")
        print(
            f"   Skills matched: {len(r['resume_features'].skills)}/{len(jd_features.required_skills)}"
        )


if __name__ == "__main__":
    main()
