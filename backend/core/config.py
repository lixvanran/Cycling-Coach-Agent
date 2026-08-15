"""Cycling Coach 后端配置

参考 Photographer-Copilot 风格:集中 .env 配置 + 友好 mock 兜底
"""
from __future__ import annotations
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM(OpenRouter 兼容协议)
    m3_base_url: str = "https://openrouter.ai/api/v1"
    m3_api_key: Optional[str] = None
    m3_model: str = "minimax/minimax-m3"

    # 后端
    backend_host: str = "127.0.0.1"
    backend_port: int = 8765
    log_level: str = "INFO"

    # 前端(用于 CORS)
    frontend_port: int = 1420
    cors_origins: str = "http://localhost:1420,http://127.0.0.1:1420"

    # Workspace(相对于 backend 父目录,即启动器 cwd=ROOT)
    workspace_dir: str = "workspace"

    @property
    def is_mock(self) -> bool:
        """没有 API key 时进入 mock 模式(对齐 P 项目)"""
        return not self.m3_api_key or not self.m3_api_key.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
