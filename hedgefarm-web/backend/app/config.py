from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    FRONTEND_ORIGIN: str = "http://localhost"
    class Config:
        env_file = ".env"

settings = Settings()