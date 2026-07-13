from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    hf_token: str | None = None

    # reads from .env at startup, don't commit to git
    class Config:
        env_file = ".env"

settings = Settings()