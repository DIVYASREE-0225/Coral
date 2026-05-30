"""Runtime configuration loaded from environment variables.

Set GIGPROOF_SIGNING_KEY in production. The default is a clearly-marked
demo value used only when the env var is unset (i.e., for local hackathon runs).
"""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GIGPROOF_", case_sensitive=False)

    signing_key: str = Field(
        default="gigproof-demo-signing-key-not-for-production",
        description="HMAC key for income-certificate signatures.",
    )
    log_level: str = Field(default="INFO")
    log_json: bool = Field(default=False, description="Emit JSON logs (true in prod).")


settings = Settings()
