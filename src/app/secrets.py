"""Secrets loader.

- development: environment variable first, then the value from `.env` / config defaults.
- any other app_env (production, staging): AWS Systems Manager Parameter Store only.

There is deliberately NO fallback outside development, so a misconfigured server
fails loudly instead of quietly running with a publicly known dev key.
"""

from __future__ import annotations

import os
from functools import lru_cache

from app.config import settings

MIN_KEY_LENGTH = 32

class SecretLoadError(RuntimeError):
    """Raised when a secret cannot be loaded or is unsafe to use."""

@lru_cache(maxsize=None)
def _read_ssm(parameter_name: str) -> str:
    # Imported here so local development works even without boto3 installed.
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    client = boto3.client("ssm", region_name=settings.aws_region)
    try:
        response = client.get_parameter(Name=parameter_name, WithDecryption=True)
    except (BotoCoreError, ClientError) as exc:
        raise SecretLoadError(f"Could not read SSM parameter {parameter_name}") from exc
    return response["Parameter"]["Value"]


def load_parameter(env_name: str, ssm_name: str, fallback: str) -> str:
    """Return a secret from SSM (non-development) or env/.env (development)."""
    if settings.app_env == "development":
        return os.environ.get(env_name) or fallback
    return _read_ssm(f"{settings.ssm_prefix}{ssm_name}")


def admin_api_key() -> str:
    return load_parameter("SSM_ADMIN_API_KEY", "admin_api_key", settings.ssm_admin_api_key)


def jwt_signing_key() -> str:
    key = load_parameter("SSM_JWT_SIGNING_KEY", "jwt_signing_key", settings.ssm_jwt_signing_key)
    if len(key) < MIN_KEY_LENGTH:
        raise SecretLoadError(f"JWT signing key must be at least {MIN_KEY_LENGTH} characters")
    return key