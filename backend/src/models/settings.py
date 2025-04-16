import yaml
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    mongo_url: str = Field(..., env="MONGO_URL")
    database_name: str = Field(..., env="DATABASE_NAME")

    def __init__(self):
        super().__init__()


def get_settings():
    return Settings()
