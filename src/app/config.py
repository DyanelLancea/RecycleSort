from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_secret_key: str = "replace-with-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120
    ssm_admin_api_key: str = "dev-admin-api-key-not-for-production"
    ssm_jwt_signing_key: str = "dev-jwt-signing-key-not-for-production"
    database_url: str = "sqlite:///./recyclesort.sqlite3"
    max_upload_bytes: int = 5 * 1024 * 1024
    allowed_image_types: str = "image/jpeg,image/png,image/webp"

    @property
    def allowed_types(self) -> set[str]:
        return {item.strip() for item in self.allowed_image_types.split(",") if item.strip()}


settings = Settings()
