from __future__ import annotations

from pydantic_settings import BaseSettings


class MinioSettings(BaseSettings):
    endpoint: str
    bucket: str
    access_key: str
    secret_key: str
    secure: bool
