import re
from typing import Optional


class JobDescriptionCleaner:
    def clean(self, text: str) -> str:
        text = self._remove_html_tags(text)
        text = self._remove_special_characters(text)
        text = self._normalize_whitespace(text)
        return text

    def _remove_html_tags(self, text: str) -> str:
        return re.sub(r"<[^>]+>", "", text)

    def _remove_special_characters(self, text: str) -> str:
        return re.sub(r"[^\w\s]", " ", text)

    def _normalize_whitespace(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()


def clean_job_description(text: str) -> str:
    cleaner = JobDescriptionCleaner()
    return cleaner.clean(text)
