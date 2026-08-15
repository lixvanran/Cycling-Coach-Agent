#!/usr/bin/env python3
"""生成诊断报告(diagnose.txt)"""
from __future__ import annotations
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
WORKSPACE_DIR = ROOT / "workspace"
LOG_FILE = WORKSPACE_DIR / ".logs" / "sidecar.log"
OUT_FILE = ROOT / "diagnose.txt"


def main() -> int:
    lines: list[str] = []
    lines.append("===== Cycling Coach 诊断报告 =====\n")
    lines.append(f"时间: {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}")
    lines.append(f"系统: {platform.system()} {platform.release()}")
    lines.append(f"Python: {sys.version}")
    lines.append("")

    lines.append("===== 环境 =====")
    for cmd in [["node", "--version"], ["npm", "--version"], ["pnpm", "--version"]]:
        out = subprocess.run(cmd, capture_output=True, text=True)
        ver = out.stdout.strip() or out.stderr.strip() or "(未安装)"
        lines.append(f"{cmd[0]}: {ver}")
    lines.append("")

    lines.append("===== 目录检查 =====")
    for d in [".venv", "backend", "frontend", "workspace"]:
        p = ROOT / d
        lines.append(f"{d}: {'OK' if p.exists() else 'MISSING'}")
    lines.append("")

    lines.append("===== 端口检查 =====")
    for port in [8765, 1420]:
        out = subprocess.run(
            ["netstat", "-ano"] if platform.system() == "Windows" else ["lsof", "-i", f":{port}"],
            capture_output=True, text=True,
        )
        if str(port) in out.stdout:
            lines.append(f"端口 {port}: 已被占用")
        else:
            lines.append(f"端口 {port}: 空闲")
    lines.append("")

    lines.append("===== 后端日志(最近 50 行) =====")
    if LOG_FILE.exists():
        try:
            text = LOG_FILE.read_text(encoding="utf-8", errors="ignore")
            tail = "\n".join(text.splitlines()[-50:])
            lines.append(tail)
        except Exception as e:
            lines.append(f"读取失败: {e}")
    else:
        lines.append("(无日志,后端可能未启动)")

    OUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"诊断报告已写入: {OUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
