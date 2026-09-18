"""Secrets loader. Production should read AWS Systems Manager Parameter Store."""

from __future__ import annotations

import os

from app.config import settings


def load_parameter(name: str, fallback: str) -> str:
    """Return a secret as if fetched from Parameter Store.

    Local/dev: environment variable, then the compiled fallback from `.env`.
    AWS: replace the body with `boto3.client("ssm").get_parameter(...)`.
    """
    from_env = os.environ.get(name)
    if from_env:
        return from_env
    return fallback


def admin_api_key() -> str:
    return load_parameter("SSM_ADMIN_API_KEY", settings.ssm_admin_api_key)


def jwt_signing_key() -> str:
    return load_parameter("SSM_JWT_SIGNING_KEY", settings.ssm_jwt_signing_key)
