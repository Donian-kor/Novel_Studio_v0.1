"""Novel Studio 1.5 모듈형 프로젝트 DB 접근 계층이다.

역할별로 분리된 4개의 SQLite DB를 사용한다.
- story.db: 기획, 전체 기획, 스토리 계층, 화별 스토리
- setting.db: 인물, 세계관, 세력, 아이템, 복선, 연표
- manuscript.db: 화 메타데이터와 채팅 기록
- summary.db: 연속성 기록과 연속성 검사 결과

공개 API는 점진적인 마이그레이션을 위해 이전 Database 계층과 비슷한 형태를 유지한다.
기존 novel.db 프로젝트는 최초 실행 시 새 저장소로 복사하며 원본 파일은 백업으로 그대로 둔다.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Callable

from novel_studio.db.threadsafe_database import ThreadSafeDatabase


class ProjectDatabase:
    """프로젝트 데이터를 역할별 4개 SQLite DB로 실제 분리한다."""

    DOMAINS = {
        "story": {"get_meta", "set_meta", "get_plan", "save_plan", "get_contract", "save_contract",
                  "section_content", "save_section_content", "sections", "section_for_chapter", "sections_overlapping", "section", "save_section",
                  "story_subsections", "story_subsection", "save_story_subsection", "story_subsection_for_chapter", "chapter_story", "save_chapter_story",
                  "plot_batches", "set_plot_batch", "save_master_diff", "latest_master_diff", "add_idea", "recent_ideas", "use_idea", "arc_bounds"},
        "setting": {"characters", "save_character", "world_entities", "save_world", "foreshadows", "active_foreshadow_count", "save_foreshadow",
                    "delete_character", "delete_world", "delete_foreshadow", "delete_timeline", "delete_major_event", "save_timeline", "save_major_event",
                    "timeline", "update_timeline", "major_events", "chapter_stories_in_range", "characters_relevant", "world_relevant", "foreshadows_relevant", "foreshadow_events", "add_foreshadow_event"},
        "manuscript": {"ensure_chapters", "chapters", "chapter_stats", "chapter_count", "chapter_range", "chapter", "set_chapter_meta", "add_chat", "chat_messages"},
        "summary": {"chapter_state", "latest_chapter_state", "chapter_states", "save_chapter_state", "continuity_for_chapter", "continuity", "add_continuity"},
    }

    def __init__(self, project_root: str | Path):
        self.root = Path(project_root)
        self.db_dir = self.root / "db"
        self._closed = False
        self.db_dir.mkdir(parents=True, exist_ok=True)
        legacy_modular = self._read_legacy_modular_story()
        self._dbs = {
            name: ThreadSafeDatabase(self.db_dir / f"{name}.db", profile=name)
            for name in ("story", "setting", "manuscript", "summary")
        }
        self._migrate_legacy_once()
        self._apply_legacy_modular_story(legacy_modular)
        self._migrate_v150_story()
        self._set_migration_marker()

    @property
    def path(self):
        return self.db_dir

    @property
    def database(self):
        return self

    def _db_for(self, method):
        for domain, names in self.DOMAINS.items():
            if method in names:
                return self._dbs[domain]
        raise AttributeError(f"ProjectDatabase에 라우팅되지 않은 DB 메서드: {method}")

    def __getattr__(self, name):
        if name in {"_dbs", "root", "db_dir"}:
            raise AttributeError(name)
        try:
            return getattr(self._db_for(name), name)
        except AttributeError:
            raise AttributeError(name) from None

    def close(self):
        """모든 프로젝트 DB 연결을 안전하게 닫고, 반복 호출도 허용한다."""
        if self._closed:
            return
        errors = []
        dbs = tuple(self._dbs.values())
        for db in dbs:
            try:
                db.close()
            except Exception as exc:
                errors.append(exc)
        # 닫힌 DB 객체도 ProjectDatabase가 계속 붙잡지 않도록 참조를 정리한다.
        self._dbs.clear()
        self._closed = True
        if errors:
            raise RuntimeError("프로젝트 DB 종료 중 오류가 발생했습니다.") from errors[0]

    def __enter__(self):
        if self._closed:
            raise RuntimeError("이미 닫힌 프로젝트 DB입니다.")
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def chapter_stories_in_range(self, start_chapter: int, end_chapter: int):
        db = self._dbs["story"]
        return db.conn.execute(
            "SELECT * FROM chapter_stories WHERE chapter_number BETWEEN ? AND ? ORDER BY chapter_number",
            (int(start_chapter), int(end_chapter)),
        ).fetchall()

    def search(self, q, limit=50):
        q=(q or "").strip()
        if not q:
            return []
        out=[]
        each=max(1,int(limit))
        for db in self._dbs.values():
            try:
                out.extend(db.search(q, each))
            except Exception:
                continue
        return out[:int(limit)]

    def _read_legacy_modular_story(self):
        """프로필 DB를 열기 전에 v1.5.0 story.db의 구형 데이터를 읽는다."""
        path=self.db_dir/"story.db"
        if not path.exists(): return None
        try:
            con=sqlite3.connect(path); con.row_factory=sqlite3.Row
            tables={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not ({"chapter_plans","snapshots"} & tables):
                con.close(); return None
            data={"sections":[],"chapter_plans":[]}
            if "story_sections" in tables:
                data["sections"]=[dict(r) for r in con.execute("SELECT id,start_chapter,end_chapter,status,content,updated_at FROM story_sections").fetchall()]
            if "chapter_plans" in tables:
                data["chapter_plans"]=[dict(r) for r in con.execute("SELECT chapter_number,title,content,status FROM chapter_plans ORDER BY chapter_number").fetchall()]
            con.close(); return data
        except sqlite3.Error:
            try: con.close()
            except Exception: pass
            return None

    def _apply_legacy_modular_story(self, data):
        if not data: return
        db=self._dbs["story"]
        for r in data.get("sections",[]):
            try:
                db.execute("INSERT OR REPLACE INTO story_sections(id,start_chapter,end_chapter,status,content,updated_at) VALUES(?,?,?,?,?,?)",(r["id"],r["start_chapter"],r["end_chapter"],r.get("status") or "미작성",r.get("content") or "",r.get("updated_at")))
            except Exception:
                continue
        for r in data.get("chapter_plans",[]):
            n=int(r["chapter_number"])
            sec=db.conn.execute("SELECT start_chapter,end_chapter FROM story_sections WHERE start_chapter<=? AND end_chapter>=? LIMIT 1",(n,n)).fetchone()
            ls,le=(int(sec["start_chapter"]),int(sec["end_chapter"])) if sec else (0,0)
            db.save_chapter_story(n,ls,le,0,0,r.get("title") or f"{n}화",r.get("content") or "",r.get("status") or "초안")
        db.execute("DROP TABLE IF EXISTS snapshots")
        db.execute("DROP TABLE IF EXISTS chapter_plans")

    def _set_migration_marker(self):
        self._dbs["story"].set_meta("modular_migration_v1_5", "done")

    def _migrate_legacy_once(self):
        if self._dbs["story"].get_meta("legacy_migration_v1_5_done", "") == "done":
            return
        legacy=self.root/"novel.db"
        if not legacy.exists():
            return
        src=sqlite3.connect(legacy); src.row_factory=sqlite3.Row
        try:
            # v1.5.1 목표 구조에 맞는 단순 테이블을 정의한다.
            groups={
                "story":["meta","schema_meta","plans","contract","section_contents","master_diffs","plot_batches","ideas"],
                "setting":["characters","character_states","relationships","world_entities","timeline_events","foreshadowing","major_events","foreshadow_events"],
                "manuscript":["chapters","chat_messages","ai_jobs"],
                "summary":["chapter_states","continuity_checks"],
            }
            for domain,names in groups.items():
                target=self._dbs[domain]
                for table in names:
                    cols=[r[1] for r in src.execute(f'PRAGMA table_info("{table}")').fetchall()]
                    if not cols: continue
                    rows=src.execute(f'SELECT * FROM "{table}"').fetchall()
                    if not rows: continue
                    placeholders=','.join('?' for _ in cols); col_sql=','.join(f'"{c}"' for c in cols)
                    try:
                        target.conn.executemany(f'INSERT OR REPLACE INTO "{table}" ({col_sql}) VALUES ({placeholders})', [tuple(r[c] for c in cols) for r in rows])
                        target.conn.commit()
                    except sqlite3.Error:
                        continue
            # 구형 story_sections가 존재할 때만 이관한다.
            legacy_tables={r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            target=self._dbs['story']
            if "story_sections" in legacy_tables:
                rows=src.execute('SELECT id,start_chapter,end_chapter,status,content,updated_at FROM story_sections').fetchall()
                for r in rows:
                    target.execute('INSERT OR REPLACE INTO story_sections(id,start_chapter,end_chapter,status,content,updated_at) VALUES(?,?,?,?,?,?)', tuple(r))
            # 구형 chapter_plans가 존재할 때만 화별 스토리로 변환한다.
            if "chapter_plans" in legacy_tables:
                rows=src.execute('SELECT chapter_number,title,content,status FROM chapter_plans').fetchall()
                for r in rows:
                    n=int(r['chapter_number'])
                    sec=target.conn.execute('SELECT start_chapter,end_chapter FROM story_sections WHERE start_chapter<=? AND end_chapter>=? LIMIT 1',(n,n)).fetchone()
                    ls,le=(int(sec['start_chapter']),int(sec['end_chapter'])) if sec else (0,0)
                    target.save_chapter_story(n,ls,le,0,0,r['title'] or f'{n}화',r['content'] or '',r['status'] or '초안')
            self._dbs['story'].set_meta('legacy_migration_v1_5_done','done')
        finally:
            src.close()

    def _migrate_v150_story(self):
        """v1.5.0의 구형 chapter_plans/snapshot 구조를 v1.5.1로 정리."""
        marker=self._dbs["story"].get_meta("story_model_v151", "")
        if marker == "done":
            # 기존 DB에 남은 불필요한 테이블/열이 있어도 아래 정리만 다시 시도한다.
            pass
        legacy=self.root/"novel.db"
        # 이미 분리된 v1.5.0 DB에서 chapter_plans를 변환할 수 있는 경우에만 수행한다.
        old=self._dbs["story"]
        try:
            if old.table_exists("chapter_plans"):
                rows=old.conn.execute("SELECT chapter_number,title,content,status FROM chapter_plans ORDER BY chapter_number").fetchall()
                for r in rows:
                    n=int(r["chapter_number"])
                    sec=old.conn.execute("SELECT start_chapter,end_chapter FROM story_sections WHERE start_chapter<=? AND end_chapter>=? LIMIT 1",(n,n)).fetchone()
                    sub=old.conn.execute("SELECT start_chapter,end_chapter,parent_start,parent_end FROM story_subsections WHERE start_chapter<=? AND end_chapter>=? LIMIT 1",(n,n)).fetchone()
                    ls,le=(int(sec["start_chapter"]),int(sec["end_chapter"])) if sec else (0,0)
                    ss,se=(int(sub["start_chapter"]),int(sub["end_chapter"])) if sub else (0,0)
                    old.save_chapter_story(n,ls,le,ss,se,r["title"] or f"{n}화",r["content"] or "",r["status"] or "초안")
                old.execute('DROP TABLE IF EXISTS chapter_plans')
            old.execute('DROP TABLE IF EXISTS snapshots')
            if old.table_exists("story_sections"):
                cols=[r[1] for r in old.conn.execute("PRAGMA table_info(story_sections)").fetchall()]
                if "snapshot" in cols:
                    old.conn.execute("ALTER TABLE story_sections RENAME TO story_sections_v150")
                    old.conn.execute("CREATE TABLE story_sections(id INTEGER PRIMARY KEY AUTOINCREMENT,start_chapter INTEGER NOT NULL,end_chapter INTEGER NOT NULL,status TEXT DEFAULT '미작성',content TEXT DEFAULT '',updated_at TEXT,UNIQUE(start_chapter,end_chapter))")
                    old.conn.execute("INSERT INTO story_sections(id,start_chapter,end_chapter,status,content,updated_at) SELECT id,start_chapter,end_chapter,status,content,updated_at FROM story_sections_v150")
                    old.conn.execute("DROP TABLE story_sections_v150")
                    old.conn.execute("CREATE INDEX IF NOT EXISTS idx_story_sections_start_end ON story_sections(start_chapter,end_chapter)")
                    old.conn.commit()
        except Exception:
            pass
        self._dbs["story"].set_meta("story_model_v151","done")
