"""Application configuration using Pydantic settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 3000
    log_level: str = "info"
    debug: bool = False

    # JIRA
    jira_url: str = ""
    jira_username: str = ""
    jira_api_token: str = ""

    # GL News Database
    glnews_db_host: str = ""
    glnews_db_port: int = 5432
    glnews_db_name: str = "glnews"
    glnews_db_user: str = ""
    glnews_db_password: str = ""

    # GL Chat Database
    glchat_db_host: str = ""
    glchat_db_port: int = 5432
    glchat_db_name: str = "glchat"
    glchat_db_user: str = ""
    glchat_db_password: str = ""

    # Keycloak
    auth_enabled: bool = False
    keycloak_url: str = ""
    keycloak_realm: str = "godfreylabs"
    required_role: str = ""

    # OAuth
    server_url: str = "http://localhost:3000"
    dev_mcp_client_id: str = ""
    dev_mcp_client_secret: str = ""

    # Vault
    vault_github_token: str = ""


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
