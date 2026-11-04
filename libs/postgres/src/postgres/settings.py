from __future__ import annotations

from pydantic_settings import BaseSettings


class PostgresSettings(BaseSettings):
    user: str
    password: str
    host: str
    db: str
    port: int

    @property
    def dsn(self) -> str:
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"
