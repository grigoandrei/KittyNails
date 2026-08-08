from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ADMIN_USERNAME: str
    ADMIN_PASSWORD_HASH: str
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 480
    TEST_DATABASE_URL: str | None = None
    DATABASE_URL: str
    DEBUG: bool = False
    # Nail analysis uses Claude on Amazon Bedrock (IAM auth via the default AWS
    # credential chain — no API key). Uses EU geo inference profile for cross-region routing.
    AWS_REGION: str = "eu-central-1"
    NAIL_ANALYSIS_MODEL: str = "eu.anthropic.claude-sonnet-4-6"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()