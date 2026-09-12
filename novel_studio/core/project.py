from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from .helpers import now, read_text, write_text

@dataclass
class ProjectPaths:
    root: Path
    @property
    def db(self): return self.root / "novel.db"
    @property
    def chapters(self): return self.root / "chapters"
    @property
    def plans(self): return self.root / "plans"
    @property
    def memory(self): return self.root / "memory"
    @property
    def backups(self): return self.root / "backups"
    @property
    def exports(self): return self.root / "exports"
    @property
    def settings(self): return self.root / "project.json"

class ProjectManager:
    def __init__(self):
        self.paths: ProjectPaths | None = None
        self.settings: dict = {}
    @property
    def active(self): return self.paths is not None
    def create(self, root: Path, title: str, genre: str, target_chapters: int, chapter_chars: int, tolerance: int):
        root.mkdir(parents=True, exist_ok=True)
        self.paths = ProjectPaths(root)
        for p in (self.paths.chapters, self.paths.plans, self.paths.memory, self.paths.backups, self.paths.exports): p.mkdir(exist_ok=True)
        self.settings = {
            "title": title or root.name, "genre": genre, "target_chapters": target_chapters,
            "chapter_chars": chapter_chars, "char_tolerance": tolerance, "char_mode": "균형",
            "created_at": now(), "updated_at": now(), "lmstudio_url": "http://localhost:1234", "model": ""
        }
        self.paths.settings.write_text(json.dumps(self.settings, ensure_ascii=False, indent=2), encoding="utf-8")
        return self.paths
    def open(self, root: Path):
        settings_path = root / "project.json"
        if not settings_path.exists(): raise FileNotFoundError("project.json이 없는 프로젝트 폴더입니다.")
        self.paths = ProjectPaths(root)
        self.settings = json.loads(settings_path.read_text(encoding="utf-8"))
        for p in (self.paths.chapters, self.paths.plans, self.paths.memory, self.paths.backups, self.paths.exports): p.mkdir(exist_ok=True)
        return self.paths
    def save_settings(self):
        if not self.paths: return
        self.settings["updated_at"] = now()
        self.paths.settings.write_text(json.dumps(self.settings, ensure_ascii=False, indent=2), encoding="utf-8")
    def chapter_path(self, number: int) -> Path:
        if not self.paths: raise RuntimeError("프로젝트가 열려 있지 않습니다.")
        return self.paths.chapters / f"{number:03d}.txt"
    def load_chapter(self, number: int) -> str: return read_text(self.chapter_path(number))
    def save_chapter(self, number: int, text: str): write_text(self.chapter_path(number), text)
