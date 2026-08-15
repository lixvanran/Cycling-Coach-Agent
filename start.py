#!/usr/bin/env python3
"""Cycling Coach 一键启动器(跨平台)

参考 Photographer-Copilot/start.py 风格:
- 自动装 venv / 镜像源
- 跨平台 shim(避免 Windows .cmd 找不到)
- 端口兜底
- stdout 直接继承给用户
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

# 关键:Windows 上 Python 默认 cp936(GBK)解码子进程 stdout
# Vite / pnpm / Node 经常输出非 GBK 字节,会直接挂掉
# 这里强制用 UTF-8 + 容错(避免 v0.1.0 的 "GBK decode 错误" 故障)
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

ROOT = Path(__file__).parent.resolve()
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
WORKSPACE_DIR = ROOT / "workspace"
LOG_DIR = WORKSPACE_DIR / ".logs"
PORT_FILE = WORKSPACE_DIR / ".sidecar-port"
PID_FILE = WORKSPACE_DIR / ".sidecar.pid"

BACKEND_PORT = int(os.environ.get("BACKEND_PORT", "8765"))
FRONTEND_PORT = int(os.environ.get("FRONTEND_PORT", "1420"))


# ---------- 工具 ----------

def log(msg: str, level: str = "info") -> None:
    """统一日志输出(带颜色)"""
    color_map = {
        "info": "\033[36m",     # cyan
        "ok": "\033[32m",       # green
        "warn": "\033[33m",     # yellow
        "err": "\033[31m",      # red
        "hint": "\033[35m",     # magenta
        "reset": "\033[0m",
    }
    c = color_map.get(level, "")
    r = color_map["reset"] if c else ""
    print(f"{c}[{level.upper()}]{r} {msg}", flush=True)


def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None,
        check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    """执行命令(带日志)"""
    cwd_str = str(cwd) if cwd else None
    log(f"$ {' '.join(cmd)}" + (f"  (cwd={cwd_str})" if cwd_str else ""))
    return subprocess.run(
        cmd, cwd=cwd_str, env=env, check=check,
        capture_output=capture, text=True,
    )


# ---------- 环境检查 ----------

def check_python() -> str:
    py = shutil.which("python3") or shutil.which("python")
    if not py:
        log("Python 3.11+ 未找到,请先安装", "err")
        sys.exit(1)
    # 版本检查
    out = subprocess.run([py, "--version"], capture_output=True, text=True)
    ver_str = out.stdout.strip() or out.stderr.strip()
    log(f"Python: {ver_str} ({py})", "ok")
    return py


def check_node() -> str | None:
    """返回 npm 可执行路径(可能是 .cmd);pnpm 缺失则装"""
    node = shutil.which("node")
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if not node or not npm:
        log("Node.js 未找到,前端无法启动", "warn")
        return None
    out = subprocess.run([node, "--version"], capture_output=True, text=True)
    log(f"Node: {out.stdout.strip()}", "ok")
    return npm


def ensure_pnpm(npm: str) -> str:
    pnpm = shutil.which("pnpm") or shutil.which("pnpm.cmd")
    if pnpm:
        log(f"pnpm: 已安装", "ok")
        return pnpm
    log("pnpm 未安装,自动安装...", "info")
    subprocess.run([npm, "install", "-g", "pnpm", "--registry=https://registry.npmmirror.com"], check=True)
    return shutil.which("pnpm") or shutil.which("pnpm.cmd")


# ---------- 依赖安装 ----------

def ensure_venv() -> Path:
    """创建/复用 .venv,返回 python 解释器路径"""
    venv = ROOT / ".venv"
    if platform.system() == "Windows":
        py_bin = venv / "Scripts" / "python.exe"
    else:
        py_bin = venv / "bin" / "python"
    if not py_bin.exists():
        log("创建 Python 虚拟环境 .venv ...", "info")
        run([sys.executable, "-m", "venv", str(venv)])
    return py_bin


def install_backend(py_bin: Path) -> None:
    log("安装后端依赖...", "info")
    # 配清华源(中国大陆常见网络环境)
    env = os.environ.copy()
    env["PIP_INDEX_URL"] = "https://pypi.tuna.tsinghua.edu.cn/simple"
    run([str(py_bin), "-m", "pip", "install", "--upgrade", "pip"], env=env)
    run([str(py_bin), "-m", "pip", "install", "-r", str(BACKEND_DIR / "requirements.txt")], env=env)
    log("后端依赖安装完成", "ok")


def install_frontend(pnpm: str) -> None:
    if (FRONTEND_DIR / "node_modules").exists():
        log("前端依赖已安装,跳过", "ok")
        return
    log("安装前端依赖...", "info")
    env = os.environ.copy()
    env["npm_config_registry"] = "https://registry.npmmirror.com"
    run([pnpm, "install"], cwd=FRONTEND_DIR, env=env)
    log("前端依赖安装完成", "ok")


# ---------- 端口清理 ----------

def kill_port(port: int) -> None:
    """兜底杀掉占用端口的进程"""
    system = platform.system()
    try:
        if system == "Windows":
            out = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True
            ).stdout
            for line in out.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    pid = parts[-1]
                    log(f"释放端口 {port}: kill PID {pid}", "warn")
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
        else:
            # macOS / Linux
            out = subprocess.run(
                ["lsof", "-ti", f":{port}"], capture_output=True, text=True
            ).stdout.strip()
            for pid in out.splitlines():
                if pid:
                    log(f"释放端口 {port}: kill PID {pid}", "warn")
                    subprocess.run(["kill", "-9", pid], capture_output=True)
    except Exception as e:
        log(f"端口清理失败(可忽略): {e}", "warn")


# ---------- 启动 ----------

def start_backend(py_bin: Path) -> subprocess.Popen:
    log(f"启动后端 Sidecar(端口 {BACKEND_PORT})...", "info")
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    # 以 backend.main:app 启动,让 backend 作为包被加载,相对导入才能用
    proc = subprocess.Popen(
        [str(py_bin), "-m", "uvicorn", "backend.main:app",
         "--host", "127.0.0.1", "--port", str(BACKEND_PORT)],
        cwd=ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, encoding="utf-8", errors="replace",
    )
    # 写 PID + 端口(给前端用)
    PID_FILE.write_text(str(proc.pid))
    PORT_FILE.write_text(str(BACKEND_PORT))
    log(f"后端 PID: {proc.pid}", "ok")
    return proc


def start_frontend(pnpm: str) -> subprocess.Popen | None:
    """启动 Vite(直接调 node_modules/.bin/vite,避免 pnpm + 中文路径的兼容问题)"""
    log(f"启动前端 Vite(端口 {FRONTEND_PORT})...", "info")

    # 找 node_modules/.bin/vite
    vite_bin = FRONTEND_DIR / "node_modules" / ".bin" / "vite"
    if platform.system() == "Windows":
        vite_bin = vite_bin.with_suffix(".cmd")

    if not vite_bin.exists():
        log(f"找不到 {vite_bin},回退到 pnpm dev", "warn")
        vite_bin = Path(pnpm)
        if platform.system() == "Windows" and not str(vite_bin).endswith(".cmd"):
            vite_bin = vite_bin.with_suffix(".cmd")
        use_shell = True
        cmd = [str(vite_bin), "dev", "--port", str(FRONTEND_PORT), "--strictPort"]
    else:
        use_shell = False
        cmd = [str(vite_bin), "--port", str(FRONTEND_PORT), "--strictPort", "--host", "127.0.0.1"]

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["FORCE_COLOR"] = "0"  # 避免 ANSI 颜色码让 stream reader 解析错

    log(f"  $ {' '.join(cmd)}")
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=FRONTEND_DIR, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, shell=use_shell,
            encoding="utf-8", errors="replace",
        )
    except Exception as e:
        log(f"Vite 启动失败: {e}", "err")
        return None
    log(f"前端 PID: {proc.pid}", "ok")
    return proc


def stream_output(proc: subprocess.Popen, prefix: str) -> None:
    """持续打印子进程输出(在独立线程里)

    关键:任何 IO 异常都不能让主线程误判进程退出
    """
    import threading
    def _reader():
        try:
            for line in iter(proc.stdout.readline, ""):
                if not line:
                    break
                # 处理一行可能有 BOM 或 \r
                line = line.replace("\r\n", "\n").rstrip("\n").rstrip("\r")
                if line:
                    print(f"[{prefix}] {line}", flush=True)
        except (ValueError, OSError):
            # pipe 已关,正常退出
            pass
        except Exception as e:
            # 任何其他异常只记一行,不抛
            try:
                print(f"[{prefix}] output reader error: {e}", flush=True)
            except Exception:
                pass
    t = threading.Thread(target=_reader, daemon=True)
    t.start()


# ---------- main ----------

def main() -> int:
    parser = argparse.ArgumentParser(description="Cycling Coach 一键启动")
    parser.add_argument("--check", action="store_true", help="只检查环境")
    parser.add_argument("--install", action="store_true", help="只装依赖")
    parser.add_argument("--no-frontend", action="store_true", help="不启动前端")
    args = parser.parse_args()

    log("=" * 50, "info")
    log("  Cycling Coach 启动器 v0.1.0", "info")
    log("=" * 50, "info")

    # 1. 环境检查
    py = check_python()
    npm = check_node()
    pnpm = ensure_pnpm(npm) if npm else None

    if args.check:
        log("环境检查完成", "ok")
        return 0

    # 2. 依赖安装
    py_bin = ensure_venv()
    install_backend(py_bin)
    if pnpm:
        install_frontend(pnpm)

    if args.install:
        log("依赖安装完成", "ok")
        return 0

    # 3. 端口清理
    kill_port(BACKEND_PORT)
    if pnpm:
        kill_port(FRONTEND_PORT)

    # 4. 启动
    try:
        backend_proc = start_backend(py_bin)
        stream_output(backend_proc, "BACKEND")
        # 等后端 ready(粗略 2s)
        time.sleep(2)
        frontend_proc = None
        if pnpm and not args.no_frontend:
            frontend_proc = start_frontend(pnpm)
            stream_output(frontend_proc, "FRONTEND")
            time.sleep(2)

        log("=" * 50, "ok")
        log(f"  应用已就绪", "ok")
        log(f"  前端: http://localhost:{FRONTEND_PORT}", "ok")
        log(f"  后端: http://127.0.0.1:{BACKEND_PORT}", "ok")
        log(f"  按 Ctrl+C 停止", "ok")
        log("=" * 50, "ok")

        # 阻塞,直到任一进程退出
        try:
            while True:
                time.sleep(1)
                if backend_proc.poll() is not None:
                    rc = backend_proc.poll()
                    log(f"后端进程退出(exit code {rc})", "err")
                    log("查看 workspace/.logs/sidecar.log 获取详细错误", "hint")
                    break
                if frontend_proc and frontend_proc.poll() is not None:
                    rc = frontend_proc.poll()
                    log(f"前端进程退出(exit code {rc})", "err")
                    log("尝试手动启动:cd frontend && node_modules/.bin/vite --port 1420", "hint")
                    break
        except KeyboardInterrupt:
            log("正在停止...", "info")
            for p in [backend_proc, frontend_proc]:
                if p and p.poll() is None:
                    p.terminate()
    except Exception as e:
        log(f"启动失败: {e}", "err")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
