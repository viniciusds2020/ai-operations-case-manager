from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CASE_", env_file=".env", extra="ignore")

    data_dir: Path = Path("data")
    max_upload_mb: int = 20
    auto_execute_max_risk: float = 0.25
    llm_provider: str = "deterministic"

    @property
    def database_path(self) -> Path:
        return self.data_dir / "cases.db"


settings = Settings()
