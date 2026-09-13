from __future__ import annotations
from pathlib import Path
import json

DEFAULT = {
    "active_provider": "lmstudio",
    "providers": {
        "lmstudio": {"base_url": "http://localhost:1234/v1", "model": ""},
        "openai": {"base_url": "https://api.openai.com/v1", "model": ""},
        "anthropic": {"base_url": "https://api.anthropic.com", "model": ""},
        "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta", "model": ""},
        "openai_compatible": {"base_url": "", "model": ""},
    },
    "ai": {"temperature": 0.72, "top_p": 0.90, "max_tokens": 9000, "memory_recent_chapters": 4, "previous_tail_chars": 1500, "context_budget_tokens": 60000},
    "editor": {"font_family": "Malgun Gothic", "font_size": 18, "text_color": "#E8E6E3", "bg_color": "#2B2B2B", "line_spacing": 1.4},
}

class AppSettings:
    def __init__(self):
        self.path = Path.home() / ".novel_studio_settings.json"
        self.data = json.loads(json.dumps(DEFAULT, ensure_ascii=False))
        if self.path.exists():
            try:
                saved = json.loads(self.path.read_text(encoding="utf-8"))
                self._merge(self.data, saved)
            except Exception:
                pass
        self.save()

    def _merge(self, base, update):
        for k, v in update.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                self._merge(base[k], v)
            else:
                base[k] = v

    def save(self):
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
