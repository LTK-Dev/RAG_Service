from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenSearchSettings(BaseSettings):
    host: str
    port: int
    http_auth_user: str
    http_auth_pass: str
    index_name: str
    use_ssl: bool = False
    verify_certs: bool = False
    ssl_assert_hostname: bool = False
    embedding_dim: int = 768
    pipeline_name: str = 'min_max-search-pipeline'
