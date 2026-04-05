import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Resume Screening Platform"

    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    hf_token: str = os.getenv("HF_TOKEN", "")

    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = base_dir / "data"
    faiss_index_path: Path = data_dir / "faiss_index"
    sqlite_db_path: Path = data_dir / "resumes.db"

    embedding_model: str = "all-MiniLM-L6-v2"
    groq_model: str = "llama-3.1-8b-instant"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
