from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    TEST_DATABASE_URL: str | None = None
    DATABASE_URL: str 
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()