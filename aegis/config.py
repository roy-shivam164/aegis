"""Central configuration for AEGIS, loaded from environment variables."""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AegisSettings(BaseSettings):
    """All AEGIS runtime configuration, sourced from .env or environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── OpenAI ────────────────────────────────────────────────
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"

    # ── Qdrant ────────────────────────────────────────────────
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""

    # ── Hermes ────────────────────────────────────────────────
    hermes_home: str = "~/.hermes"
    hermes_skills_dir: str = "~/.hermes/skills/aegis"

    # ── Notifications ─────────────────────────────────────────
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    discord_webhook_url: str = ""

    # ── AEGIS Behaviour ───────────────────────────────────────
    aegis_log_level: str = "INFO"
    aegis_heartbeat_interval_minutes: int = 30
    aegis_similarity_threshold: float = 0.75
    aegis_max_proactive_notifications_per_day: int = 10

    # ── API ───────────────────────────────────────────────────
    aegis_api_host: str = "0.0.0.0"
    aegis_api_port: int = 8000
    aegis_api_cors_origins: str = "http://localhost:5173"

    # ── Qdrant collection names ───────────────────────────────
    collection_failure_traces: str = "failure_traces"
    collection_skill_documents: str = "skill_documents"
    collection_user_life_log: str = "user_life_log"
    collection_user_patterns: str = "user_patterns"
    collection_person_profiles: str = "person_profiles"

    # ── Vector dimensions ─────────────────────────────────────
    dim_large: int = 1536   # OpenAI text-embedding-3-small
    dim_small: int = 384    # all-MiniLM-L6-v2 (sentiment)

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list."""
        return [o.strip() for o in self.aegis_api_cors_origins.split(",")]


@lru_cache(maxsize=1)
def get_settings() -> AegisSettings:
    """Return the singleton settings instance (cached after first call)."""
    return AegisSettings()


# Module-level convenience alias
settings = get_settings()
