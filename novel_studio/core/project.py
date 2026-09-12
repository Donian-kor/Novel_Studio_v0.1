from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
from novel_studio.core.helpers import ensure_text_file, safe_filename


@dataclass
class ProjectPaths:
    root: Path
    chapters: Path
    backups: Path
    exports: Path
    temp: Path


DEFAULT_SETTINGS = {
    "title": "새 작품",
    "genre": "선협",
    "mood": "진중하고 어두운 분위기",
    "target_chapters": "500",
    "chapter_chars": "5000",
    "tolerance": "300",
    "section_size": "5",
    "lmstudio_url": "http://localhost:1234",
    "model": "",
    "temperature": "0.72",
    "top_p": "0.90",
    "max_tokens": "9000",
    "memory_recent_chapters": "4",
    "previous_tail_chars": "1500",
    "editor_font_family": "Malgun Gothic",
    "editor_font_size": "18",
    "editor_text_color": "#222222",
    "editor_bg_color": "#FFFDF5",
    "editor_line_spacing": "1.4",
}


class ProjectManager:
    def __init__(self) -> None:
        self.active = False
        self.root: Path | None = None
        self.paths: ProjectPaths | None = None
        self.settings: dict[str, str] = {}

    def create(self, root: Path, title: str, genre: str, mood: str, total_chapters: int, chapter_chars: int, tolerance: int) -> None:
        root.mkdir(parents=True, exist_ok=True)
        self._set_paths(root)
        self.settings = {**DEFAULT_SETTINGS,
            "title": title, "genre": genre, "mood": mood,
            "target_chapters": str(total_chapters), "chapter_chars": str(chapter_chars), "tolerance": str(tolerance)}
        self._write_project_json()
        self.active = True

    def open(self, root: Path) -> None:
        project_file = root / "project.json"
        if not project_file.exists():
            raise FileNotFoundError("project.json이 없는 Novel Studio 프로젝트입니다.")
        data = json.loads(project_file.read_text(encoding="utf-8"))
        self._set_paths(root)
        self.settings = {**DEFAULT_SETTINGS, **{str(k): str(v) for k, v in data.get("settings", {}).items()}}
        self.active = True

    def save_settings(self, values: dict[str, str]) -> None:
        self.settings.update({str(k): str(v) for k, v in values.items()})
        self._write_project_json()

    def _write_project_json(self) -> None:
        assert self.root is not None
        payload = {"settings": self.settings}
        (self.root / "project.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _set_paths(self, root: Path) -> None:
        self.root = root
        chapters = root / "chapters"
        backups = root / "backups"
        exports = root / "exports"
        temp = root / "temp"
        for p in (chapters, backups, exports, temp):
            p.mkdir(parents=True, exist_ok=True)
        self.paths = ProjectPaths(root, chapters, backups, exports, temp)

    def chapter_path(self, number: int) -> Path:
        if not self.paths:
            raise RuntimeError("프로젝트가 없습니다.")
        return self.paths.chapters / f"{number:03d}.txt"

    def load_chapter(self, number: int) -> str:
        path = self.chapter_path(number)
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def save_chapter(self, number: int, text: str) -> None:
        path = self.chapter_path(number)
        ensure_text_file(path)
        path.write_text(text, encoding="utf-8")
