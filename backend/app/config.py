from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://news_hub:news_hub@localhost:5432/news_hub"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    RSS_POLL_INTERVAL_SECONDS: int = 3600
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIMS: int = 384
    CLAUDE_MODEL: str = "claude-sonnet-4-6"
    CORS_ORIGINS: str = "http://localhost:5173"
    HDBSCAN_MIN_CLUSTER_SIZE: int = 3

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
