from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    REPLICATE_API_TOKEN: str = ""
    JWT_SECRET: str = "dev-secret-change-in-production"
    DATABASE_PATH: str = "app.db"
    UPLOAD_DIR: str = "uploads"
    RESULTS_DIR: str = "results"
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    model_config = {"env_file": ".env"}


settings = Settings()
