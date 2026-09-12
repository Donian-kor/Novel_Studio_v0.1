from __future__ import annotations
import sqlite3
from pathlib import Path
from novel_studio.core.helpers import now


class Database:
    """작품의 모든 구조화된 정보를 SQLite로 관리한다."""
    def __init__(self, path: Path):
        self.path = path
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.init_schema()

    def close(self) -> None:
        self.conn.close()

    def init_schema(self) -> None:
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS chapters(
            number INTEGER PRIMARY KEY, title TEXT DEFAULT '', status TEXT DEFAULT '미작성',
            char_count INTEGER DEFAULT 0, char_count_spaces INTEGER DEFAULT 0,
            target_chars INTEGER DEFAULT 5000, updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS chapter_plans(
            chapter_number INTEGER PRIMARY KEY, title TEXT DEFAULT '', content TEXT DEFAULT '', status TEXT DEFAULT '초안', updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS story_sections(
            id INTEGER PRIMARY KEY AUTOINCREMENT, start_chapter INTEGER NOT NULL, end_chapter INTEGER NOT NULL,
            status TEXT DEFAULT '미작성', objective TEXT DEFAULT '', content TEXT DEFAULT '',
            snapshot TEXT DEFAULT '', updated_at TEXT, UNIQUE(start_chapter,end_chapter)
        );
        CREATE TABLE IF NOT EXISTS core_contract(id INTEGER PRIMARY KEY CHECK(id=1), content TEXT DEFAULT '', locked INTEGER DEFAULT 0, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS characters(
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, role TEXT DEFAULT '', profile TEXT DEFAULT '',
            personality TEXT DEFAULT '', speech_style TEXT DEFAULT '', goal TEXT DEFAULT '', secret TEXT DEFAULT '',
            arc TEXT DEFAULT '', status TEXT DEFAULT '초안', updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS character_states(
            id INTEGER PRIMARY KEY AUTOINCREMENT, character_id INTEGER NOT NULL, chapter_number INTEGER NOT NULL,
            location TEXT DEFAULT '', cultivation TEXT DEFAULT '', condition TEXT DEFAULT '', injuries TEXT DEFAULT '',
            possessions TEXT DEFAULT '', emotions TEXT DEFAULT '', knows TEXT DEFAULT '', does_not_know TEXT DEFAULT '', notes TEXT DEFAULT '', updated_at TEXT,
            UNIQUE(character_id,chapter_number), FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS relationships(
            id INTEGER PRIMARY KEY AUTOINCREMENT, from_character TEXT, to_character TEXT, relation TEXT, start_chapter INTEGER,
            current_state TEXT DEFAULT '', history TEXT DEFAULT '', updated_at TEXT,
            UNIQUE(from_character,to_character,relation)
        );
        CREATE TABLE IF NOT EXISTS world_entities(
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, category TEXT DEFAULT '', description TEXT DEFAULT '',
            rules TEXT DEFAULT '', status TEXT DEFAULT '초안', updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS timeline_events(
            id INTEGER PRIMARY KEY AUTOINCREMENT, chapter_number INTEGER, story_date TEXT DEFAULT '', title TEXT DEFAULT '',
            description TEXT DEFAULT '', location TEXT DEFAULT '', participants TEXT DEFAULT '', updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS foreshadowing(
            id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, title TEXT DEFAULT '', first_chapter INTEGER,
            latest_chapter INTEGER, reveal_chapter INTEGER, status TEXT DEFAULT '활성', public_info TEXT DEFAULT '',
            author_truth TEXT DEFAULT '', related_characters TEXT DEFAULT '', notes TEXT DEFAULT '', updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS major_events(
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT UNIQUE NOT NULL, start_chapter INTEGER, end_chapter INTEGER,
            description TEXT DEFAULT '', consequence TEXT DEFAULT '', status TEXT DEFAULT '계획', updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS summaries(
            chapter_number INTEGER PRIMARY KEY, summary TEXT DEFAULT '', state_snapshot TEXT DEFAULT '', updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS snapshots(
            scope TEXT PRIMARY KEY, content TEXT DEFAULT '', updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS continuity_checks(
            id INTEGER PRIMARY KEY AUTOINCREMENT, chapter_number INTEGER, severity TEXT, category TEXT,
            message TEXT, evidence TEXT DEFAULT '', status TEXT DEFAULT '미해결', created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS ai_jobs(
            id INTEGER PRIMARY KEY AUTOINCREMENT, job_type TEXT, target TEXT, status TEXT, model TEXT DEFAULT '',
            prompt_chars INTEGER DEFAULT 0, output_chars INTEGER DEFAULT 0, started_at TEXT, completed_at TEXT, error TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS chat_messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT, chapter_number INTEGER, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS ideas(
            id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, created_at TEXT, used INTEGER DEFAULT 0
        );
        """)
        self._migrate_legacy_schema()
        self.conn.commit()

    def _migrate_legacy_schema(self) -> None:
        """v0.x/v1.0 프로젝트에서 새 컬럼이 필요한 경우 안전하게 추가한다."""
        migrations = {
            "chapters": [
                ("char_count", "INTEGER DEFAULT 0"),
                ("char_count_spaces", "INTEGER DEFAULT 0"),
            ],
            "chapter_plans": [("status", "TEXT DEFAULT '초안'")],
            "story_sections": [("snapshot", "TEXT DEFAULT ''")],
        }
        for table, columns in migrations.items():
            existing = {row[1] for row in self.conn.execute(f"PRAGMA table_info({table})").fetchall()}
            for name, definition in columns:
                if name not in existing:
                    self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
        # Very old versions used word_count. Preserve it by copying values when possible.
        cols = {row[1] for row in self.conn.execute("PRAGMA table_info(chapters)").fetchall()}
        if "word_count" in cols and "char_count" in cols:
            self.conn.execute("UPDATE chapters SET char_count=word_count WHERE COALESCE(char_count,0)=0 AND COALESCE(word_count,0)>0")

    def execute(self, sql: str, params=()):
        cur = self.conn.execute(sql, params); self.conn.commit(); return cur

    def set_meta(self, key: str, value: str) -> None:
        self.execute("INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

    def get_meta(self, key: str, default: str = "") -> str:
        row = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return str(row["value"]) if row else default

    def chapters(self): return self.conn.execute("SELECT * FROM chapters ORDER BY number").fetchall()
    def chapter(self, number: int): return self.conn.execute("SELECT * FROM chapters WHERE number=?", (number,)).fetchone()

    def ensure_chapters(self, total: int, target: int) -> None:
        for n in range(1, total + 1):
            self.conn.execute("INSERT OR IGNORE INTO chapters(number,title,status,target_chars,updated_at) VALUES(?,?,?,?,?)", (n, f"{n}화", "미작성", target, now()))
        self.conn.commit()

    def set_chapter_meta(self, number: int, title: str, status: str, count: int, count_spaces: int, target: int) -> None:
        self.execute("""INSERT INTO chapters(number,title,status,char_count,char_count_spaces,target_chars,updated_at)
        VALUES(?,?,?,?,?,?,?) ON CONFLICT(number) DO UPDATE SET title=excluded.title,status=excluded.status,
        char_count=excluded.char_count,char_count_spaces=excluded.char_count_spaces,target_chars=excluded.target_chars,updated_at=excluded.updated_at""",
        (number,title,status,count,count_spaces,target,now()))

    def chapter_plans(self): return self.conn.execute("SELECT * FROM chapter_plans ORDER BY chapter_number").fetchall()
    def chapter_plan(self, number: int): return self.conn.execute("SELECT * FROM chapter_plans WHERE chapter_number=?", (number,)).fetchone()
    def set_chapter_plan(self, number: int, title: str, content: str, status: str = "초안"):
        self.execute("INSERT INTO chapter_plans(chapter_number,title,content,status,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(chapter_number) DO UPDATE SET title=excluded.title,content=excluded.content,status=excluded.status,updated_at=excluded.updated_at", (number,title,content,status,now()))

    def sections(self): return self.conn.execute("SELECT * FROM story_sections ORDER BY start_chapter").fetchall()
    def section(self, start: int, end: int): return self.conn.execute("SELECT * FROM story_sections WHERE start_chapter=? AND end_chapter=?", (start,end)).fetchone()
    def upsert_section(self, start: int, end: int, status: str, objective: str, content: str, snapshot: str = ""):
        self.execute("""INSERT INTO story_sections(start_chapter,end_chapter,status,objective,content,snapshot,updated_at) VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(start_chapter,end_chapter) DO UPDATE SET status=excluded.status,objective=excluded.objective,content=excluded.content,snapshot=excluded.snapshot,updated_at=excluded.updated_at""", (start,end,status,objective,content,snapshot,now()))

    def contract(self): return self.conn.execute("SELECT * FROM core_contract WHERE id=1").fetchone()
    def save_contract(self, content: str, locked: bool):
        self.execute("INSERT INTO core_contract(id,content,locked,updated_at) VALUES(1,?,?,?) ON CONFLICT(id) DO UPDATE SET content=excluded.content,locked=excluded.locked,updated_at=excluded.updated_at", (content,int(locked),now()))

    def characters(self): return self.conn.execute("SELECT * FROM characters ORDER BY id").fetchall()
    def character(self, name: str): return self.conn.execute("SELECT * FROM characters WHERE name=?", (name,)).fetchone()
    def save_character(self, data: dict):
        self.execute("""INSERT INTO characters(name,role,profile,personality,speech_style,goal,secret,arc,status,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET role=excluded.role,profile=excluded.profile,personality=excluded.personality,
        speech_style=excluded.speech_style,goal=excluded.goal,secret=excluded.secret,arc=excluded.arc,status=excluded.status,updated_at=excluded.updated_at""",
        (data.get("name", ""),data.get("role", ""),data.get("profile", ""),data.get("personality", ""),data.get("speech_style", ""),data.get("goal", ""),data.get("secret", ""),data.get("arc", ""),data.get("status", "초안"),now()))

    def save_character_state(self, data: dict):
        c = self.character(data.get("name", ""));
        if not c: return
        self.execute("""INSERT INTO character_states(character_id,chapter_number,location,cultivation,condition,injuries,possessions,emotions,knows,does_not_know,notes,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(character_id,chapter_number) DO UPDATE SET location=excluded.location,cultivation=excluded.cultivation,
        condition=excluded.condition,injuries=excluded.injuries,possessions=excluded.possessions,emotions=excluded.emotions,knows=excluded.knows,does_not_know=excluded.does_not_know,notes=excluded.notes,updated_at=excluded.updated_at""",
        (c["id"],data.get("chapter_number",0),data.get("location",""),data.get("cultivation",""),data.get("condition",""),data.get("injuries",""),data.get("possessions",""),data.get("emotions",""),data.get("knows",""),data.get("does_not_know",""),data.get("notes",""),now()))

    def latest_character_state(self, character_id: int, before_or_at: int | None = None):
        if before_or_at is None:
            return self.conn.execute("SELECT * FROM character_states WHERE character_id=? ORDER BY chapter_number DESC LIMIT 1", (character_id,)).fetchone()
        return self.conn.execute("SELECT * FROM character_states WHERE character_id=? AND chapter_number<=? ORDER BY chapter_number DESC LIMIT 1", (character_id,before_or_at)).fetchone()

    def relationships(self): return self.conn.execute("SELECT * FROM relationships ORDER BY from_character,to_character").fetchall()
    def save_relationship(self, data: dict):
        self.execute("""INSERT INTO relationships(from_character,to_character,relation,start_chapter,current_state,history,updated_at) VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(from_character,to_character,relation) DO UPDATE SET start_chapter=excluded.start_chapter,current_state=excluded.current_state,history=excluded.history,updated_at=excluded.updated_at""",
        (data.get("from_character",""),data.get("to_character",""),data.get("relation",""),data.get("start_chapter"),data.get("current_state",""),data.get("history",""),now()))

    def worlds(self): return self.conn.execute("SELECT * FROM world_entities ORDER BY category,name").fetchall()
    def save_world(self, data: dict):
        self.execute("INSERT INTO world_entities(name,category,description,rules,status,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET category=excluded.category,description=excluded.description,rules=excluded.rules,status=excluded.status,updated_at=excluded.updated_at", (data.get("name",""),data.get("category",""),data.get("description",""),data.get("rules",""),data.get("status","초안"),now()))

    def timelines(self): return self.conn.execute("SELECT * FROM timeline_events ORDER BY COALESCE(chapter_number,999999),id").fetchall()
    def save_timeline(self, data: dict):
        self.execute("INSERT INTO timeline_events(chapter_number,story_date,title,description,location,participants,updated_at) VALUES(?,?,?,?,?,?,?)", (data.get("chapter_number"),data.get("story_date",""),data.get("title",""),data.get("description",""),data.get("location",""),data.get("participants",""),now()))

    def foreshadows(self): return self.conn.execute("SELECT * FROM foreshadowing ORDER BY id").fetchall()
    def save_foreshadow(self, data: dict):
        self.execute("""INSERT INTO foreshadowing(code,title,first_chapter,latest_chapter,reveal_chapter,status,public_info,author_truth,related_characters,notes,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(code) DO UPDATE SET title=excluded.title,first_chapter=excluded.first_chapter,latest_chapter=excluded.latest_chapter,
        reveal_chapter=excluded.reveal_chapter,status=excluded.status,public_info=excluded.public_info,author_truth=excluded.author_truth,related_characters=excluded.related_characters,notes=excluded.notes,updated_at=excluded.updated_at""",
        (data.get("code",""),data.get("title",""),data.get("first_chapter"),data.get("latest_chapter"),data.get("reveal_chapter"),data.get("status","활성"),data.get("public_info",""),data.get("author_truth",""),data.get("related_characters",""),data.get("notes",""),now()))

    def major_events(self): return self.conn.execute("SELECT * FROM major_events ORDER BY COALESCE(start_chapter,999999),id").fetchall()
    def save_major_event(self, data: dict): self.execute("INSERT INTO major_events(title,start_chapter,end_chapter,description,consequence,status,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(title) DO UPDATE SET start_chapter=excluded.start_chapter,end_chapter=excluded.end_chapter,description=excluded.description,consequence=excluded.consequence,status=excluded.status,updated_at=excluded.updated_at", (data.get("title",""),data.get("start_chapter"),data.get("end_chapter"),data.get("description",""),data.get("consequence",""),data.get("status","계획"),now()))

    def summary(self, number: int): return self.conn.execute("SELECT * FROM summaries WHERE chapter_number=?", (number,)).fetchone()
    def summaries(self): return self.conn.execute("SELECT * FROM summaries ORDER BY chapter_number").fetchall()
    def save_summary(self, number: int, summary: str, state_snapshot: str): self.execute("INSERT INTO summaries(chapter_number,summary,state_snapshot,updated_at) VALUES(?,?,?,?) ON CONFLICT(chapter_number) DO UPDATE SET summary=excluded.summary,state_snapshot=excluded.state_snapshot,updated_at=excluded.updated_at", (number,summary,state_snapshot,now()))

    def snapshot(self, scope: str): return self.conn.execute("SELECT * FROM snapshots WHERE scope=?", (scope,)).fetchone()
    def save_snapshot(self, scope: str, content: str): self.execute("INSERT INTO snapshots(scope,content,updated_at) VALUES(?,?,?) ON CONFLICT(scope) DO UPDATE SET content=excluded.content,updated_at=excluded.updated_at", (scope,content,now()))

    def add_idea(self, content: str): self.execute("INSERT INTO ideas(content,created_at,used) VALUES(?,?,0)", (content,now()))
    def recent_ideas(self, limit: int = 10): return self.conn.execute("SELECT content FROM ideas ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    def use_idea(self, content: str): self.execute("UPDATE ideas SET used=0"); self.execute("UPDATE ideas SET used=1 WHERE content=?", (content,))

    def add_chat(self, role: str, content: str, chapter_number: int | None): self.execute("INSERT INTO chat_messages(role,content,chapter_number,created_at) VALUES(?,?,?,?)", (role,content,chapter_number,now()))
    def chat_messages(self, chapter_number: int | None = None):
        if chapter_number is None: return self.conn.execute("SELECT * FROM chat_messages ORDER BY id").fetchall()
        return self.conn.execute("SELECT * FROM chat_messages WHERE chapter_number=? ORDER BY id", (chapter_number,)).fetchall()

    def start_job(self, job_type: str, target: str, model: str) -> int:
        cur=self.conn.execute("INSERT INTO ai_jobs(job_type,target,status,model,started_at) VALUES(?,?,?,?,?)", (job_type,target,"실행중",model,now())); self.conn.commit(); return int(cur.lastrowid)
    def finish_job(self, job_id: int, status: str, prompt_chars: int, output_chars: int, error: str = ""):
        self.execute("UPDATE ai_jobs SET status=?,prompt_chars=?,output_chars=?,completed_at=?,error=? WHERE id=?", (status,prompt_chars,output_chars,now(),error,job_id))

    def add_continuity(self, chapter: int, severity: str, category: str, message: str, evidence: str = ""):
        self.execute("INSERT INTO continuity_checks(chapter_number,severity,category,message,evidence,created_at) VALUES(?,?,?,?,?,?)", (chapter,severity,category,message,evidence,now()))
    def continuity(self, chapter: int | None = None):
        if chapter is None: return self.conn.execute("SELECT * FROM continuity_checks ORDER BY id DESC").fetchall()
        return self.conn.execute("SELECT * FROM continuity_checks WHERE chapter_number=? ORDER BY id DESC", (chapter,)).fetchall()
