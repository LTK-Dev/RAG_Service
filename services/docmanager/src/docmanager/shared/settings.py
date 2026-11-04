from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
    YamlConfigSettingsSource,
)
from postgres import PostgresSettings
from storage import MinioSettings
from llm import EmbeddingSettings
from open_search import OpenSearchSettings


class ServerSettings(BaseSettings):
    host: str
    port: int
    reload: bool


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        yaml_file=str(Path(__file__).parent.parent / 'settings.yaml'),
    )

    postgres: PostgresSettings
    minio: MinioSettings
    server: ServerSettings
    embedding: EmbeddingSettings
    opensearch: OpenSearchSettings

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,     # Ưu tiên 1: Biến môi trường hệ thống
            dotenv_settings,  # Ưu tiên 2: File .env
            file_secret_settings,
            YamlConfigSettingsSource(settings_cls),
        )

@lru_cache(maxsize=None)
def get_settings() -> Settings:
    return Settings()
