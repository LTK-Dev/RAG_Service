from __future__ import annotations
from functools import lru_cache
from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
    YamlConfigSettingsSource,
)
from llm import EmbeddingSettings, LLMSettings
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

    server: ServerSettings
    embedding: EmbeddingSettings
    opensearch: OpenSearchSettings
    llm: LLMSettings

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
            env_settings,
            dotenv_settings,
            file_secret_settings,
            YamlConfigSettingsSource(settings_cls),
        )

@lru_cache(maxsize=None)
def get_settings() -> Settings:
    return Settings()
