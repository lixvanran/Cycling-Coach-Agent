"""SQLite + SQLAlchemy 初始化

参考 ZhangXuefeng-Agent 风格:单文件 DB + 自动 schema 迁移
"""
from __future__ import annotations
import logging
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from ..core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def _db_path() -> str:
    """workspace/cycling_coach.sqlite"""
    workspace = Path(settings.workspace_dir).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    db_file = workspace / "cycling_coach.sqlite"
    return f"sqlite:///{db_file}"


engine = create_engine(
    _db_path(),
    connect_args={"check_same_thread": False},
    echo=False,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _):
    """SQLite 性能优化 + 兼容性

    v0.1.0:默认 rollback journal 模式,避免挂载文件系统上 WAL 失败
    后续 V0.2 视情况再开 WAL
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """建表(MVP 用 create_all,V0.2 加 schema 迁移)"""
    from . import models  # noqa: F401  注册表
    Base.metadata.create_all(engine)
    logger.info("数据库初始化完成")


def get_db() -> Session:
    """FastAPI 依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
