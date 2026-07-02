from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ADMIN_USERNAME: str
    ADMIN_PASSWORD_HASH: str
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 480
    TEST_DATABASE_URL: str | None = None
    DATABASE_URL: str 
    DEBUG: bool = False
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()