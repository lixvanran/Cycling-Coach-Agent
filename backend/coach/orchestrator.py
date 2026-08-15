"""AI 教练编排器 — v0.1.1 简化版

只做 chat(没有工具调用循环),SSE 流式输出
后续 V0.4 加多轮工具循环
"""
from __future__ import annotations
import logging
from typing import Generator

from .m3_client import get_m3, M3Error, M3AuthError, M3NetworkError, M3QuotaError
from .prompts.chat import build_chat_messages
from ..profile import store as profile_store
from ..db.database import SessionLocal
from ..db.models import Athlete

logger = logging.getLogger(__name__)


def stream_chat(
    history: list[dict],
    user_message: str,
) -> Generator[str, None, None]:
    """流式 chat 编排

    Yields:
      "data: <text>\n\n"  — 文本块(SSE 格式)
      "data: [DONE]\n\n"  — 结束
      "data: [ERROR] <msg>\n\n" — 错误
    """
    # 取 athlete 名字(简单,从第一个 athlete 取)
    db = SessionLocal()
    try:
        athlete = profile_store.get_or_create_athlete(db)
        athlete_name = athlete.name
    finally:
        db.close()

    system, messages = build_chat_messages(history, user_message, athlete_name=athlete_name)
    m3 = get_m3()

    try:
        for chunk in m3.stream_chat(system, messages):
            # SSE 安全转义
            chunk_safe = chunk.replace("\n", "\\n")
            yield f"data: {chunk_safe}\n\n"
        yield "data: [DONE]\n\n"
    except (M3AuthError, M3QuotaError, M3NetworkError) as e:
        logger.error(f"chat 致命错: {e}")
        msg = str(e).replace("\n", " ")
        yield f"data: [ERROR] {msg}\n\n"
    except M3Error as e:
        logger.error(f"chat 错误: {e}")
        msg = str(e).replace("\n", " ")
        yield f"data: [ERROR] {msg}\n\n"
    except Exception as e:
        logger.exception(f"chat 未知错误: {e}")
        msg = str(e).replace("\n", " ")
        yield f"data: [ERROR] {msg}\n\n"
