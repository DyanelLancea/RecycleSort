from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # "development" reads secrets from env/.env. Any other value reads from SSM.
    app_env: str = "development"
    app_secret_key: str = "replace-with-a-long-random-string"

    # Only HS256 is allowed, so a bad env value can never enable a weaker algorithm.
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_expire_minutes: int = 30

    # Local-dev fallbacks only. They are NOT used when app_env != "development".
    ssm_admin_api_key: str = "dev-admin-api-key-not-for-production"
    ssm_jwt_signing_key: str = "dev-jwt-signing-key-not-for-production"

    # AWS Systems Manager Parameter Store
    ssm_prefix: str = "/recyclesort/prod/"  # change to match your parameter names
    aws_region: str | None = None  # None = use boto3's normal region lookup

    database_url: str = "sqlite:///./recyclesort.sqlite3"
    max_upload_bytes: int = 5 * 1024 * 1024
    allowed_image_types: str = "image/jpeg,image/png,image/webp"

    @property
    def allowed_types(self) -> set[str]:
        return {item.strip() for item in self.allowed_image_types.split(",") if item.strip()}


settings = Settings()