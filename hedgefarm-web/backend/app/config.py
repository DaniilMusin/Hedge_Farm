from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

class Settings(BaseSettings):
    FRONTEND_ORIGIN: str = Field(
        default="http://localhost:5173",
        description="Frontend origin URL for CORS"
    )

    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }

    @field_validator("FRONTEND_ORIGIN")
    def validate_origin(cls, v):
        """Validate that production origins use HTTPS."""
        if "localhost" not in v and not v.startswith("https://"):
            raise ValueError("Production origins must use HTTPS")
        return v

settings = Settings()