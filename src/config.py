import json
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_aws_secrets() -> None:
    """When running in AWS (Lambda), populate os.environ from Secrets Manager.

    Activated only when DB_SECRET_ARN / APP_SECRET_ARN are set (injected by the
    CDK stack). For local development these are unset, so the .env file is used
    instead and this function is a no-op.

    - DB secret (RDS-generated) → build DATABASE_URL from host/port/user/pass.
    - App secret → ADMIN_USERNAME, ADMIN_PASSWORD_HASH, JWT_SECRET, STRIPE_*.
    """
    db_secret_arn = os.getenv("DB_SECRET_ARN")
    app_secret_arn = os.getenv("APP_SECRET_ARN")
    if not db_secret_arn and not app_secret_arn:
        return

    import boto3  # imported lazily so local dev doesn't require it at import time

    region = os.getenv("AWS_REGION_NAME") or os.getenv("AWS_REGION", "eu-central-1")
    client = boto3.client("secretsmanager", region_name=region)

    if db_secret_arn:
        db = json.loads(client.get_secret_value(SecretId=db_secret_arn)["SecretString"])
        host = os.getenv("DB_HOST") or db["host"]
        port = os.getenv("DB_PORT") or str(db.get("port", 5432))
        name = os.getenv("DB_NAME") or db.get("dbname", "kittynails")
        user = db["username"]
        password = db["password"]
        os.environ["DATABASE_URL"] = (
            f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
        )

    if app_secret_arn:
        app = json.loads(
            client.get_secret_value(SecretId=app_secret_arn)["SecretString"]
        )
        for key, value in app.items():
            # Don't overwrite anything explicitly set in the environment.
            if value and not os.getenv(key):
                os.environ[key] = value


_load_aws_secrets()


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
    # SES email configuration
    SES_SENDER_EMAIL: str = "noreply@kittynails.de"
    SES_REGION: str = "eu-central-1"
    SES_ENABLED: bool = True
    STUDIO_NAME: str = "KittyNails Berlin"
    STUDIO_ADDRESS: str = "Stallschreiberstraße 16, 10179 Berlin"
    STUDIO_INSTAGRAM: str = "https://www.instagram.com/kittynails_berlin/"
    # Stripe configuration
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_DEPOSIT_AMOUNT: int = 1500  # cents (€15.00)
    FRONTEND_URL: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
