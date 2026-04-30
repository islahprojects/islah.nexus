from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "jajis2026-grand-bridge"
    PUBLIC_BASE_URL: str = "http://localhost:9000"
    PUBLIC_DOMAIN: str = "localhost"
    BRIDGE_API_TOKEN: str = "dev-local-token-change-me"
    FOUNDERS_SEED: str = "change-me-strong-random-secret"
    VAULT_DIR: str = "./vault"
    FRONTEND_DIR: str = "./frontend"
    ALLOW_EXTERNAL_HTTP_APIS: bool = False
    ALLOWED_API_HOSTS: str = ""
    OLLAMA_BASE_URL: str = ""
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    MAX_MEMORY_RECORDS: int = 5000
    DEV_PLAINTEXT_MODE: bool = False
    CORS_ORIGINS: str = "http://localhost:9000,http://localhost:5173"

    @property
    def vault_path(self) -> Path:
        return Path(self.VAULT_DIR)

    @property
    def frontend_path(self) -> Path:
        return Path(self.FRONTEND_DIR)

    @property
    def wal_path(self) -> Path:
        return self.vault_path / "wal.log"

    @property
    def memory_path(self) -> Path:
        return self.vault_path / "memory.jsonl"

    @property
    def commitments_path(self) -> Path:
        return self.vault_path / "commitments.jsonl"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def allowed_hosts(self) -> set[str]:
        return {host.strip().lower() for host in self.ALLOWED_API_HOSTS.split(",") if host.strip()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
