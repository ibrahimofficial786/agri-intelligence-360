from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]  # project root


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./agri360.db"
    secret_key: str = "dev-only-change-me"
    access_token_minutes: int = 60 * 24
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    upload_dir: str = "./uploads"
    max_upload_mb: int = 5
    model_path: str = ""
    model_labels_path: str = ""
    model_input_size: int = 224
    min_confidence: float = 0.6
    market_provider: str = "sample"  # sample | datagov
    data_gov_api_key: str = ""
    seed_demo: bool = True
    risk_min_reports: int = 3
    risk_window_days: int = 14
    data_dir: str = str(ROOT / "data")


settings = Settings()
