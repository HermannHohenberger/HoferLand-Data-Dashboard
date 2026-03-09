from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    genesis_username: str | None = None
    genesis_password: str | None = None
    genesis_code: str | None = None
    genesis_base_url: str = "https://www.regionalstatistik.de/genesisws/rest/2020/"
    genesis_population_table: str = "12411-01-01-4"
    genesis_regional_variable: str = "KREISE"
    etl_start_year: int = 2014
    cors_origins: list[str] = ["http://localhost:5173"]
    database_url: str | None = None
    sqlite_db_path: str | None = None

    model_config = SettingsConfigDict(
        env_file=str(ROOT_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
