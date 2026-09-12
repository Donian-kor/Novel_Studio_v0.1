from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class ProjectPaths:
    root: Path
    chapters: Path
    backups: Path
    exports: Path
    temp: Path

class ProjectManager:
    def __init__(self):
        self.active = False
        self.root = None
        self.paths = None
        self.settings = {}

    def create(self, root, title, genre, mood, total_chapters, chapter_chars, tolerance, section_size=5):
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        self._set_paths(root)
        self.settings = {
            "title": title, "genre": genre, "mood": mood,
            "target_chapters": int(total_chapters), "chapter_chars": int(chapter_chars),
            "tolerance": int(tolerance), "section_size": int(section_size)
        }
        self._save_project_json()
        self.active = True

    def open(self, root):
        root = Path(root)
        f = root / "project.json"
        if not f.exists():
            raise FileNotFoundError("project.json이 없는 Novel Studio 프로젝트입니다.")
        data = json.loads(f.read_text(encoding="utf-8"))
        self._set_paths(root)
        self.settings = data.get("settings", {})
        self.active = True

    def save_settings(self, values):
        self.settings.update(values)
        self._save_project_json()

    def _save_project_json(self):
        (self.root / "project.json").write_text(json.dumps({"settings": self.settings}, ensure_ascii=False, indent=2), encoding="utf-8")

    def _set_paths(self, root):
        self.root = root
        dirs = {k: root / k for k in ("chapters", "backups", "exports", "temp")}
        for p in dirs.values():
            p.mkdir(parents=True, exist_ok=True)
        self.paths = ProjectPaths(root, dirs["chapters"], dirs["backups"], dirs["exports"], dirs["temp"])

    def chapter_path(self, number):
        if not self.paths:
            raise RuntimeError("프로젝트가 없습니다.")
        return self.paths.chapters / f"{int(number):03d}.txt"

    def load_chapter(self, number):
        path = self.chapter_path(number)
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def save_chapter(self, number, text):
        self.chapter_path(number).write_text(text, encoding="utf-8")
