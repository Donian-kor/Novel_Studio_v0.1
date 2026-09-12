from __future__ import annotations
import re
from datetime import datetime
from pathlib import Path

def now() -> str:
    return datetime.now().isoformat(timespec="seconds")

def count_chars(text: str, include_whitespace: bool = False) -> int:
    if include_whitespace:
        return len(text.replace("\r", ""))
    return len(re.sub(r"[\\r\\n\\t\\s]", "", text))

def safe_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip() or "unnamed"

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
