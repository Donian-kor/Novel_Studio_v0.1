import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

from novel_studio.db.project_database import ProjectDatabase
from novel_studio.core.project import ProjectManager

ROOT = Path(__file__).resolve().parents[1]


class TestV151Stability(unittest.TestCase):
    def make_project(self, td):
        root = Path(td) / "novel"
        pm = ProjectManager()
        pm.create(
            root=root,
            title="테스트",
            genre="선협",
            mood="진중",
            total_chapters=3,
            chapter_chars=5000,
            tolerance=300,
            section_size=10,
            long_story_size=50,
            sub_story_size=10,
        )
        return root

    def test_db_context_releases_windows_file_handle(self):
        with tempfile.TemporaryDirectory() as td:
            root = self.make_project(td)
            with ProjectDatabase(root) as db:
                db.ensure_chapters(3, 5000)
            # Windows에서도 이 시점에는 DB 파일을 다시 열고 삭제할 수 있어야 한다.
            con = sqlite3.connect(root / "db" / "story.db")
            con.execute("SELECT 1")
            con.close()
            import shutil
            shutil.rmtree(root)

    def test_project_database_close_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root = self.make_project(td)
            db = ProjectDatabase(root)
            db.close()
            db.close()

    def test_factory_is_the_only_service_constructor(self):
        impl = (ROOT / "novel_studio" / "services" / "implementations.py").read_text(encoding="utf-8")
        factory = (ROOT / "novel_studio" / "factories.py").read_text(encoding="utf-8")
        self.assertNotIn("def create_services(", impl)
        self.assertIn("ServiceFactory", factory)
        self.assertNotIn("from novel_studio.db.database import", impl)

    def test_snapshot_implementation_files_are_removed(self):
        self.assertFalse((ROOT / "novel_studio" / "jobs" / "snapshot.py").exists())
        self.assertFalse((ROOT / "novel_studio" / "db" / "database.py").exists())
        for path in (ROOT / "novel_studio").rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("snapshotBtn", text)

    def test_snapshot_refs_are_only_legacy_migration(self):
        refs = {}
        for path in (ROOT / "novel_studio").rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if re.search(r"snapshot|snapshots|AISnapshotStore", text, re.I):
                refs[path.relative_to(ROOT).as_posix()] = [
                    line for line in text.splitlines()
                    if re.search(r"snapshot|snapshots|AISnapshotStore", line, re.I)
                ]
        self.assertEqual(set(refs), {"novel_studio/db/project_database.py"})

    def test_no_view_index_access(self):
        text = (ROOT / "novel_studio" / "ui" / "main_window.py").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"self\.views\[[0-9]+\]", text))


if __name__ == "__main__":
    unittest.main()
