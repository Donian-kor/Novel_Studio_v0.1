from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime

def now():
    return datetime.now().isoformat(timespec="seconds")

# 현재 스키마 버전. 스키마 변경 시 MIGRATIONS에 새 단계를 추가하고 버전을 올린다.
CURRENT_SCHEMA_VERSION = 4
# 4단계: 구조 변경 없음. 테이블은 _schema()에서 생성되므로 마이그레이션 SQL이 필요 없다.
# 구버전 DB의 누락 오브젝트는 _schema() 내 CREATE TABLE IF NOT EXISTS로 보완된다.
MIGRATIONS = {4: "PRAGMA user_version = 4;"}

class SQLiteStorage:
    SCHEMA_PROFILES = {
        "story": {"meta", "schema_meta", "plans", "contract", "section_contents", "story_sections", "master_diffs", "plot_batches", "ideas", "story_subsections", "chapter_stories", "search_documents", "search_fts"},
        "setting": {"schema_meta", "characters", "character_states", "relationships", "world_entities", "timeline_events", "foreshadowing", "major_events", "foreshadow_events", "search_documents", "search_fts"},
        "manuscript": {"schema_meta", "chapters", "chat_messages", "ai_jobs", "search_documents", "search_fts"},
        "summary": {"schema_meta", "chapter_states", "continuity_checks", "search_documents", "search_fts"},
    }

    def __init__(self, path: Path, profile: str | None = None):
        self.path = Path(path)
        self.profile = profile
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._schema()

    def close(self):
        """SQLite 연결을 완전히 종료한다. Windows의 WAL 파일 잠금도 정리한다."""
        conn = getattr(self, "conn", None)
        if conn is None:
            return
        try:
            conn.commit()
            try:
                # 열린 cursor/연결이 남아 있지 않을 때 SQLite 보조 파일을 정리한다.
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            except sqlite3.Error:
                pass
        except sqlite3.Error:
            pass
        finally:
            try:
                conn.close()
            except sqlite3.Error:
                pass
            self.conn = None

    def _schema(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS schema_meta(version INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS chapters(number INTEGER PRIMARY KEY,title TEXT DEFAULT '',status TEXT DEFAULT '미작성',char_count INTEGER DEFAULT 0,char_count_spaces INTEGER DEFAULT 0,target_chars INTEGER DEFAULT 5000,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS story_sections(id INTEGER PRIMARY KEY AUTOINCREMENT,start_chapter INTEGER NOT NULL,end_chapter INTEGER NOT NULL,status TEXT DEFAULT '미작성',content TEXT DEFAULT '',updated_at TEXT,UNIQUE(start_chapter,end_chapter));
        CREATE TABLE IF NOT EXISTS story_subsections(id INTEGER PRIMARY KEY AUTOINCREMENT,parent_start INTEGER NOT NULL,parent_end INTEGER NOT NULL,start_chapter INTEGER NOT NULL,end_chapter INTEGER NOT NULL,title TEXT DEFAULT '',content TEXT DEFAULT '',status TEXT DEFAULT '미작성',updated_at TEXT,UNIQUE(parent_start,parent_end,start_chapter,end_chapter));
        CREATE INDEX IF NOT EXISTS idx_story_sub_parent ON story_subsections(parent_start,parent_end,start_chapter);
        CREATE TABLE IF NOT EXISTS chapter_stories(chapter_number INTEGER PRIMARY KEY,long_start INTEGER DEFAULT 0,long_end INTEGER DEFAULT 0,sub_start INTEGER DEFAULT 0,sub_end INTEGER DEFAULT 0,title TEXT DEFAULT '',content TEXT DEFAULT '',status TEXT DEFAULT '초안',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS characters(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,role TEXT DEFAULT '',profile TEXT DEFAULT '',personality TEXT DEFAULT '',speech_style TEXT DEFAULT '',goal TEXT DEFAULT '',secret TEXT DEFAULT '',arc TEXT DEFAULT '',status TEXT DEFAULT '초안',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS character_states(id INTEGER PRIMARY KEY AUTOINCREMENT,character_id INTEGER NOT NULL,chapter_number INTEGER NOT NULL,location TEXT DEFAULT '',cultivation TEXT DEFAULT '',condition TEXT DEFAULT '',injuries TEXT DEFAULT '',possessions TEXT DEFAULT '',emotions TEXT DEFAULT '',knows TEXT DEFAULT '',does_not_know TEXT DEFAULT '',notes TEXT DEFAULT '',updated_at TEXT,UNIQUE(character_id,chapter_number),FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS relationships(id INTEGER PRIMARY KEY AUTOINCREMENT,from_character TEXT,to_character TEXT,relation TEXT,current_state TEXT DEFAULT '',history TEXT DEFAULT '',start_chapter INTEGER,updated_at TEXT,UNIQUE(from_character,to_character,relation));
        CREATE TABLE IF NOT EXISTS world_entities(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,category TEXT DEFAULT '',description TEXT DEFAULT '',rules TEXT DEFAULT '',status TEXT DEFAULT '초안',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS timeline_events(id INTEGER PRIMARY KEY AUTOINCREMENT,chapter_number INTEGER,story_date TEXT DEFAULT '',title TEXT DEFAULT '',description TEXT DEFAULT '',location TEXT DEFAULT '',participants TEXT DEFAULT '',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS foreshadowing(id INTEGER PRIMARY KEY AUTOINCREMENT,code TEXT UNIQUE NOT NULL,title TEXT DEFAULT '',first_chapter INTEGER,latest_chapter INTEGER,reveal_chapter INTEGER,status TEXT DEFAULT '활성',public_info TEXT DEFAULT '',author_truth TEXT DEFAULT '',related_characters TEXT DEFAULT '',notes TEXT DEFAULT '',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS major_events(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT UNIQUE NOT NULL,start_chapter INTEGER,end_chapter INTEGER,description TEXT DEFAULT '',consequence TEXT DEFAULT '',status TEXT DEFAULT '계획',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS chapter_states(chapter_number INTEGER PRIMARY KEY,summary TEXT DEFAULT '',state TEXT DEFAULT '',source_hash TEXT DEFAULT '',status TEXT DEFAULT '갱신완료',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS continuity_checks(id INTEGER PRIMARY KEY AUTOINCREMENT,chapter_number INTEGER,severity TEXT,category TEXT,message TEXT,evidence TEXT DEFAULT '',status TEXT DEFAULT '미해결',created_at TEXT);
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
        CREATE INDEX IF NOT EXISTS idx_story_sections_start_end ON story_sections(start_chapter,end_chapter);
        CREATE INDEX IF NOT EXISTS idx_character_states_chapter ON character_states(chapter_number);
        CREATE INDEX IF NOT EXISTS idx_character_states_character_chapter ON character_states(character_id,chapter_number);
        CREATE INDEX IF NOT EXISTS idx_timeline_chapter ON timeline_events(chapter_number);
        CREATE INDEX IF NOT EXISTS idx_foreshadow_status ON foreshadowing(status);
        CREATE INDEX IF NOT EXISTS idx_foreshadow_first ON foreshadowing(first_chapter);
        CREATE INDEX IF NOT EXISTS idx_foreshadow_latest ON foreshadowing(latest_chapter);
        CREATE INDEX IF NOT EXISTS idx_major_events_start ON major_events(start_chapter);
        CREATE INDEX IF NOT EXISTS idx_chapter_states_updated_at ON chapter_states(updated_at);
        CREATE INDEX IF NOT EXISTS idx_continuity_chapter ON continuity_checks(chapter_number);
        CREATE INDEX IF NOT EXISTS idx_chat_chapter ON chat_messages(chapter_number);
        CREATE INDEX IF NOT EXISTS idx_foreshadow_events_chapter ON foreshadow_events(chapter_number);
        CREATE INDEX IF NOT EXISTS idx_foreshadow_events_fk ON foreshadow_events(foreshadow_id);
        CREATE INDEX IF NOT EXISTS idx_master_diffs_status ON master_diffs(status);
        CREATE INDEX IF NOT EXISTS idx_plot_batches_start ON plot_batches(start_chapter);
        """)
        self.conn.commit()
        self._migrate_schema()
        self._prune_profile_schema()
        self._ensure_search_index()

    def _prune_profile_schema(self):
        """프로필별 허용 테이블만 남겨 실제 DB를 물리적으로 분리한다."""
        if not self.profile:
            return
        allowed = self.SCHEMA_PROFILES.get(self.profile)
        if not allowed:
            raise ValueError(f"알 수 없는 DB 프로필: {self.profile}")
        rows = self.conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'").fetchall()
        names = {str(r[0]) for r in rows}
        self.conn.execute("PRAGMA foreign_keys=OFF")
        try:
            # 가상 FTS 테이블과 원본 테이블은 함께 정리해야 한다.
            protected = set(allowed) | {'schema_meta'} | {n for n in names if n.startswith('search_fts_')}
            for name in sorted(names - protected, reverse=True):
                try:
                    self.conn.execute(f'DROP TABLE IF EXISTS "{name}"')
                except sqlite3.Error:
                    pass
            self.conn.execute("PRAGMA user_version = 1501")
            self.conn.commit()
        finally:
            self.conn.execute("PRAGMA foreign_keys=ON")

    def _migrate_schema(self):
        """schema_meta 버전에 맞춰 MIGRATIONS를 순차 적용한다.

        - schema_meta 행이 없으면(새 DB) _schema()가 이미 최신 구조를 만들었으므로
          최신 버전만 기록한다. 구버전 DB의 누락 오브젝트는 IF NOT EXISTS로 보완된다.
        - 행이 있으면 현재 버전 다음 단계부터 MIGRATIONS를 순서대로 실행한다.
        """
        row=self.conn.execute("SELECT version FROM schema_meta LIMIT 1").fetchone()
        if row is None:
            self.execute("INSERT INTO schema_meta(version) VALUES(?)",(CURRENT_SCHEMA_VERSION,))
            return
        version=int(row['version'])
        for step in range(version+1,CURRENT_SCHEMA_VERSION+1):
            sql=MIGRATIONS.get(step)
            if sql: self.conn.executescript(sql)
            self.execute("UPDATE schema_meta SET version=?",(step,))

    def _ensure_search_index(self):
        try:
            docs=int(self.conn.execute("SELECT COUNT(*) FROM search_documents").fetchone()[0])
            fts=int(self.conn.execute("SELECT COUNT(*) FROM search_fts").fetchone()[0])
            if docs != fts:
                self.rebuild_search_index()
        except Exception:
            self.rebuild_search_index()

    def execute(self, sql, args=()):
        cur = self.conn.execute(sql, args); self.conn.commit(); return cur

    def get_meta(self, key, default=""):
        r=self.conn.execute("SELECT value FROM meta WHERE key=?",(key,)).fetchone(); return r["value"] if r else default
    def set_meta(self,key,value):
        self.execute("INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(key,str(value)))
        self._index_doc("meta", key, f"{key} {value}")

    def ensure_chapters(self,total,target):
        for n in range(1,int(total)+1):
            self.conn.execute("INSERT OR IGNORE INTO chapters(number,title,target_chars,updated_at) VALUES(?,?,?,?)",(n,f"{n}화",int(target),now()))
        self.conn.commit()
    def chapters(self, limit=None, offset=0):
        sql="SELECT * FROM chapters ORDER BY number"
        args=[]
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"; args=[int(limit), int(offset)]
        return self.conn.execute(sql,args).fetchall()
    def chapter_stats(self):
        r=self.conn.execute("SELECT COUNT(*) AS total, COALESCE(SUM(char_count),0) AS total_chars, SUM(CASE WHEN status IN ('작성완료','확정','윤문완료') THEN 1 ELSE 0 END) AS done FROM chapters").fetchone()
        return dict(r) if r else {'total':0,'total_chars':0,'done':0}
    def chapter_count(self):
        r=self.conn.execute("SELECT COUNT(*) AS n FROM chapters").fetchone(); return int(r['n'] or 0)
    def chapter_range(self,start,end):
        return self.conn.execute("SELECT * FROM chapters WHERE number BETWEEN ? AND ? ORDER BY number",(int(start),int(end))).fetchall()
    def chapter(self,n): return self.conn.execute("SELECT * FROM chapters WHERE number=?",(n,)).fetchone()
    def set_chapter_meta(self,n,title,status,count,count_spaces,target):
        self.execute("""INSERT INTO chapters(number,title,status,char_count,char_count_spaces,target_chars,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(number) DO UPDATE SET title=excluded.title,status=excluded.status,char_count=excluded.char_count,char_count_spaces=excluded.char_count_spaces,target_chars=excluded.target_chars,updated_at=excluded.updated_at""",(n,title,status,count,count_spaces,target,now()))
        self._index_doc("chapter", n, f"{n}화 {title} {status}")

    def get_plan(self):
        r=self.conn.execute("SELECT content FROM plans WHERE id=1").fetchone(); return r["content"] if r else ""
    def save_plan(self,content):
        self.execute("INSERT INTO plans(id,content,updated_at) VALUES(1,?,?) ON CONFLICT(id) DO UPDATE SET content=excluded.content,updated_at=excluded.updated_at",(content,now()))
        self._index_doc("plan", "1", content)
    def get_contract(self): return self.conn.execute("SELECT * FROM contract WHERE id=1").fetchone()
    def save_contract(self,content,locked=False):
        self.execute("INSERT INTO contract(id,content,locked,updated_at) VALUES(1,?,?,?) ON CONFLICT(id) DO UPDATE SET content=excluded.content,locked=excluded.locked,updated_at=excluded.updated_at",(content,int(bool(locked)),now()))
        self._index_doc("contract", "1", content)

    def section_content(self,s):
        r=self.conn.execute("SELECT content FROM section_contents WHERE section=?",(s,)).fetchone(); return r["content"] if r else ""
    def save_section_content(self,s,content,status="초안"):
        self.execute("INSERT INTO section_contents(section,content,status,updated_at) VALUES(?,?,?,?) ON CONFLICT(section) DO UPDATE SET content=excluded.content,status=excluded.status,updated_at=excluded.updated_at",(s,content,status,now()))
        self._index_doc("section", s, f"{s} {content}")

    def sections(self, limit=None, offset=0):
        sql="SELECT * FROM story_sections ORDER BY start_chapter"; args=[]
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"; args=[int(limit),int(offset)]
        return self.conn.execute(sql,args).fetchall()
    def section_for_chapter(self, chapter):
        return self.conn.execute("SELECT * FROM story_sections WHERE start_chapter<=? AND end_chapter>=? ORDER BY (end_chapter-start_chapter) LIMIT 1",(int(chapter),int(chapter))).fetchone()
    def sections_overlapping(self, start, end):
        return self.conn.execute("SELECT * FROM story_sections WHERE end_chapter>=? AND start_chapter<=? ORDER BY start_chapter",(int(start),int(end))).fetchall()
    def section(self,s,e): return self.conn.execute("SELECT * FROM story_sections WHERE start_chapter=? AND end_chapter=?",(s,e)).fetchone()
    def save_section(self,s,e,status,content):
        self.execute("INSERT INTO story_sections(start_chapter,end_chapter,status,content,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(start_chapter,end_chapter) DO UPDATE SET status=excluded.status,content=excluded.content,updated_at=excluded.updated_at",(int(s),int(e),status or "초안",content or "",now()))

    def story_subsections(self, parent_start, parent_end):
        return self.conn.execute("SELECT * FROM story_subsections WHERE parent_start=? AND parent_end=? ORDER BY start_chapter",(int(parent_start),int(parent_end))).fetchall()

    def story_subsection(self, start, end):
        return self.conn.execute("SELECT * FROM story_subsections WHERE start_chapter=? AND end_chapter=?",(int(start),int(end))).fetchone()

    def save_story_subsection(self,parent_start,parent_end,start,end,title,content,status="초안"):
        self.execute("INSERT INTO story_subsections(parent_start,parent_end,start_chapter,end_chapter,title,content,status,updated_at) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(parent_start,parent_end,start_chapter,end_chapter) DO UPDATE SET title=excluded.title,content=excluded.content,status=excluded.status,updated_at=excluded.updated_at",(int(parent_start),int(parent_end),int(start),int(end),title or "",content or "",status or "초안",now()))

    def story_subsection_for_chapter(self, chapter):
        return self.conn.execute("SELECT * FROM story_subsections WHERE start_chapter<=? AND end_chapter>=? ORDER BY start_chapter DESC LIMIT 1",(int(chapter),int(chapter))).fetchone()

    def chapter_story(self, chapter):
        return self.conn.execute("SELECT * FROM chapter_stories WHERE chapter_number=?",(int(chapter),)).fetchone()

    def save_chapter_story(self,chapter,long_start,long_end,sub_start,sub_end,title,content,status="초안"):
        self.execute("INSERT INTO chapter_stories(chapter_number,long_start,long_end,sub_start,sub_end,title,content,status,updated_at) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(chapter_number) DO UPDATE SET long_start=excluded.long_start,long_end=excluded.long_end,sub_start=excluded.sub_start,sub_end=excluded.sub_end,title=excluded.title,content=excluded.content,status=excluded.status,updated_at=excluded.updated_at",(int(chapter),int(long_start),int(long_end),int(sub_start),int(sub_end),title or "",content or "",status or "초안",now()))

    def characters(self, limit=None, offset=0, roles=None):
        sql="SELECT * FROM characters"; args=[]; where=[]
        if roles:
            placeholders=','.join('?' for _ in roles); where.append(f"role IN ({placeholders})"); args.extend(roles)
        if where: sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY id"
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"; args.extend([int(limit),int(offset)])
        return self.conn.execute(sql,args).fetchall()
    def save_character(self,d):
        self.execute("""INSERT INTO characters(name,role,profile,personality,speech_style,goal,secret,arc,status,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET role=excluded.role,profile=excluded.profile,personality=excluded.personality,speech_style=excluded.speech_style,goal=excluded.goal,secret=excluded.secret,arc=excluded.arc,status=excluded.status,updated_at=excluded.updated_at""",(d.get("name",""),d.get("role",""),d.get("profile",""),d.get("personality",""),d.get("speech_style",""),d.get("goal",""),d.get("secret",""),d.get("arc",""),d.get("status","초안"),now()))
        key=d.get("name","")
        self._index_doc("character", key, " ".join(str(d.get(k,"") or "") for k in ("name","role","profile","personality","goal","secret")))
    def world_entities(self, limit=None, offset=0, category=None):
        sql="SELECT * FROM world_entities"; args=[]
        if category is not None:
            sql += " WHERE category=?"; args.append(category)
        sql += " ORDER BY id"
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"; args.extend([int(limit),int(offset)])
        return self.conn.execute(sql,args).fetchall()
    def save_world(self,d):
        self.execute("INSERT INTO world_entities(name,category,description,rules,status,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET category=excluded.category,description=excluded.description,rules=excluded.rules,status=excluded.status,updated_at=excluded.updated_at",(d.get("name",""),d.get("category",""),d.get("description",""),d.get("rules",""),d.get("status","초안"),now()))
        self._index_doc("world", d.get("name",""), " ".join(str(d.get(k,"") or "") for k in ("name","category","description","rules")))
    def foreshadows(self, limit=None, offset=0, active_only=False):
        sql="SELECT * FROM foreshadowing"; args=[]
        if active_only: sql += " WHERE status!='회수'"
        sql += " ORDER BY id"
        if limit is not None: sql += " LIMIT ? OFFSET ?"; args.extend([int(limit),int(offset)])
        return self.conn.execute(sql,args).fetchall()
    def active_foreshadow_count(self):
        r=self.conn.execute("SELECT COUNT(*) AS n FROM foreshadowing WHERE status!='회수'").fetchone(); return int(r['n'] or 0)
    def save_foreshadow(self,d):
        code=d.get("code","")
        self.execute("INSERT INTO foreshadowing(code,title,first_chapter,latest_chapter,reveal_chapter,status,public_info,author_truth,related_characters,notes,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(code) DO UPDATE SET title=excluded.title,first_chapter=excluded.first_chapter,latest_chapter=excluded.latest_chapter,reveal_chapter=excluded.reveal_chapter,status=excluded.status,public_info=excluded.public_info,author_truth=excluded.author_truth,related_characters=excluded.related_characters,notes=excluded.notes,updated_at=excluded.updated_at",(code,d.get("title",""),d.get("first_chapter"),d.get("latest_chapter"),d.get("reveal_chapter"),d.get("status","활성"),d.get("public_info",""),d.get("author_truth",""),d.get("related_characters",""),d.get("notes",""),now()))
        for ch,etype in ((d.get('first_chapter'),'첫 암시'),(d.get('latest_chapter'),'최근 진행'),(d.get('reveal_chapter'),'회수/공개')):
            if ch: self.add_foreshadow_event(code,int(ch),etype)
        self._index_doc("foreshadow", code, " ".join(str(d.get(k,"") or "") for k in ("code","title","public_info","author_truth","notes")))
    def _delete_index(self,category,ref_key):
        row=self.conn.execute("SELECT doc_id,category,ref_key,content FROM search_documents WHERE category=? AND ref_key=?",(str(category),str(ref_key))).fetchone()
        if not row: return
        try:
            self.conn.execute("INSERT INTO search_fts(search_fts,rowid,category,ref_key,content) VALUES('delete',?,?,?,?)",(int(row['doc_id']),row['category'],row['ref_key'],row['content']))
        except Exception:
            try: self.conn.execute("DELETE FROM search_fts WHERE rowid=?",(int(row['doc_id']),))
            except Exception: pass
        self.conn.execute("DELETE FROM search_documents WHERE doc_id=?",(int(row['doc_id']),)); self.conn.commit()

    def delete_character(self,n):
        self.execute("DELETE FROM characters WHERE name=?",(n,)); self._delete_index("character",n)
    def delete_world(self,n):
        self.execute("DELETE FROM world_entities WHERE name=?",(n,)); self._delete_index("world",n)
    def delete_foreshadow(self,c):
        self.execute("DELETE FROM foreshadowing WHERE code=?",(c,)); self._delete_index("foreshadow",c)
    def delete_timeline(self,i): self.execute("DELETE FROM timeline_events WHERE id=?",(i,))
    def delete_major_event(self,t): self.execute("DELETE FROM major_events WHERE title=?",(t,))
    def save_timeline(self,d):
        self.execute("INSERT INTO timeline_events(chapter_number,story_date,title,description,location,participants,updated_at) VALUES(?,?,?,?,?,?,?)",(d.get("chapter_number"),d.get("story_date",""),d.get("title",""),d.get("description",""),d.get("location",""),d.get("participants",""),now()))
        key=d.get("chapter_number") or now()
        self._index_doc("timeline", key, " ".join(str(d.get(k,"") or "") for k in ("chapter_number","story_date","title","description","location","participants")))

    def update_timeline(self, timeline_id, data):
        self.execute(
            "UPDATE timeline_events SET title=?, description=?, chapter_number=?, story_date=?, location=?, participants=?, updated_at=? WHERE id=?",
            (
                data.get("title", ""),
                data.get("description", ""),
                data.get("chapter_number"),
                data.get("story_date", ""),
                data.get("location", ""),
                data.get("participants", ""),
                now(),
                int(timeline_id),
            ),
        )
        self._index_doc("timeline", int(timeline_id), " ".join(str(data.get(k, "") or "") for k in ("chapter_number", "story_date", "title", "description", "location", "participants")))
    def save_major_event(self,d):
        self.execute("INSERT INTO major_events(title,start_chapter,end_chapter,description,consequence,status,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(title) DO UPDATE SET start_chapter=excluded.start_chapter,end_chapter=excluded.end_chapter,description=excluded.description,consequence=excluded.consequence,status=excluded.status,updated_at=excluded.updated_at",(d.get("title",""),d.get("start_chapter"),d.get("end_chapter"),d.get("description",""),d.get("consequence",""),d.get("status","계획"),now()))
        self._index_doc("event", d.get("title",""), " ".join(str(d.get(k,"") or "") for k in ("title","description","consequence")))
    def timeline(self, limit=None, offset=0, start=None, end=None):
        sql="SELECT * FROM timeline_events"; args=[]; where=[]
        if start is not None: where.append("chapter_number>=?"); args.append(int(start))
        if end is not None: where.append("chapter_number<=?"); args.append(int(end))
        if where: sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY COALESCE(chapter_number,999999),id"
        if limit is not None: sql += " LIMIT ? OFFSET ?"; args.extend([int(limit),int(offset)])
        return self.conn.execute(sql,args).fetchall()
    def major_events(self, limit=None, offset=0, start=None, end=None):
        sql="SELECT * FROM major_events"; args=[]; where=[]
        if start is not None: where.append("COALESCE(end_chapter,start_chapter,0)>=?"); args.append(int(start))
        if end is not None: where.append("COALESCE(start_chapter,end_chapter,999999)<=?"); args.append(int(end))
        if where: sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY COALESCE(start_chapter,999999),id"
        if limit is not None: sql += " LIMIT ? OFFSET ?"; args.extend([int(limit),int(offset)])
        return self.conn.execute(sql,args).fetchall()
    def chapter_state(self,n): return self.conn.execute("SELECT * FROM chapter_states WHERE chapter_number=?",(int(n),)).fetchone()
    def latest_chapter_state(self,before=None):
        if before is None:
            return self.conn.execute("SELECT * FROM chapter_states ORDER BY chapter_number DESC LIMIT 1").fetchone()
        return self.conn.execute("SELECT * FROM chapter_states WHERE chapter_number<=? ORDER BY chapter_number DESC LIMIT 1",(int(before),)).fetchone()
    def chapter_states(self, limit=None, offset=0, start=None, end=None):
        sql="SELECT * FROM chapter_states"; args=[]; where=[]
        if start is not None: where.append("chapter_number>=?"); args.append(int(start))
        if end is not None: where.append("chapter_number<=?"); args.append(int(end))
        if where: sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY chapter_number DESC"
        if limit is not None: sql += " LIMIT ? OFFSET ?"; args.extend([int(limit), int(offset)])
        return self.conn.execute(sql,args).fetchall()
    def save_chapter_state(self,n,summary,state,source_hash="",status="갱신완료"):
        self.execute("INSERT INTO chapter_states(chapter_number,summary,state,source_hash,status,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(chapter_number) DO UPDATE SET summary=excluded.summary,state=excluded.state,source_hash=excluded.source_hash,status=excluded.status,updated_at=excluded.updated_at",(int(n),summary or "",state or "",source_hash or "",status,now()))
    def arc_bounds(self,total,arc_count=5):
        total=max(1,int(total)); count=max(1,min(int(arc_count),total))
        base=total//count; rem=total%count; out=[]; start=1
        for i in range(1,count+1):
            size=base+(1 if i<=rem else 0); end=start+size-1; out.append((i,start,end)); start=end+1
        return out
    def add_idea(self,content):
        self.execute("INSERT INTO ideas(content,created_at,used) VALUES(?,?,0)",(content,now()))
        row=self.conn.execute("SELECT id FROM ideas ORDER BY id DESC LIMIT 1").fetchone()
        if row: self._index_doc("idea", row["id"], content)
    def recent_ideas(self,limit=20): return self.conn.execute("SELECT content FROM ideas ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
    def use_idea(self,content): self.execute("UPDATE ideas SET used=0"); self.execute("UPDATE ideas SET used=1 WHERE content=?",(content,))
    def add_chat(self,role,content,chapter=None): self.execute("INSERT INTO chat_messages(role,content,chapter_number,created_at) VALUES(?,?,?,?)",(role,content,chapter,now()))
    def chat_messages(self, limit=None, offset=0, chapter=None):
        sql="SELECT * FROM chat_messages"; args=[]
        if chapter is not None: sql += " WHERE chapter_number=?"; args.append(int(chapter))
        sql += " ORDER BY id DESC"
        if limit is not None: sql += " LIMIT ? OFFSET ?"; args.extend([int(limit),int(offset)])
        return self.conn.execute(sql,args).fetchall()
    def continuity_for_chapter(self, chapter):
        return self.conn.execute("SELECT * FROM continuity_checks WHERE chapter_number=? ORDER BY id DESC", (int(chapter),)).fetchall()

    def continuity(self): return self.conn.execute("SELECT * FROM continuity_checks ORDER BY id DESC").fetchall()
    def add_continuity(self,ch,severity,category,message,evidence=""): self.execute("INSERT INTO continuity_checks(chapter_number,severity,category,message,evidence,created_at) VALUES(?,?,?,?,?,?)",(ch,severity,category,message,evidence,now()))
    def start_job(self,typ,target,provider,model):
        c=self.conn.execute("INSERT INTO ai_jobs(job_type,target,status,provider,model,started_at) VALUES(?,?,?,?,?,?)",(typ,target,"실행중",provider,model,now())); self.conn.commit(); return c.lastrowid
    def finish_job(self,jid,status,error=""): self.execute("UPDATE ai_jobs SET status=?,completed_at=?,error=? WHERE id=?",(status,now(),error,jid))
    def foreshadow_events(self,code=None,start=None,end=None,limit=100):
        sql="SELECT fe.*,f.code,f.title FROM foreshadow_events fe JOIN foreshadowing f ON f.id=fe.foreshadow_id"; args=[]; where=[]
        if code is not None: where.append("f.code=?"); args.append(code)
        if start is not None: where.append("fe.chapter_number>=?"); args.append(int(start))
        if end is not None: where.append("fe.chapter_number<=?"); args.append(int(end))
        if where: sql += " WHERE "+" AND ".join(where)
        sql += " ORDER BY fe.chapter_number,fe.id LIMIT ?"; args.append(int(limit))
        return self.conn.execute(sql,args).fetchall()
    def add_foreshadow_event(self,code,chapter,event_type,description='',before_state='',after_state=''):
        f=self.conn.execute("SELECT id FROM foreshadowing WHERE code=?",(code,)).fetchone()
        if not f:return
        self.execute("INSERT INTO foreshadow_events(foreshadow_id,chapter_number,event_type,description,before_state,after_state,created_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(foreshadow_id,chapter_number,event_type) DO UPDATE SET description=excluded.description,before_state=excluded.before_state,after_state=excluded.after_state",(f['id'],int(chapter),event_type,description,before_state,after_state,now()))
    def save_master_diff(self,category,payload,status='제안'): self.execute("INSERT INTO master_diffs(category,payload,status,created_at) VALUES(?,?,?,?)",(category,payload,status,now()))
    def latest_master_diff(self,category=None):
        if category:return self.conn.execute("SELECT * FROM master_diffs WHERE category=? ORDER BY id DESC LIMIT 1",(category,)).fetchone()
        return self.conn.execute("SELECT * FROM master_diffs ORDER BY id DESC LIMIT 1").fetchone()
    def set_plot_batch(self,start,end,status='대기'): self.execute("INSERT INTO plot_batches(start_chapter,end_chapter,status,updated_at) VALUES(?,?,?,?) ON CONFLICT(start_chapter,end_chapter) DO UPDATE SET status=excluded.status,updated_at=excluded.updated_at",(int(start),int(end),status,now()))
    def plot_batches(self,limit=100): return self.conn.execute("SELECT * FROM plot_batches ORDER BY start_chapter LIMIT ?",(int(limit),)).fetchall()
    def characters_relevant(self,chapter,limit=40): return self.conn.execute("SELECT c.* FROM characters c ORDER BY CASE WHEN EXISTS(SELECT 1 FROM character_states cs WHERE cs.character_id=c.id AND cs.chapter_number<=?) THEN 0 ELSE 1 END,c.id LIMIT ?",(int(chapter),int(limit))).fetchall()
    def world_relevant(self,chapter,limit=40): return self.conn.execute("SELECT w.* FROM world_entities w WHERE w.category='세계관' OR EXISTS(SELECT 1 FROM timeline_events t WHERE t.chapter_number<=? AND (t.location=w.name OR t.description LIKE '%'||w.name||'%')) ORDER BY w.id LIMIT ?",(int(chapter),int(limit))).fetchall()
    def foreshadows_relevant(self,chapter,limit=60): return self.conn.execute("SELECT f.* FROM foreshadowing f WHERE f.first_chapter IS NULL OR f.first_chapter<=? ORDER BY CASE WHEN f.latest_chapter IS NULL THEN 0 ELSE ABS(f.latest_chapter-?) END,f.id LIMIT ?",(int(chapter),int(chapter),int(limit))).fetchall()

    def _index_doc(self,category,ref_key,content):
        category=str(category); ref_key=str(ref_key); content=content or ''
        old=self.conn.execute("SELECT doc_id,category,ref_key,content FROM search_documents WHERE category=? AND ref_key=?",(category,ref_key)).fetchone()
        if old:
            try:
                self.conn.execute("INSERT INTO search_fts(search_fts,rowid,category,ref_key,content) VALUES('delete',?,?,?,?)", (int(old["doc_id"]), old["category"], old["ref_key"], old["content"]))
            except Exception:
                try: self.conn.execute("DELETE FROM search_fts WHERE rowid=?",(int(old["doc_id"]),))
                except Exception: pass
        self.conn.execute("INSERT INTO search_documents(category,ref_key,content,updated_at) VALUES(?,?,?,?) ON CONFLICT(category,ref_key) DO UPDATE SET content=excluded.content,updated_at=excluded.updated_at",(category,ref_key,content,now()))
        row=self.conn.execute("SELECT doc_id FROM search_documents WHERE category=? AND ref_key=?",(category,ref_key)).fetchone()
        if row:
            rid=int(row["doc_id"])
            self.conn.execute("INSERT INTO search_fts(rowid,category,ref_key,content) VALUES(?,?,?,?)",(rid,category,ref_key,content))
        self.conn.commit()

    def rebuild_search_index(self):
        if not self._table_exists("search_documents") or not self._table_exists("search_fts"):
            return
        try:
            self.conn.execute("INSERT INTO search_fts(search_fts) VALUES('delete-all')")
        except Exception:
            pass
        self.conn.execute("DELETE FROM search_documents")
        source_specs = {
            "meta": ("SELECT key,value FROM meta", lambda r: f"{r['key']} {r['value']}"),
            "plan": ("SELECT id,content FROM plans", lambda r: f"소설 설계 {r['content']}"),
            "contract": ("SELECT id,content FROM contract", lambda r: f"작품 규칙 {r['content']}"),
            "section": ("SELECT section,content FROM section_contents", lambda r: f"{r['section']} {r['content']}"),
            "story": ("SELECT start_chapter,end_chapter,content FROM story_sections", lambda r: f"{r['start_chapter']}~{r['end_chapter']}화 {r['content']}"),
            "substory": ("SELECT start_chapter,end_chapter,title,content FROM story_subsections", lambda r: f"{r['start_chapter']}~{r['end_chapter']}화 {r['title']} {r['content']}"),
            "chapter_story": ("SELECT chapter_number,title,content FROM chapter_stories", lambda r: f"{r['chapter_number']}화 {r['title']} {r['content']}"),
            "character": ("SELECT id,name,role,profile,personality,goal,secret FROM characters", lambda r: f"{r['name']} {r['role']} {r['profile']} {r['personality']} {r['goal']} {r['secret']}"),
            "world": ("SELECT id,name,category,description,rules FROM world_entities", lambda r: f"{r['name']} {r['category']} {r['description']} {r['rules']}"),
            "foreshadow": ("SELECT id,code,title,public_info,author_truth,notes FROM foreshadowing", lambda r: f"{r['code']} {r['title']} {r['public_info']} {r['author_truth']} {r['notes']}"),
            "timeline": ("SELECT id,title,description,location,participants FROM timeline_events", lambda r: f"{r['title']} {r['description']} {r['location']} {r['participants']}"),
            "event": ("SELECT id,title,description,consequence FROM major_events", lambda r: f"{r['title']} {r['description']} {r['consequence']}"),
            "end_state": ("SELECT chapter_number,state,status FROM chapter_states", lambda r: f"{r['chapter_number']}화 {r['status']} {r['state']}"),
            "idea": ("SELECT id,content FROM ideas", lambda r: f"{r['content']}"),
            "chapter": ("SELECT number,title,status FROM chapters", lambda r: f"{r['number']}화 {r['title']} {r['status']}"),
        }
        for cat,(sql,fmt) in source_specs.items():
            if not self._table_exists(sql.split()[3]):
                continue
            for r in self.conn.execute(sql):
                keys=r.keys()
                key = r['chapter_number'] if 'chapter_number' in keys else (r['id'] if 'id' in keys else f"{cat}:{len(self.conn.execute('SELECT 1 FROM search_documents').fetchall())}")
                self.conn.execute("INSERT INTO search_documents(category,ref_key,content,updated_at) VALUES(?,?,?,?)",(cat,str(key),fmt(r),now()))
        self.conn.commit()
        try:
            self.conn.execute("INSERT INTO search_fts(search_fts) VALUES('rebuild')")
            self.conn.commit()
        except Exception:
            pass

    def _table_exists(self, name):
        return self.conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=?",(name,)).fetchone() is not None

    def search(self,q,limit=50):
        """FTS5 우선 검색. 한국어/특수어 등 MATCH가 실패하면 LIKE로 안전하게 fallback."""
        import re
        q=(q or '').strip()
        if not q: return []
        tokens=[x for x in re.findall(r"[^\s\W_]{1,}", q) if x not in {"써줘","알려줘","뭐야","해줘","정리해","현재"}]
        if not tokens: tokens=[q]
        out=[]; seen=set()
        try:
            if int(self.conn.execute("SELECT COUNT(*) FROM search_documents").fetchone()[0]) == 0:
                self.rebuild_search_index()
        except Exception:
            pass
        # FTS5: 각 토큰을 OR로 검색해 관련성이 높은 순으로 반환.
        try:
            terms=[]
            for t in tokens:
                safe=t.replace('"','""')
                terms.append(f'"{safe}"')
            match=' OR '.join(terms)
            rows=self.conn.execute("""SELECT d.category,d.ref_key,d.content,bm25(search_fts) AS score
                                      FROM search_fts
                                      JOIN search_documents d ON d.doc_id=search_fts.rowid
                                      WHERE search_fts MATCH ?
                                      ORDER BY score LIMIT ?""",(match,int(limit))).fetchall()
            for r in rows:
                key=(r['category'],r['ref_key'])
                if key in seen: continue
                seen.add(key); out.append((r['category'], {'ref_key':r['ref_key'],'content':r['content']}))
                if len(out)>=int(limit): return out
        except Exception:
            pass
        # 색인이 비어 있거나 FTS가 특정 입력을 해석하지 못하면 기존 LIKE 검색을 사용한다.
        specs=[("작품","meta",["key","value"]),("구간별 상세 스토리","story_sections",["start_chapter","end_chapter","content"]),("세부 스토리","story_subsections",["start_chapter","end_chapter","title","content"]),("화별 스토리","chapter_stories",["chapter_number","title","content"]),("인물","characters",["name","role","profile","personality","goal","secret"]),("세계관","world_entities",["name","category","description","rules"]),("복선","foreshadowing",["code","title","public_info","author_truth","notes"]),("시간축","timeline_events",["chapter_number","story_date","title","description","location"]),("핵심 사건","major_events",["title","description","consequence"]),("연속성 기록","chapter_states",["chapter_number","state","status"]),("아이디어","ideas",["content"]),("설정","section_contents",["section","content"])]
        for token in tokens:
            like=f"%{token}%"
            for label,table,cols in specs:
                where=" OR ".join([f"CAST({c} AS TEXT) LIKE ?" for c in cols])
                try:
                    if not self._table_exists(table):
                        continue
                    rows=self.conn.execute(f"SELECT * FROM {table} WHERE {where} LIMIT ?",[like]*len(cols)+[int(limit)]).fetchall()
                except Exception: rows=[]
                for r in rows:
                    key=(table,tuple(r))
                    if key in seen: continue
                    seen.add(key); out.append((label,dict(r)))
                    if len(out)>=int(limit): return out
        return out
