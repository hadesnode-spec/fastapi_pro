from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    JWT_SECRET_KEY: str = "secretkey"

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REDIS_URL: str = "redis://localhost:6379/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()