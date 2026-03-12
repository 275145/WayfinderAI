from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    LLM_MODEL_ID: Optional[str] = None
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    LLM_TIMEOUT: int = 100

    OPENAI_API_KEY: Optional[str] = None
    ZHIPU_API_KEY: Optional[str] = None
    MODELSCOPE_API_KEY: Optional[str] = None

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    LOG_LEVEL: str = "INFO"

    UNSPLASH_ACCESS_KEY: Optional[str] = None
    UNSPLASH_SECRET_KEY: Optional[str] = None

    AMAP_API_KEY: str
    AMAP_MCP_SERVER_URL: str = "http://127.0.0.1:8000"
    CITY_CONFIG_PATH: str = "app/data/city_support.json"

    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_EXPIRY_HOURS: int = 24

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DECODE_RESPONSES: bool = True

    BCRYPT_ROUNDS: int = 12

    VECTOR_MEMORY_DIR: str = "vector_memory"
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    VECTOR_DIM: int = 384

    HF_ENDPOINT: str = "https://hf-mirror.com"
    HF_HUB_OFFLINE: bool = False
    HF_HUB_CACHE_DIR: Optional[str] = None

    def get_cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
