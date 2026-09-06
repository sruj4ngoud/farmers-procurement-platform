import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Secrets come from the environment, never from code."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str = (
        "postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/farmer_procurement"
    )

    # JWT / authentication configuration.
    # JWT_SECRET must be provided through the environment in any real deployment.
    # When it is not set (local development / tests) a throwaway secret is
    # generated per process so that secrets are never hard-coded in source.
    jwt_secret: str | None = None
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # OTP configuration.
    otp_length: int = 6
    otp_expiry_seconds: int = 300  # 5 minutes by default
    otp_max_attempts: int = 5
    # Demo/test mode returns the generated OTP in the request-otp response so the
    # farmer journey can be exercised without a real SMS gateway.
    otp_demo_mode: bool = True


settings = Settings()

if settings.jwt_secret is None:
    # Ephemeral per-process secret: enough for local development/tests, but
    # deployments must export JWT_SECRET in the environment.
    settings.jwt_secret = secrets.token_urlsafe(48)
