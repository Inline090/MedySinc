from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    PORT: int = 8000
    DATABASE_URL: str
    CORS_ORIGIN: str = "http://localhost:3000"
    STORAGE_ROOT: str = "storage"
    STORAGE_BACKEND: str = "local"
    S3_BUCKET: str | None = None
    S3_REGION: str = "ap-south-1"
    S3_ENDPOINT: str | None = None
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024
    OCR_ENABLED: bool = True
    OCR_LANGUAGE: str = "en"
    OCR_DPI: int = 200
    OCR_MAX_PAGES: int = 10
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DIMENSION: int = 1024
    MODEL_CACHE_DIR: str | None = None
    AI_API_KEY: str | None = None
    LLM_MODEL: str = "gemini-2.5-flash"
    HNSW_EF_SEARCH: int = 100
    MIN_SIMILARITY: float = 0.45
    ANSWER_CACHE_ENABLED: bool = True
    ANSWER_CACHE_TTL_HOURS: int = 24
    RERANK_ENABLED: bool = True
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANK_CANDIDATES: int = 20
    FRONTEND_URL: str = "http://localhost:3000"
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URL: str = "http://localhost:8000/api/v1/auth/google/callback"
    JWT_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGIN.split(",") if origin.strip()]


settings = Settings()  # type: ignore[call-arg]
