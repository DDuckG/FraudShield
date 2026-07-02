from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]

# Load sớm để chạy local đỡ phải export từng biến trong terminal.
load_dotenv(ROOT_DIR / ".env")


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def env_path(name: str, default: str) -> Path:
    raw = env(name, default)
    path = Path(raw)
    return path if path.is_absolute() else ROOT_DIR / path
