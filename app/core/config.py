from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DBREADER_",
        env_file=".env",
        extra="ignore",
    )

    database_directory: Path = Path("data")

settings = Settings()
