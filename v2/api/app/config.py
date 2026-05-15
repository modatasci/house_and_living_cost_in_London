from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    tfl_app_key: str | None = None
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    data_dir: str | None = None

    @property
    def resolved_data_dir(self) -> Path:
        if self.data_dir:
            return Path(self.data_dir).resolve()
        # Default: repo-root /data, two levels above this file (api/app/config.py -> api/ -> repo)
        return (Path(__file__).resolve().parents[3] / "data").resolve()

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
