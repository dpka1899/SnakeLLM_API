# api/settings.py

from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


# -------------------------------------------------
# ✅ Ensure .env is loaded for BOTH FastAPI & Celery
# -------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    # =================================================
    # 🔐 AUTH
    # =================================================
    api_key: str = Field(default="", alias="API_KEY")

    # =================================================
    # 📝 LOGGING
    # =================================================
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # =================================================
    # 🤖 LLM CONFIG
    # =================================================
    llm_provider: str = Field(default="auto", alias="LLM_PROVIDER")

    llm_model: str = Field(
        default="claude-3-sonnet-20240229",
        alias="LLM_MODEL",
    )

    anthropic_api_key: str = Field(
        default="",
        alias="ANTHROPIC_API_KEY",
    )

    snakellm_path: str = Field(
        default="",
        alias="SNAKELLM_PATH",
    )

    # =================================================
    # 🗄 DATABASE
    # =================================================
    database_url: str = Field(
        default="postgresql+psycopg://snakellm:snakellm@localhost:5432/snakellm",
        alias="DATABASE_URL",
    )

    # =================================================
    # ⚡ CELERY / REDIS
    # =================================================
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        alias="CELERY_BROKER_URL",
    )

    celery_result_backend: str = Field(
        default="redis://localhost:6379/1",
        alias="CELERY_RESULT_BACKEND",
    )

    # =================================================
    # 📦 STORAGE
    # =================================================
    artifacts_dir: str = Field(
        default="storage/jobs",
        alias="ARTIFACTS_DIR",
    )


# Singleton settings object
settings = Settings()