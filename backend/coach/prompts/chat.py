"""chat 场景 prompt — 普通问答,不绑定活动"""
from __future__ import annotations

CHAT_USER_HEADER = """以下是车友和你的对话。车友可能会问训练相关问题,也可能问装备/比赛/伤病/营养等。

记住:数据是依据,人是目的。回答要短、有用、可执行。

## 上下文
- 车友: {athlete_name}
- 训练经验: 未知(如有 athlete 资料会附在 system prompt)
"""


def build_chat_messages(
    history: list[dict], user_message: str, athlete_name: str = "Rider"
) -> tuple[str, list[dict]]:
    """构造 (system, messages)

    history: [{"role": "user"/"assistant", "content": "..."}, ...]
    user_message: 当前用户输入
    """
    from .style import get_style_prompt

    system = get_style_prompt() + "\n\n" + CHAT_USER_HEADER.format(athlete_name=athlete_name)
    messages = []
    for m in history:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_message})
    return system, messages
