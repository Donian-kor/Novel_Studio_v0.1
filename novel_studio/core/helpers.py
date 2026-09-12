from __future__ import annotations
from datetime import datetime
from pathlib import Path
import re


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def count_chars(text: str, include_spaces: bool = False) -> int:
    if include_spaces:
        return len(text.replace("\r", ""))
    return len(re.sub(r"[\s\u200b]+", "", text))


def safe_filename(text: str, default: str = "project") -> str:
    text = re.sub(r'[<>:"/\\|?*]+', "_", text.strip())
    return text or default


def ensure_text_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
