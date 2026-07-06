import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    service_name: str = "freelance-shield-ai"
    google_api_key: str | None = os.getenv("GOOGLE_API_KEY") or None
    google_adk_model: str = os.getenv("GOOGLE_ADK_MODEL", "gemini-2.5-flash")
    cors_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )
    database_path: Path = Path(
        os.getenv(
            "FREELANCE_SHIELD_DB",
            str(Path(__file__).resolve().parents[2] / "data" / "freelance_shield.db"),
        )
    )
    static_dir: Path = Path(__file__).resolve().parents[2] / "static"


settings = Settings()
