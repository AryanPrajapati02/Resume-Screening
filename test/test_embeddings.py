import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv(Path(__file__).parent.parent / ".env")

from core.step1_input_processing import parse_resume, clean_job_description
from core.step2_semantic_understanding import SemanticEmbedder, get_semantic_similarity

RESUMES = [
    "/Users/apple/practice/Yuvraj Singh Bhadoria Ai_ML_engineer_resume.pdf",
    "/Users/apple/practice/vrinda-cv.pdf",
]


def test_embeddings():
    embedder = SemanticEmbedder()

    with open("/Users/apple/practice/job_description.txt", "r") as f:
        jd_text = clean_job_description(f.read())

    print("=" * 60)
    print("EMBEDDING VECTORS - ALL RESUMES")
    print("=" * 60)

    print(f"\n📋 JOB DESCRIPTION:")
    print(f"   Text length: {len(jd_text)} chars")
    jd_embedding = embedder.encode([jd_text])[0]
    print(f"   Vector shape: {jd_embedding.shape}")

    results = []
    for path in RESUMES:
        print("\n" + "-" * 60)
        filename = path.split("/")[-1]
        print(f"📄 {filename}")

        resume_text = parse_resume(path)
        resume_embedding = embedder.encode([resume_text])[0]
        similarity = get_semantic_similarity(resume_text, jd_text, embedder)

        print(f"   Text length: {len(resume_text)} chars")
        print(f"   Vector shape: {resume_embedding.shape}")
        print(f"   Match Score: {similarity:.4f}")

        results.append(
            {
                "filename": filename,
                "chars": len(resume_text),
                "similarity": similarity,
            }
        )

    print("\n" + "=" * 60)
    print("SUMMARY - RANKED BY MATCH SCORE")
    print("=" * 60)
    results.sort(key=lambda x: x["similarity"], reverse=True)
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['filename']}: {r['similarity']:.4f} ({r['chars']} chars)")


if __name__ == "__main__":
    test_embeddings()
