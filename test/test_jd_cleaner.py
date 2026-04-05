from core.step1_input_processing import clean_job_description

if __name__ == "__main__":
    jd_path = "/Users/apple/practice/job_description.txt"

    with open(jd_path, "r") as f:
        jd_text = f.read()

    print("Original JD:")
    print("-" * 50)
    print(jd_text)

    print("\n\nCleaned JD:")
    print("-" * 50)
    cleaned = clean_job_description(jd_text)
    print(cleaned)
    print(f"\n({len(cleaned)} chars)")
