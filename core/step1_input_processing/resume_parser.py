import pdfplumber
import re
from pathlib import Path
from typing import Optional, Tuple


def is_likely_resume(text: str) -> Tuple[bool, str]:
    """
    Check if a document appears to be a resume.
    Returns (is_valid, reason).
    """
    if not text or len(text.strip()) < 200:
        return False, "Document is too short or empty"

    text_lower = text.lower()

    # Non-resume indicators (high confidence rejection)
    non_resume_phrases = [
        "offer of employment",
        "terms and conditions",
        "compensation and benefits",
        "non-disclosure agreement",
        "employment contract",
        "notice period",
        "date of joining",
        "ctc",
        "salary:",
        "annual package",
        "background check",
    ]
    for phrase in non_resume_phrases:
        if phrase in text_lower:
            return (
                False,
                f"Document appears to be a contract/offer letter (found: '{phrase}')",
            )

    # Resume section indicators
    resume_sections = [
        "education",
        "experience",
        "work experience",
        "skills",
        "projects",
        "certifications",
        "achievements",
        "summary",
        "objective",
        "profile",
    ]
    found_sections = sum(1 for section in resume_sections if section in text_lower)

    if found_sections < 2:
        return (
            False,
            f"Document missing typical resume sections (found {found_sections}/2 required)",
        )

    # Name detection (resume usually has name at top)
    name_pattern = r"^[A-Z][a-z]+\s+[A-Z][a-z]+"
    if not re.search(name_pattern, text.strip()):
        # Allow if there's contact info (email/phone near start)
        if not re.search(r"[\w.-]+@[\w.-]+", text) and not re.search(r"\d{10}", text):
            return False, "Document does not appear to have candidate name/contact info"

    return True, "Valid resume"


class ResumeParser:
    def __init__(self):
        self.supported_formats = [".pdf"]

    def extract_text(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported format: {path.suffix}")

        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        return self._basic_preprocessing(text)

    def _basic_preprocessing(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text


def parse_resume(file_path: str) -> str:
    parser = ResumeParser()
    return parser.extract_text(file_path)
