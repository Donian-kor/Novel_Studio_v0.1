import ast
import sqlite3
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

from novel_studio.core.project import ProjectManager
from novel_studio.db.project_database import ProjectDatabase

ROOT = Path(__file__).resolve().parents[1]

class TestV151Architecture(unittest.TestCase):
    def test_physical_database_separation_and_story_hierarchy(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"novel"
            pm=ProjectManager(); pm.create(root=root, title="테스트", genre="선협", mood="진중", total_chapters=50, chapter_chars=5000, tolerance=300, section_size=10, long_story_size=50, sub_story_size=10)
            db=ProjectDatabase(root); db.ensure_chapters(50,5000)
            expected={
                "story":{"meta","schema_meta","plans","contract","section_contents","story_sections","story_subsections","chapter_stories","master_diffs","plot_batches","ideas","search_documents","search_fts"},
                "setting":{"schema_meta","characters","character_states","relationships","world_entities","timeline_events","foreshadowing","major_events","foreshadow_events","search_documents","search_fts"},
                "manuscript":{"schema_meta","chapters","chat_messages","ai_jobs","search_documents","search_fts"},
                "summary":{"schema_meta","chapter_states","continuity_checks","search_documents","search_fts"},
            }
            for name, allowed in expected.items():
                con=sqlite3.connect(root/"db"/f"{name}.db")
                tables={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'")}
                # FTS5 internal shadow tables are expected and stay with their own DB.
                tables={t for t in tables if not t.startswith('search_fts_')} | ({'search_fts'} if 'search_fts' in tables else set())
                self.assertEqual(tables, allowed, name)
                con.close()
            db.save_section(1,50,"생성완료","장기")
            db.save_story_subsection(1,50,1,10,"1~10","세부","생성완료")
            db.save_chapter_story(1,1,50,1,10,"1화","화별","생성완료")
            self.assertEqual(db.story_subsection_for_chapter(5)["title"],"1~10")
            self.assertEqual(db.chapter_story(1)["content"],"화별")
            db.save_chapter_state(1,"","종료 상태","hash","완료")
            self.assertEqual(db.latest_chapter_state(1)["state"],"종료 상태")
            db.close()

    def test_manuscript_is_file_source_of_truth(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"novel"; pm=ProjectManager(); pm.create(root=root, title="테스트", genre="선협", mood="진중", total_chapters=3, chapter_chars=5000, tolerance=300, section_size=10, long_story_size=50, sub_story_size=10)
            pm.save_chapter(2,"실제 원고 본문")
            self.assertEqual(pm.load_chapter(2),"실제 원고 본문")

    def test_legacy_snapshot_and_plot_tables_are_absent_after_open(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"novel"; pm=ProjectManager(); pm.create(root=root, title="테스트", genre="선협", mood="진중", total_chapters=3, chapter_chars=5000, tolerance=300, section_size=10, long_story_size=50, sub_story_size=10)
            # simulate old modular DB by opening once, then inject obsolete tables.
            db=ProjectDatabase(root); db.close()
            con=sqlite3.connect(root/"db"/"story.db")
            con.execute("CREATE TABLE chapter_plans(chapter_number INTEGER PRIMARY KEY,title TEXT,content TEXT,status TEXT,updated_at TEXT)")
            con.execute("CREATE TABLE snapshots(scope TEXT PRIMARY KEY,content TEXT,updated_at TEXT)")
            con.execute("INSERT INTO chapter_plans VALUES(1,'구형','이전 화별 플롯','완료','now')")
            con.execute("INSERT INTO snapshots VALUES('state:1','구형','now')")
            con.commit(); con.close()
            db=ProjectDatabase(root)
            self.assertIsNotNone(db.chapter_story(1))
            self.assertEqual(db.chapter_story(1)["content"],"이전 화별 플롯")
            con=sqlite3.connect(root/"db"/"story.db")
            try:
                names={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                self.assertNotIn('chapter_plans',names); self.assertNotIn('snapshots',names)
            finally:
                con.close()
                db.close()


    def test_single_service_factory_and_new_database_api(self):
        impl = (ROOT / "novel_studio" / "services" / "implementations.py").read_text(encoding="utf-8")
        factory = (ROOT / "novel_studio" / "factories.py").read_text(encoding="utf-8")
        self.assertNotIn("def create_services(", impl)
        self.assertNotIn("from novel_studio.db.database import Database", impl)
        self.assertNotIn("from novel_studio.db.threadsafe_database import ThreadSafeDatabase as Database", impl)
        self.assertNotIn("novel_studio.db.database", impl)
        self.assertTrue((ROOT / "novel_studio" / "db" / "sqlite_storage.py").exists())
        self.assertIn("ProjectDatabase", impl)
        self.assertIn("ServiceFactory", factory)
        self.assertIn("IdeaService", factory)
        main = (ROOT / "novel_studio" / "ui" / "main_window.py").read_text(encoding="utf-8")
        self.assertIn('self.idea_service = bundle["idea_service"]', main)

    def test_setting_timeline_updates_stay_in_setting_db(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"novel"
            pm=ProjectManager(); pm.create(root=root, title="테스트", genre="선협", mood="진중", total_chapters=2, chapter_chars=5000, tolerance=300, section_size=10, long_story_size=50, sub_story_size=10)
            db=ProjectDatabase(root)
            db.save_timeline({"chapter_number": 1, "title": "처음", "description": "기록", "story_date": "1일", "location": "장소", "participants": "주인공"})
            row=db.timeline()[0]
            db.update_timeline(row["id"], {"chapter_number": 2, "title": "수정", "description": "수정 기록", "story_date": "2일", "location": "다른 장소", "participants": "주인공, 조력자"})
            self.assertEqual(db.timeline()[0]["title"], "수정")
            story=sqlite3.connect(root/"db"/"story.db")
            setting=sqlite3.connect(root/"db"/"setting.db")
            self.assertEqual(story.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='timeline_events'").fetchone()[0], 0)
            self.assertEqual(setting.execute("SELECT COUNT(*) FROM timeline_events").fetchone()[0], 1)
            story.close(); setting.close(); db.close()

    def test_old_database_module_is_removed_from_public_api(self):
        self.assertFalse((ROOT / "novel_studio" / "db" / "database.py").exists())
        storage = (ROOT / "novel_studio" / "db" / "sqlite_storage.py").read_text(encoding="utf-8")
        thread = (ROOT / "novel_studio" / "db" / "threadsafe_database.py").read_text(encoding="utf-8")
        self.assertIn("class SQLiteStorage", storage)
        self.assertIn("from novel_studio.db.sqlite_storage import SQLiteStorage", thread)

    def test_project_database_has_no_generic_connection_api(self):
        db_code=(ROOT/"novel_studio"/"db"/"project_database.py").read_text(encoding="utf-8")
        self.assertNotIn("def execute(self, sql", db_code)
        self.assertNotIn("def conn(self)", db_code)
        story=(ROOT/"novel_studio"/"ui"/"views"/"story.py").read_text(encoding="utf-8")
        entities=(ROOT/"novel_studio"/"ui"/"views"/"entities.py").read_text(encoding="utf-8")
        self.assertNotIn("self.w.db.conn", story)
        self.assertNotIn("db.execute(", entities)

    def test_snapshot_references_are_migration_only(self):
        import re
        files = list((ROOT / "novel_studio").rglob("*.py"))
        refs = {}
        for path in files:
            text = path.read_text(encoding="utf-8")
            if re.search(r"snapshot|snapshots|AISnapshotStore", text, re.I):
                refs[path.relative_to(ROOT).as_posix()] = [line for line in text.splitlines() if re.search(r"snapshot|snapshots|AISnapshotStore", line, re.I)]
        allowed = {"novel_studio/db/project_database.py"}
        self.assertTrue(set(refs).issubset(allowed), refs)
        text = (ROOT / "novel_studio" / "db" / "project_database.py").read_text(encoding="utf-8")
        self.assertNotRegex(text, r"CREATE TABLE IF NOT EXISTS\s+snapshots")
        self.assertNotIn("def save_snapshot", text)
        self.assertNotIn("def snapshot", text)

    def test_main_window_does_not_hardcode_view_indexes(self):
        text = (ROOT / "novel_studio" / "ui" / "main_window.py").read_text(encoding="utf-8")
        import re
        self.assertEqual(re.findall(r"self\.views\[[0-9]+\]", text), [])

    def test_project_creation_signature_is_keyword_only(self):
        import inspect
        from novel_studio.core.project import ProjectManager
        params = list(inspect.signature(ProjectManager.create).parameters.values())
        self.assertTrue(all(p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.KEYWORD_ONLY) for p in params[1:]))
        self.assertTrue(all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in params[1:]))

    def test_all_ui_xml_files_parse(self):
        for path in (ROOT/"novel_studio"/"ui"/"forms").glob("*.ui"):
            ET.parse(path)

    def test_python_ast_parses_without_syntax_error(self):
        for path in ROOT.rglob("*.py"):
            if "__pycache__" in path.parts: continue
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

if __name__=="__main__": unittest.main()
