"""
스레드 안전한 데이터베이스 래퍼
- 스레드별 읽기 전용 커넥션 (threading.local)
- 쓰기 작업용 전용 커넥션 + RLock
- database is locked 시 지수 백오프 재시도
"""
import sqlite3
import threading
import time
import random
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Any, Iterator
from datetime import datetime

from novel_studio.db.database import Database as BaseDatabase, CURRENT_SCHEMA_VERSION, MIGRATIONS, now

logger = logging.getLogger(__name__)


class ThreadSafeDatabase:
    """
    스레드 안전한 데이터베이스 래퍼
    
    특징:
    - 읽기 작업: 스레드별 독립 커넥션 (threading.local)
    - 쓰기 작업: 전용 커넥션 + RLock으로 직렬화
    - database is locked 시 지수 백오프 재시도
    - 기존 Database API와 호환
    """
    
    def __init__(self, path: str, max_retries: int = 5, base_delay: float = 0.1, max_delay: float = 5.0):
        self.path = str(path)
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        
        # 쓰기 작업용 락
        self._write_lock = threading.RLock()
        
        # 스레드별 읽기 전용 커넥션 저장소
        self._local = threading.local()
        
        # 메인 커넥션 (초기화용)
        self._main_conn = None
        self._path = path

        # 래퍼에 직접 정의되지 않은 나머지 Database API를 위임할 기본 Database 객체
        self._base = BaseDatabase(Path(path))

        # 초기화
        self._init_main_connection()

    def __getattr__(self, name: str) -> Any:
        """래퍼에 정의되지 않은 속성/메서드를 기본 Database 객체에 위임한다.

        예: ensure_chapters, chapter, save_character 등은 여기에 정의되어
        있지 않으므로 기본 Database(self._base)의 동일한 메서드를 대신 호출한다.
        """
        # 무한 재귀 방지: _base 자체나 듀얼 언더스코어 이름은 위임하지 않는다.
        if name == '_base' or (name.startswith('__') and name.endswith('__')):
            raise AttributeError(name)
        try:
            base = object.__getattribute__(self, '_base')
        except AttributeError:
            # _base가 아직 준비되지 않은 초기화 중 접근은 일반 AttributeError로 처리
            raise AttributeError(
                f"{type(self).__name__} 객체에 '{name}' 속성이 없습니다"
            ) from None
        return getattr(base, name)

    def _init_main_connection(self):
        """메인 커넥션 초기화 (스키마 생성용)"""
        self._main_conn = sqlite3.connect(self.path, check_same_thread=False)
        self._main_conn.row_factory = sqlite3.Row
        self._main_conn.execute("PRAGMA foreign_keys=ON")
        self._main_conn.execute("PRAGMA journal_mode=WAL")
        self._main_conn.execute("PRAGMA busy_timeout=5000")  # 5초 busy timeout
        self._create_schema()
        self._migrate_schema()
        self._ensure_search_index()
    
    def _create_schema(self):
        """스키마 생성 (기존 Database._schema와 동일)"""
        self._main_conn.executescript("""
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS schema_meta(version INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS chapters(number INTEGER PRIMARY KEY,title TEXT DEFAULT '',status TEXT DEFAULT '미작성',char_count INTEGER DEFAULT 0,char_count_spaces INTEGER DEFAULT 0,target_chars INTEGER DEFAULT 5000,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS chapter_plans(chapter_number INTEGER PRIMARY KEY,title TEXT DEFAULT '',content TEXT DEFAULT '',status TEXT DEFAULT '초안',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS story_sections(id INTEGER PRIMARY KEY AUTOINCREMENT,start_chapter INTEGER NOT NULL,end_chapter INTEGER NOT NULL,status TEXT DEFAULT '미작성',content TEXT DEFAULT '',snapshot TEXT DEFAULT '',updated_at TEXT,UNIQUE(start_chapter,end_chapter));
        CREATE TABLE IF NOT EXISTS characters(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,role TEXT DEFAULT '',profile TEXT DEFAULT '',personality TEXT DEFAULT '',speech_style TEXT DEFAULT '',goal TEXT DEFAULT '',secret TEXT DEFAULT '',arc TEXT DEFAULT '',status TEXT DEFAULT '초안',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS character_states(id INTEGER PRIMARY KEY AUTOINCREMENT,character_id INTEGER NOT NULL,chapter_number INTEGER NOT NULL,location TEXT DEFAULT '',cultivation TEXT DEFAULT '',condition TEXT DEFAULT '',injuries TEXT DEFAULT '',possessions TEXT DEFAULT '',emotions TEXT DEFAULT '',knows TEXT DEFAULT '',does_not_know TEXT DEFAULT '',notes TEXT DEFAULT '',updated_at TEXT,UNIQUE(character_id,chapter_number),FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS relationships(id INTEGER PRIMARY KEY AUTOINCREMENT,from_character TEXT,to_character TEXT,relation TEXT,current_state TEXT DEFAULT '',history TEXT DEFAULT '',start_chapter INTEGER,updated_at TEXT,UNIQUE(from_character,to_character,relation));
        CREATE TABLE IF NOT EXISTS world_entities(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,category TEXT DEFAULT '',description TEXT DEFAULT '',rules TEXT DEFAULT '',status TEXT DEFAULT '초안',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS timeline_events(id INTEGER PRIMARY KEY AUTOINCREMENT,chapter_number INTEGER,story_date TEXT DEFAULT '',title TEXT DEFAULT '',description TEXT DEFAULT '',location TEXT DEFAULT '',participants TEXT DEFAULT '',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS foreshadowing(id INTEGER PRIMARY KEY AUTOINCREMENT,code TEXT UNIQUE NOT NULL,title TEXT DEFAULT '',first_chapter INTEGER,latest_chapter INTEGER,reveal_chapter INTEGER,status TEXT DEFAULT '활성',public_info TEXT DEFAULT '',author_truth TEXT DEFAULT '',related_characters TEXT DEFAULT '',notes TEXT DEFAULT '',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS major_events(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT UNIQUE NOT NULL,start_chapter INTEGER,end_chapter INTEGER,description TEXT DEFAULT '',consequence TEXT DEFAULT '',status TEXT DEFAULT '계획',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS summaries(chapter_number INTEGER PRIMARY KEY,summary TEXT DEFAULT '',state_snapshot TEXT DEFAULT '',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS chapter_states(chapter_number INTEGER PRIMARY KEY,summary TEXT DEFAULT '',state TEXT DEFAULT '',source_hash TEXT DEFAULT '',status TEXT DEFAULT '갱신완료',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS section_memories(start_chapter INTEGER NOT NULL,end_chapter INTEGER NOT NULL,content TEXT DEFAULT '',source_hash TEXT DEFAULT '',status TEXT DEFAULT '갱신완료',updated_at TEXT,PRIMARY KEY(start_chapter,end_chapter));
        CREATE TABLE IF NOT EXISTS arc_memories(arc_number INTEGER PRIMARY KEY, start_chapter INTEGER NOT NULL,end_chapter INTEGER NOT NULL,content TEXT DEFAULT '',source_hash TEXT DEFAULT '',status TEXT DEFAULT '갱신완료',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS snapshots(scope TEXT PRIMARY KEY,content TEXT DEFAULT '',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS continuity_checks(id INTEGER PRIMARY KEY AUTOINCREMENT,chapter_number INTEGER,severity TEXT,category TEXT,message TEXT,evidence TEXT DEFAULT '',status TEXT DEFAULT '미해결',created_at TEXT);
        CREATE TABLE IF NOT EXISTS entity_state_ledger(id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,entity_key TEXT NOT NULL,chapter_number INTEGER NOT NULL,state TEXT DEFAULT '',source_hash TEXT DEFAULT '',updated_at TEXT,UNIQUE(kind,entity_key,chapter_number));
        CREATE TABLE IF NOT EXISTS foreshadow_events(id INTEGER PRIMARY KEY AUTOINCREMENT,foreshadow_id INTEGER NOT NULL,chapter_number INTEGER NOT NULL,event_type TEXT NOT NULL,description TEXT DEFAULT '',before_state TEXT DEFAULT '',after_state TEXT DEFAULT '',created_at TEXT,UNIQUE(foreshadow_id,chapter_number,event_type),FOREIGN KEY(foreshadow_id) REFERENCES foreshadowing(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS master_diffs(id INTEGER PRIMARY KEY AUTOINCREMENT,category TEXT NOT NULL,payload TEXT NOT NULL,status TEXT DEFAULT '제안',created_at TEXT,applied_at TEXT);
        CREATE TABLE IF NOT EXISTS plot_batches(id INTEGER PRIMARY KEY AUTOINCREMENT,start_chapter INTEGER NOT NULL,end_chapter INTEGER NOT NULL,status TEXT DEFAULT '대기',updated_at TEXT,UNIQUE(start_chapter,end_chapter));
        CREATE TABLE IF NOT EXISTS search_documents(doc_id INTEGER PRIMARY KEY AUTOINCREMENT,category TEXT NOT NULL,ref_key TEXT NOT NULL,content TEXT DEFAULT '',updated_at TEXT,UNIQUE(category,ref_key));
        CREATE VIRTUAL TABLE IF NOT EXISTS search_fts USING fts5(category,ref_key,content,content='search_documents',content_rowid='doc_id');
        CREATE TABLE IF NOT EXISTS ai_jobs(id INTEGER PRIMARY KEY AUTOINCREMENT,job_type TEXT,target TEXT,status TEXT,provider TEXT DEFAULT '',model TEXT DEFAULT '',prompt_chars INTEGER DEFAULT 0,output_chars INTEGER DEFAULT 0,started_at TEXT,completed_at TEXT,error TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS chat_messages(id INTEGER PRIMARY KEY AUTOINCREMENT,role TEXT,content TEXT,chapter_number INTEGER,created_at TEXT);
        CREATE TABLE IF NOT EXISTS ideas(id INTEGER PRIMARY KEY AUTOINCREMENT,content TEXT,created_at TEXT,used INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS plans(id INTEGER PRIMARY KEY CHECK(id=1),content TEXT DEFAULT '',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS contract(id INTEGER PRIMARY KEY CHECK(id=1),content TEXT DEFAULT '',locked INTEGER DEFAULT 0,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS section_contents(section TEXT PRIMARY KEY,content TEXT DEFAULT '',status TEXT DEFAULT '초안',updated_at TEXT);
        CREATE INDEX IF NOT EXISTS idx_chapters_status ON chapters(status);
        CREATE INDEX IF NOT EXISTS idx_chapters_updated_at ON chapters(updated_at);
        CREATE INDEX IF NOT EXISTS idx_chapter_plans_status ON chapter_plans(status);
        CREATE INDEX IF NOT EXISTS idx_story_sections_start_end ON story_sections(start_chapter,end_chapter);
        CREATE INDEX IF NOT EXISTS idx_character_states_chapter ON character_states(chapter_number);
        CREATE INDEX IF NOT EXISTS idx_character_states_character_chapter ON character_states(character_id,chapter_number);
        CREATE INDEX IF NOT EXISTS idx_timeline_chapter ON timeline_events(chapter_number);
        CREATE INDEX IF NOT EXISTS idx_foreshadow_status ON foreshadowing(status);
        CREATE INDEX IF NOT EXISTS idx_foreshadow_first ON foreshadowing(first_chapter);
        CREATE INDEX IF NOT EXISTS idx_foreshadow_latest ON foreshadowing(latest_chapter);
        CREATE INDEX IF NOT EXISTS idx_major_events_start ON major_events(start_chapter);
        CREATE INDEX IF NOT EXISTS idx_summaries_updated_at ON summaries(updated_at);
        CREATE INDEX IF NOT EXISTS idx_chapter_states_updated_at ON chapter_states(updated_at);
        CREATE INDEX IF NOT EXISTS idx_section_memories_start_end ON section_memories(start_chapter,end_chapter);
        CREATE INDEX IF NOT EXISTS idx_arc_memories_start_end ON arc_memories(start_chapter,end_chapter);
        CREATE INDEX IF NOT EXISTS idx_continuity_chapter ON continuity_checks(chapter_number);
        CREATE INDEX IF NOT EXISTS idx_chat_chapter ON chat_messages(chapter_number);
        CREATE INDEX IF NOT EXISTS idx_entity_state_kind_key_chapter ON entity_state_ledger(kind,entity_key,chapter_number);
        CREATE INDEX IF NOT EXISTS idx_entity_state_chapter ON entity_state_ledger(chapter_number);
        CREATE INDEX IF NOT EXISTS idx_foreshadow_events_chapter ON foreshadow_events(chapter_number);
        CREATE INDEX IF NOT EXISTS idx_foreshadow_events_fk ON foreshadow_events(foreshadow_id);
        CREATE INDEX IF NOT EXISTS idx_master_diffs_status ON master_diffs(status);
        CREATE INDEX IF NOT EXISTS idx_plot_batches_start ON plot_batches(start_chapter);
        """)
        self._main_conn.commit()
    
    def _get_read_connection(self):
        """스레드별 읽기 전용 커넥션 반환"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            conn = sqlite3.connect(self.path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("PRAGMA read_uncommitted=TRUE")  # 읽기 성능 향상
            self._local.conn = conn
        return self._local.conn
    
    def _get_write_connection(self):
        """쓰기용 메인 커넥션 반환"""
        return self._main_conn
    
    @contextmanager
    def _write_transaction(self) -> Iterator[sqlite3.Connection]:
        """쓰기 트랜잭션 컨텍스트 (락 + 재시도)"""
        for attempt in range(5):
            try:
                with self._write_lock:
                    conn = self._get_write_connection()
                    yield conn
                    conn.commit()
                    return
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() or "busy" in str(e).lower():
                    delay = min(0.1 * (2 ** attempt), 2.0) + random.uniform(0, 0.1)
                    logger.warning(f"DB locked, retrying in {delay:.2f}s (attempt {attempt+1}/5)")
                    time.sleep(delay)
                else:
                    raise
        raise sqlite3.OperationalError("Database locked after max retries")
    
    def _execute_with_retry(self, sql: str, args: tuple = (), write: bool = True) -> sqlite3.Cursor:
        """재시도 로직이 포함된 실행 메서드"""
        last_error = None
        for attempt in range(3):
            try:
                if write:
                    with self._write_transaction() as conn:
                        return conn.execute(sql, args)
                else:
                    conn = self._get_read_connection()
                    return conn.execute(sql, args)
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() or "busy" in str(e).lower():
                    delay = min(0.1 * (2 ** attempt), 1.0) + random.uniform(0, 0.05)
                    logger.warning(f"DB locked, retry {attempt+1}/3 in {delay:.2f}s: {e}")
                    time.sleep(delay)
                    continue
                raise
        raise sqlite3.OperationalError("Database locked after max retries")
    
    def _create_schema(self):
        """스키마 생성 (초기화용)"""
        self._main_conn.executescript("""
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS schema_meta(version INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS chapters(number INTEGER PRIMARY KEY,title TEXT DEFAULT '',status TEXT DEFAULT '미작성',char_count INTEGER DEFAULT 0,char_count_spaces INTEGER DEFAULT 0,target_chars INTEGER DEFAULT 5000,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS chapter_plans(chapter_number INTEGER PRIMARY KEY,title TEXT DEFAULT '',content TEXT DEFAULT '',status TEXT DEFAULT '초안',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS story_sections(id INTEGER PRIMARY KEY AUTOINCREMENT,start_chapter INTEGER NOT NULL,end_chapter INTEGER NOT NULL,status TEXT DEFAULT '미작성',content TEXT DEFAULT '',snapshot TEXT DEFAULT '',updated_at TEXT,UNIQUE(start_chapter,end_chapter));
        CREATE TABLE IF NOT EXISTS characters(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,role TEXT DEFAULT '',profile TEXT DEFAULT '',personality TEXT DEFAULT '',speech_style TEXT DEFAULT '',goal TEXT DEFAULT '',secret TEXT DEFAULT '',arc TEXT DEFAULT '',status TEXT DEFAULT '초안',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS character_states(id INTEGER PRIMARY KEY AUTOINCREMENT,character_id INTEGER NOT NULL,chapter_number INTEGER NOT NULL,location TEXT DEFAULT '',cultivation TEXT DEFAULT '',condition TEXT DEFAULT '',injuries TEXT DEFAULT '',possessions TEXT DEFAULT '',emotions TEXT DEFAULT '',knows TEXT DEFAULT '',does_not_know TEXT DEFAULT '',notes TEXT DEFAULT '',updated_at TEXT,UNIQUE(character_id,chapter_number),FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS relationships(id INTEGER PRIMARY KEY AUTOINCREMENT,from_character TEXT,to_character TEXT,relation TEXT,current_state TEXT DEFAULT '',history TEXT DEFAULT '',start_chapter INTEGER,updated_at TEXT,UNIQUE(from_character,to_character,relation));
        CREATE TABLE IF NOT EXISTS world_entities(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,category TEXT DEFAULT '',description TEXT DEFAULT '',rules TEXT DEFAULT '',status TEXT DEFAULT '초안',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS timeline_events(id INTEGER PRIMARY KEY AUTOINCREMENT,chapter_number INTEGER,story_date TEXT DEFAULT '',title TEXT DEFAULT '',description TEXT DEFAULT '',location TEXT DEFAULT '',participants TEXT DEFAULT '',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS foreshadowing(id INTEGER PRIMARY KEY AUTOINCREMENT,code TEXT UNIQUE NOT NULL,title TEXT DEFAULT '',first_chapter INTEGER,latest_chapter INTEGER,reveal_chapter INTEGER,status TEXT DEFAULT '활성',public_info TEXT DEFAULT '',author_truth TEXT DEFAULT '',related_characters TEXT DEFAULT '',notes TEXT DEFAULT '',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS major_events(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT UNIQUE NOT NULL,start_chapter INTEGER,end_chapter INTEGER,description TEXT DEFAULT '',consequence TEXT DEFAULT '',status TEXT DEFAULT '계획',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS summaries(chapter_number INTEGER PRIMARY KEY,summary TEXT DEFAULT '',state_snapshot TEXT DEFAULT '',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS chapter_states(chapter_number INTEGER PRIMARY KEY,summary TEXT DEFAULT '',state TEXT DEFAULT '',source_hash TEXT DEFAULT '',status TEXT DEFAULT '갱신완료',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS section_memories(start_chapter INTEGER NOT NULL,end_chapter INTEGER NOT NULL,content TEXT DEFAULT '',source_hash TEXT DEFAULT '',status TEXT DEFAULT '갱신완료',updated_at TEXT,PRIMARY KEY(start_chapter,end_chapter));
        CREATE TABLE IF NOT EXISTS arc_memories(arc_number INTEGER PRIMARY KEY, start_chapter INTEGER NOT NULL,end_chapter INTEGER NOT NULL,content TEXT DEFAULT '',source_hash TEXT DEFAULT '',status TEXT DEFAULT '갱신완료',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS snapshots(scope TEXT PRIMARY KEY,content TEXT DEFAULT '',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS continuity_checks(id INTEGER PRIMARY KEY AUTOINCREMENT,chapter_number INTEGER,severity TEXT,category TEXT,message TEXT,evidence TEXT DEFAULT '',status TEXT DEFAULT '미해결',created_at TEXT);
        CREATE TABLE IF NOT EXISTS entity_state_ledger(id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,entity_key TEXT NOT NULL,chapter_number INTEGER NOT NULL,state TEXT DEFAULT '',source_hash TEXT DEFAULT '',updated_at TEXT,UNIQUE(kind,entity_key,chapter_number));
        CREATE TABLE IF NOT EXISTS foreshadow_events(id INTEGER PRIMARY KEY AUTOINCREMENT,foreshadow_id INTEGER NOT NULL,chapter_number INTEGER NOT NULL,event_type TEXT NOT NULL,description TEXT DEFAULT '',before_state TEXT DEFAULT '',after_state TEXT DEFAULT '',created_at TEXT,UNIQUE(foreshadow_id,chapter_number,event_type),FOREIGN KEY(foreshadow_id) REFERENCES foreshadowing(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS master_diffs(id INTEGER PRIMARY KEY AUTOINCREMENT,category TEXT NOT NULL,payload TEXT NOT NULL,status TEXT DEFAULT '제안',created_at TEXT,applied_at TEXT);
        CREATE TABLE IF NOT EXISTS plot_batches(id INTEGER PRIMARY KEY AUTOINCREMENT,start_chapter INTEGER NOT NULL,end_chapter INTEGER NOT NULL,status TEXT DEFAULT '대기',updated_at TEXT,UNIQUE(start_chapter,end_chapter));
        CREATE TABLE IF NOT EXISTS search_documents(doc_id INTEGER PRIMARY KEY AUTOINCREMENT,category TEXT NOT NULL,ref_key TEXT NOT NULL,content TEXT DEFAULT '',updated_at TEXT,UNIQUE(category,ref_key));
        CREATE VIRTUAL TABLE IF NOT EXISTS search_fts USING fts5(category,ref_key,content,content='search_documents',content_rowid='doc_id');
        CREATE TABLE IF NOT EXISTS ai_jobs(id INTEGER PRIMARY KEY AUTOINCREMENT,job_type TEXT,target TEXT,status TEXT,provider TEXT DEFAULT '',model TEXT DEFAULT '',prompt_chars INTEGER DEFAULT 0,output_chars INTEGER DEFAULT 0,started_at TEXT,completed_at TEXT,error TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS chat_messages(id INTEGER PRIMARY KEY AUTOINCREMENT,role TEXT,content TEXT,chapter_number INTEGER,created_at TEXT);
        CREATE TABLE IF NOT EXISTS ideas(id INTEGER PRIMARY KEY AUTOINCREMENT,content TEXT,created_at TEXT,used INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS plans(id INTEGER PRIMARY KEY CHECK(id=1),content TEXT DEFAULT '',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS contract(id INTEGER PRIMARY KEY CHECK(id=1),content TEXT DEFAULT '',locked INTEGER DEFAULT 0,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS section_contents(section TEXT PRIMARY KEY,content TEXT DEFAULT '',status TEXT DEFAULT '초안',updated_at TEXT);
        CREATE INDEX IF NOT EXISTS idx_chapters_status ON chapters(status);
        CREATE INDEX IF NOT EXISTS idx_chapters_updated_at ON chapters(updated_at);
        CREATE INDEX IF NOT EXISTS idx_chapter_plans_status ON chapter_plans(status);
        CREATE INDEX IF NOT EXISTS idx_story_sections_start_end ON story_sections(start_chapter,end_chapter);
        CREATE INDEX IF NOT EXISTS idx_character_states_chapter ON character_states(chapter_number);
        CREATE INDEX IF NOT EXISTS idx_character_states_character_chapter ON character_states(character_id,chapter_number);
        CREATE INDEX IF NOT EXISTS idx_timeline_chapter ON timeline_events(chapter_number);
        CREATE INDEX IF NOT EXISTS idx_foreshadow_status ON foreshadowing(status);
        CREATE INDEX IF NOT EXISTS idx_foreshadow_first ON foreshadowing(first_chapter);
        CREATE INDEX IF NOT EXISTS idx_foreshadow_latest ON foreshadowing(latest_chapter);
        CREATE INDEX IF NOT EXISTS idx_major_events_start ON major_events(start_chapter);
        CREATE INDEX IF NOT EXISTS idx_summaries_updated_at ON summaries(updated_at);
        CREATE INDEX IF NOT EXISTS idx_chapter_states_updated_at ON chapter_states(updated_at);
        CREATE INDEX IF NOT EXISTS idx_section_memories_start_end ON section_memories(start_chapter,end_chapter);
        CREATE INDEX IF NOT EXISTS idx_arc_memories_start_end ON arc_memories(start_chapter,end_chapter);
        CREATE INDEX IF NOT EXISTS idx_continuity_chapter ON continuity_checks(chapter_number);
        CREATE INDEX IF NOT EXISTS idx_chat_chapter ON chat_messages(chapter_number);
        CREATE INDEX IF NOT EXISTS idx_entity_state_kind_key_chapter ON entity_state_ledger(kind,entity_key,chapter_number);
        CREATE INDEX IF NOT EXISTS idx_entity_state_chapter ON entity_state_ledger(chapter_number);
        CREATE INDEX IF NOT EXISTS idx_foreshadow_events_chapter ON foreshadow_events(chapter_number);
        CREATE INDEX IF NOT EXISTS idx_foreshadow_events_fk ON foreshadow_events(foreshadow_id);
        CREATE INDEX IF NOT EXISTS idx_master_diffs_status ON master_diffs(status);
        CREATE INDEX IF NOT EXISTS idx_plot_batches_start ON plot_batches(start_chapter);
        """)
        self._main_conn.commit()
    
    def _migrate_schema(self):
        row = self._main_conn.execute("SELECT version FROM schema_meta LIMIT 1").fetchone()
        if row is None:
            self._main_conn.execute("INSERT INTO schema_meta(version) VALUES(?)", (3,))
            return
        version = int(row['version'])
        MIGRATIONS = {
            2: "",
            3: "CREATE INDEX IF NOT EXISTS idx_entity_state_updated ON entity_state_ledger(updated_at);",
        }
        for step in range(version + 1, 4):
            sql = MIGRATIONS.get(step)
            if sql:
                self._main_conn.executescript(sql)
            self._main_conn.execute("UPDATE schema_meta SET version=?", (step,))
    
    def _ensure_search_index(self):
        try:
            docs = int(self._main_conn.execute("SELECT COUNT(*) FROM search_documents").fetchone()[0])
            fts = int(self._main_conn.execute("SELECT COUNT(*) FROM search_fts").fetchone()[0])
            if docs != fts:
                self.rebuild_search_index()
        except Exception:
            self.rebuild_search_index()

    # ========== 기존 Database API 호환 메서드 ==========
    
    def execute(self, sql: str, args=()):
        """쓰기 작업 실행 (락 + 재시도)"""
        return self._execute_with_retry(sql, args, write=True)
    
    def _execute_read(self, sql: str, args=()):
        """읽기 작업 실행 (재시도)"""
        return self._execute_with_retry(sql, args, write=False)
    
    def close(self):
        try:
            if hasattr(self._local, 'conn') and self._local.conn:
                self._local.conn.close()
            if self._main_conn:
                self._main_conn.close()
            # 위임 대상인 기본 Database 연결도 함께 닫는다.
            base = getattr(self, '_base', None)
            if base is not None:
                base.close()
        except Exception:
            pass
    
    # ========== 기존 Database API 호환 메서드 (일부) ==========
    
    def execute(self, sql: str, args=()):
        return self._execute_with_retry(sql, args, write=True)
    
    def get_meta(self, key, default=""):
        r = self._execute_read("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return r["value"] if r else default
    
    def set_meta(self, key, value):
        self.execute("INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))
        self._index_doc("meta", key, f"{key} {value}")
    
    def get_plan(self):
        r = self._execute_read("SELECT content FROM plans WHERE id=1").fetchone()
        return r["content"] if r else ""
    
    def save_plan(self, content):
        self.execute("INSERT INTO plans(id,content,updated_at) VALUES(1,?,?) ON CONFLICT(id) DO UPDATE SET content=excluded.content,updated_at=excluded.updated_at", (content, now()))
        self._index_doc("plan", "1", content)
    
    def get_contract(self):
        return self._execute_read("SELECT * FROM contract WHERE id=1").fetchone()
    
    def save_contract(self, content, locked=False):
        self.execute("INSERT INTO contract(id,content,locked,updated_at) VALUES(1,?,?,?) ON CONFLICT(id) DO UPDATE SET content=excluded.content,locked=excluded.locked,updated_at=excluded.updated_at", (content, int(bool(locked)), now()))
        self._index_doc("contract", "1", content)
    
    def get_plan(self):
        r = self._execute_read("SELECT content FROM plans WHERE id=1").fetchone()
        return r["content"] if r else ""
    
    def save_plan(self, content):
        self.execute("INSERT INTO plans(id,content,updated_at) VALUES(1,?,?) ON CONFLICT(id) DO UPDATE SET content=excluded.content,updated_at=excluded.updated_at", (content, now()))
        self._index_doc("plan", "1", content)
    
    def get_contract(self):
        return self._execute_read("SELECT * FROM contract WHERE id=1").fetchone()
    
    def save_contract(self, content, locked=False):
        self.execute("INSERT INTO contract(id,content,locked,updated_at) VALUES(1,?,?,?) ON CONFLICT(id) DO UPDATE SET content=excluded.content,locked=excluded.locked,updated_at=excluded.updated_at", (content, int(bool(locked)), now()))
        self._index_doc("contract", "1", content)
    
    def get_contract(self):
        return self._execute_read("SELECT * FROM contract WHERE id=1").fetchone()
    
    def save_contract(self, content, locked=False):
        self.execute("INSERT INTO contract(id,content,locked,updated_at) VALUES(1,?,?,?) ON CONFLICT(id) DO UPDATE SET content=excluded.content,locked=excluded.locked,updated_at=excluded.updated_at", (content, int(bool(locked)), now()))
        self._index_doc("contract", "1", content)
    
    def get_plan(self):
        r = self._execute_read("SELECT content FROM plans WHERE id=1").fetchone()
        return r["content"] if r else ""
    
    def save_plan(self, content):
        self.execute("INSERT INTO plans(id,content,updated_at) VALUES(1,?,?) ON CONFLICT(id) DO UPDATE SET content=excluded.content,updated_at=excluded.updated_at", (content, now()))
        self._index_doc("plan", "1", content)
    
    def get_contract(self):
        return self._execute_read("SELECT * FROM contract WHERE id=1").fetchone()
    
    def save_contract(self, content, locked=False):
        self.execute("INSERT INTO contract(id,content,locked,updated_at) VALUES(1,?,?,?) ON CONFLICT(id) DO UPDATE SET content=excluded.content,locked=excluded.locked,updated_at=excluded.updated_at", (content, int(bool(locked)), now()))
        self._index_doc("contract", "1", content)