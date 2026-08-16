"""Cycling Coach 后端入口

参考 Photographer-Copilot main.py 风格:
- FastAPI lifespan
- CORS
- /api/diagnose
- 所有日志走 setup_logging
"""
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.logging import setup_logging
from .db import init_db
from .routers import activities, athlete, dashboard, diagnose, dev, coach


WORKSPACE = Path(settings.workspace_dir).resolve()
LOG_FILE = WORKSPACE / ".logs" / "sidecar.log"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时:配日志 + 建表"""
    setup_logging(settings.log_level, LOG_FILE)
    logger = logging.getLogger("backend.main")
    logger.info("=" * 50)
    logger.info("Cycling Coach Sidecar v0.1.0 启动")
    logger.info(f"Mock 模式: {settings.is_mock}")
    if not settings.is_mock:
        logger.info(f"M3 model: {settings.m3_model}")
    logger.info(f"Workspace: {WORKSPACE}")
    init_db()
    logger.info("=" * 50)
    yield
    logger.info("Sidecar 关闭")


app = FastAPI(
    title="Cycling Coach API",
    description="公路自行车 AI 教练 · 后端",
    version="0.1.2",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(activities.router)
app.include_router(athlete.router)
app.include_router(dashboard.router)
app.include_router(diagnose.router)
app.include_router(dev.router)
app.include_router(coach.router)
