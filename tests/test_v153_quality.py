from __future__ import annotations

import inspect
import json
import sqlite3
import tempfile
from pathlib import Path

from novel_studio.core.project import ProjectManager
from novel_studio.db.project_database import ProjectDatabase



def make_project(td: str | Path) -> Path:
    root = Path(td) / "novel"
    ProjectManager().create(
        root=root,
        title="검증 작품",
        genre="선협",
        mood="진중",
        total_chapters=3,
        chapter_chars=5000,
        tolerance=300,
    )
    return root


def test_project_json_is_replaced_atomically(tmp_path: Path) -> None:
    pm = ProjectManager()
    root = make_project(tmp_path)
    pm.open(root)
    pm.save_settings({"title": "변경된 작품"})
    payload = json.loads((root / "project.json").read_text(encoding="utf-8"))
    assert payload["settings"]["title"] == "변경된 작품"
    assert not (root / "project.json.tmp").exists()


def test_project_save_chapter_preserves_previous_backup(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    pm = ProjectManager()
    pm.open(root)
    pm.save_chapter(1, "첫 번째 원고")
    pm.save_chapter(1, "두 번째 원고")
    assert pm.load_chapter(1) == "두 번째 원고"
    assert (root / "backups" / "001.txt.bak").read_text(encoding="utf-8") == "첫 번째 원고"


def test_partial_legacy_project_can_open_without_snapshot_runtime(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    legacy = root / "novel.db"
    con = sqlite3.connect(legacy)
    con.execute("CREATE TABLE plans(id INTEGER PRIMARY KEY, content TEXT)")
    con.execute("INSERT INTO plans(id, content) VALUES(1, '기존 기획')")
    con.execute("CREATE TABLE story_sections(id INTEGER PRIMARY KEY, start_chapter INTEGER, end_chapter INTEGER, status TEXT, content TEXT, updated_at TEXT)")
    con.commit()
    con.close()

    db = ProjectDatabase(root)
    try:
        assert db.get_plan() == "기존 기획"
    finally:
        db.close()


def test_key_project_methods_have_return_annotations() -> None:
    for name in ("create", "open", "save_settings", "chapter_path", "load_chapter", "save_chapter", "export_all_chapters"):
        assert inspect.signature(getattr(ProjectManager, name)).return_annotation is not inspect.Signature.empty
