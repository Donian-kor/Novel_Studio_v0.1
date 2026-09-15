from __future__ import annotations
from pathlib import Path
import json
from typing import Any

DEFAULT = {
    "active_provider": "lmstudio",
    "providers": {
        "lmstudio": {"base_url": "http://localhost:1234/v1", "model": ""},
        "openai": {"base_url": "https://api.openai.com/v1", "model": ""},
        "anthropic": {"base_url": "https://api.anthropic.com", "model": ""},
        "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta", "model": ""},
        "openai_compatible": {"base_url": "", "model": ""},
    },
    "ai": {"temperature": 0.72, "top_p": 0.90, "max_tokens": 9000, "end_state_recent_chapters": 4, "previous_tail_chars": 1500, "context_budget_tokens": 60000},
    "editor": {"font_family": "Malgun Gothic", "font_size": 18, "text_color": "#E8E6E3", "bg_color": "#2B2B2B", "line_spacing": 1.4, "auto_generate_end_state": False},
    "ui": {"geometry": "", "window_state": "", "left_panel_visible": True, "right_panel_visible": True, "selected_nav": 0},
}

class AppSettings:
    """애플리케이션 전역 설정을 읽고 저장한다."""

    def __init__(self) -> None:
        self.path = Path.home() / ".novel_studio_settings.json"
        self.data = json.loads(json.dumps(DEFAULT, ensure_ascii=False))
        if self.path.exists():
            try:
                saved = json.loads(self.path.read_text(encoding="utf-8"))
                self._merge(self.data, saved)
            except Exception:
                pass
        self.save()

    def _merge(self, base: dict[str, Any], update: dict[str, Any]) -> None:
        for k, v in update.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                self._merge(base[k], v)
            else:
                base[k] = v

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")


    def set_ui_state(self, **values: Any) -> None:
        """UI 상태 값을 저장한다."""
        self.data.setdefault("ui", {}).update(values)

    def get_ui_state(self, key: str, default: Any = None) -> Any:
        """저장된 UI 상태 값을 반환한다."""
        return self.data.get("ui", {}).get(key, default)
