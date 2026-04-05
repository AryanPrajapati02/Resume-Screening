from core.step1_input_processing import parse_resume

RESUMES = [
    "/Users/apple/practice/Yuvraj Singh Bhadoria Ai_ML_engineer_resume.pdf",
    "/Users/apple/practice/vrinda-cv.pdf",
    "/Users/apple/practice/candidate.pdf",
]


def parse_single_resume(path: str) -> dict:
    print(f"\n{'=' * 60}")
    print(f"Parsing: {path.split('/')[-1]}")
    print("=" * 60)

    try:
        text = parse_resume(path)
        print(f"Extracted {len(text)} chars")
        print("-" * 40)
        print(text[:500] + "..." if len(text) > 500 else text)
        return {"path": path, "text": text, "success": True, "error": None}
    except Exception as e:
        print(f"Error: {e}")
        return {"path": path, "text": None, "success": False, "error": str(e)}


def parse_all_resumes(resume_list: list[str]) -> list[dict]:
    results = []
    for path in resume_list:
        result = parse_single_resume(path)
        results.append(result)
    return results


def print_summary(results: list[dict]):
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"Total resumes: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if successful:
        print("\nParsed successfully:")
        for r in successful:
            print(f"  - {r['path'].split('/')[-1]}: {len(r['text'])} chars")

    if failed:
        print("\nFailed to parse:")
        for r in failed:
            print(f"  - {r['path'].split('/')[-1]}: {r['error']}")


if __name__ == "__main__":
    print("Resume Parser Test")
    print("-" * 40)

    results = parse_all_resumes(RESUMES)
    print_summary(results)

    print("\nTest completed.")
