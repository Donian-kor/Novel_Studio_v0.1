from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json, os, shutil

@dataclass
class ProjectPaths:
    root: Path
    chapters: Path
    backups: Path
    exports: Path
    temp: Path

DEFAULT_PROJECT_SETTINGS = {
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
    def __init__(self):
        self.active = False
        self.root = None
        self.paths = None
        self.settings = {}

    def create(
        self,
        *,
        root,
        title,
        genre,
        mood,
        total_chapters,
        chapter_chars,
        tolerance,
        section_size=10,
        long_story_size=50,
        sub_story_size=10,
    ):
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        self._set_paths(root)
        self.settings = {
            "title": title, "genre": genre, "mood": mood,
            "target_chapters": int(total_chapters), "chapter_chars": int(chapter_chars),
            "tolerance": int(tolerance), "section_size": int(section_size),
            "long_story_size": int(long_story_size), "sub_story_size": int(sub_story_size)
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
        self.ensure_defaults()
        self.active = True

    def ensure_defaults(self):
        """오래된 프로젝트.json에도 필요한 기본 설정값이 남아 있도록 보정한다.

        기존 값을 덮어쓰지 않고, 없는 키만 DEFAULT_PROJECT_SETTINGS 값으로 채운다.
        하나라도 보정됐으면 project.json을 다시 저장해서 다음 실행부터는 정상 상태로 만든다.
        """
        changed = False
        for k, v in DEFAULT_PROJECT_SETTINGS.items():
            if k not in self.settings:
                self.settings[k] = v
                changed = True
        if changed:
            self._save_project_json()

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
        path=self.chapter_path(number)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp=self.paths.temp / f"chapter_{int(number):03d}.tmp"
        backup=self.paths.backups / f"{int(number):03d}.txt.bak"
        if path.exists():
            try: shutil.copy2(path, backup)
            except OSError: pass
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
        return path

    def export_all_chapters(self):
        """작성된 전체 원고를 exports/ 폴더에 단일 텍스트 파일로 병합 저장."""
        if not self.paths:
            raise RuntimeError("프로젝트가 없습니다.")
        from datetime import datetime
        total = int(self.settings.get("target_chapters", 0))
        parts = []
        for n in range(1, total + 1):
            text = self.load_chapter(n)
            if text.strip():
                parts.append(f"{'=' * 24}\n제{n}화\n{'=' * 24}\n{text.strip()}")
        if not parts:
            raise RuntimeError("내보낼 원고가 없습니다.")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        title = (self.settings.get("title") or "novel").strip().replace("/", "_").replace("\\", "_")
        out = self.paths.exports / f"{title}_전체원고_{stamp}.txt"
        out.write_text("\n\n".join(parts), encoding="utf-8")
        return out
