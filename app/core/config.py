"""Application configuration definitions."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "RecruiterMind AI"
    DATABASE_URL: str = "sqlite+aiosqlite:///./recruitermind.db"
    LOG_LEVEL: str = "INFO"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    ENABLE_EMBEDDINGS: bool = False
    ANALYSIS_CANDIDATE_LIMIT: int = 5000
    GEMINI_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
