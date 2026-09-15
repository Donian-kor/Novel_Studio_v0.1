from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
from typing import Any


@dataclass(frozen=True)
class ProjectPaths:
    """프로젝트에서 사용하는 주요 경로 묶음."""

    root: Path
    chapters: Path
    backups: Path
    exports: Path
    temp: Path


DEFAULT_PROJECT_SETTINGS: dict[str, Any] = {
    "title": "새 작품",
    "genre": "선협",
    "mood": "진중하고 어두운 분위기",
    "target_chapters": 500,
    "chapter_chars": 5000,
    "tolerance": 300,
    "section_size": 10,
    "long_story_size": 50,
    "sub_story_size": 10,
}


class ProjectManager:
    """프로젝트 파일과 원고 파일을 관리한다."""

    def __init__(self) -> None:
        self.active = False
        self.root: Path | None = None
        self.paths: ProjectPaths | None = None
        self.settings: dict[str, Any] = {}

    def create(
        self,
        *,
        root: str | Path,
        title: str,
        genre: str,
        mood: str,
        total_chapters: int,
        chapter_chars: int,
        tolerance: int,
        section_size: int = 10,
        long_story_size: int = 50,
        sub_story_size: int = 10,
    ) -> None:
        """새 프로젝트를 생성한다."""
        project_root = Path(root)
        project_root.mkdir(parents=True, exist_ok=True)
        self._set_paths(project_root)
        self.settings = {
            "title": title,
            "genre": genre,
            "mood": mood,
            "target_chapters": int(total_chapters),
            "chapter_chars": int(chapter_chars),
            "tolerance": int(tolerance),
            "section_size": int(section_size),
            "long_story_size": int(long_story_size),
            "sub_story_size": int(sub_story_size),
        }
        self._save_project_json()
        self.active = True

    def open(self, root: str | Path) -> None:
        """기존 프로젝트를 연다."""
        project_root = Path(root)
        project_file = project_root / "project.json"
        if not project_file.exists():
            raise FileNotFoundError("project.json이 없는 Novel Studio 프로젝트입니다.")
        data = json.loads(project_file.read_text(encoding="utf-8"))
        self._set_paths(project_root)
        self.settings = dict(data.get("settings", {}))
        self.ensure_defaults()
        self.active = True

    def ensure_defaults(self) -> None:
        """기존 프로젝트의 누락 설정만 기본값으로 보완한다."""
        changed = False
        for key, value in DEFAULT_PROJECT_SETTINGS.items():
            if key not in self.settings:
                self.settings[key] = value
                changed = True
        if changed:
            self._save_project_json()

    def save_settings(self, values: dict[str, Any]) -> None:
        """프로젝트 설정을 병합하고 저장한다."""
        self.settings.update(values)
        self._save_project_json()

    def _save_project_json(self) -> None:
        """project.json을 저장한다."""
        if self.root is None:
            raise RuntimeError("프로젝트가 없습니다.")
        target = self.root / "project.json"
        temporary = self.root / "project.json.tmp"
        payload = json.dumps({"settings": self.settings}, ensure_ascii=False, indent=2)
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, target)

    def _set_paths(self, root: Path) -> None:
        self.root = root
        dirs = {key: root / key for key in ("chapters", "backups", "exports", "temp")}
        for path in dirs.values():
            path.mkdir(parents=True, exist_ok=True)
        self.paths = ProjectPaths(root, dirs["chapters"], dirs["backups"], dirs["exports"], dirs["temp"])

    def chapter_path(self, number: int) -> Path:
        """지정한 화의 원고 경로를 반환한다."""
        if self.paths is None:
            raise RuntimeError("프로젝트가 없습니다.")
        return self.paths.chapters / f"{int(number):03d}.txt"

    def load_chapter(self, number: int) -> str:
        """원고 파일을 읽어 반환한다."""
        path = self.chapter_path(number)
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def save_chapter(self, number: int, text: str) -> Path:
        """원고를 임시 파일로 저장한 뒤 원자적으로 교체한다."""
        if self.paths is None:
            raise RuntimeError("프로젝트가 없습니다.")
        path = self.chapter_path(number)
        backup = self.paths.backups / f"{int(number):03d}.txt.bak"
        if path.exists():
            try:
                shutil.copy2(path, backup)
            except OSError:
                pass
        temporary = self.paths.temp / f"chapter_{int(number):03d}.tmp"
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, path)
        return path

    def export_all_chapters(self) -> Path:
        """작성된 전체 원고를 exports/ 폴더에 하나의 텍스트 파일로 저장한다."""
        if self.paths is None:
            raise RuntimeError("프로젝트가 없습니다.")
        from datetime import datetime

        total = int(self.settings.get("target_chapters", 0))
        parts: list[str] = []
        for number in range(1, total + 1):
            text = self.load_chapter(number)
            if text.strip():
                parts.append(f"{'=' * 24}\n제{number}화\n{'=' * 24}\n{text.strip()}")
        if not parts:
            raise RuntimeError("내보낼 원고가 없습니다.")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        title = str(self.settings.get("title") or "novel").strip().replace("/", "_").replace("\\", "_")
        output = self.paths.exports / f"{title}_전체원고_{stamp}.txt"
        output.write_text("\n\n".join(parts), encoding="utf-8")
        return output
