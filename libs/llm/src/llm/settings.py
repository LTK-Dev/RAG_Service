from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbeddingSettings(BaseSettings):
    model: str

class LLMSettings(BaseSettings):
    api_key: str
    temperature: float = 0.1
    top_p: float = 0.9
