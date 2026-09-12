from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime

def now():
    return datetime.now().isoformat(timespec="seconds")

class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._schema()

    def close(self):
        try: self.conn.close()
        except Exception: pass

    def _schema(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
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
        CREATE TABLE IF NOT EXISTS snapshots(scope TEXT PRIMARY KEY,content TEXT DEFAULT '',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS continuity_checks(id INTEGER PRIMARY KEY AUTOINCREMENT,chapter_number INTEGER,severity TEXT,category TEXT,message TEXT,evidence TEXT DEFAULT '',status TEXT DEFAULT '미해결',created_at TEXT);
        CREATE TABLE IF NOT EXISTS ai_jobs(id INTEGER PRIMARY KEY AUTOINCREMENT,job_type TEXT,target TEXT,status TEXT,provider TEXT DEFAULT '',model TEXT DEFAULT '',prompt_chars INTEGER DEFAULT 0,output_chars INTEGER DEFAULT 0,started_at TEXT,completed_at TEXT,error TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS chat_messages(id INTEGER PRIMARY KEY AUTOINCREMENT,role TEXT,content TEXT,chapter_number INTEGER,created_at TEXT);
        CREATE TABLE IF NOT EXISTS ideas(id INTEGER PRIMARY KEY AUTOINCREMENT,content TEXT,created_at TEXT,used INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS plans(id INTEGER PRIMARY KEY CHECK(id=1),content TEXT DEFAULT '',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS contract(id INTEGER PRIMARY KEY CHECK(id=1),content TEXT DEFAULT '',locked INTEGER DEFAULT 0,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS section_contents(section TEXT PRIMARY KEY,content TEXT DEFAULT '',status TEXT DEFAULT '초안',updated_at TEXT);
        """)
        self.conn.commit()

    def execute(self, sql, args=()):
        cur = self.conn.execute(sql, args); self.conn.commit(); return cur

    def get_meta(self, key, default=""):
        r=self.conn.execute("SELECT value FROM meta WHERE key=?",(key,)).fetchone(); return r["value"] if r else default
    def set_meta(self,key,value): self.execute("INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(key,str(value)))

    def ensure_chapters(self,total,target):
        for n in range(1,int(total)+1):
            self.conn.execute("INSERT OR IGNORE INTO chapters(number,title,target_chars,updated_at) VALUES(?,?,?,?)",(n,f"{n}화",int(target),now()))
        self.conn.commit()
    def chapters(self): return self.conn.execute("SELECT * FROM chapters ORDER BY number").fetchall()
    def chapter(self,n): return self.conn.execute("SELECT * FROM chapters WHERE number=?",(n,)).fetchone()
    def set_chapter_meta(self,n,title,status,count,count_spaces,target): self.execute("""INSERT INTO chapters(number,title,status,char_count,char_count_spaces,target_chars,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(number) DO UPDATE SET title=excluded.title,status=excluded.status,char_count=excluded.char_count,char_count_spaces=excluded.char_count_spaces,target_chars=excluded.target_chars,updated_at=excluded.updated_at""",(n,title,status,count,count_spaces,target,now()))

    def get_plan(self):
        r=self.conn.execute("SELECT content FROM plans WHERE id=1").fetchone(); return r["content"] if r else ""
    def save_plan(self,content): self.execute("INSERT INTO plans(id,content,updated_at) VALUES(1,?,?) ON CONFLICT(id) DO UPDATE SET content=excluded.content,updated_at=excluded.updated_at",(content,now()))
    def get_contract(self): return self.conn.execute("SELECT * FROM contract WHERE id=1").fetchone()
    def save_contract(self,content,locked=False): self.execute("INSERT INTO contract(id,content,locked,updated_at) VALUES(1,?,?,?) ON CONFLICT(id) DO UPDATE SET content=excluded.content,locked=excluded.locked,updated_at=excluded.updated_at",(content,int(bool(locked)),now()))

    def section_content(self,s):
        r=self.conn.execute("SELECT content FROM section_contents WHERE section=?",(s,)).fetchone(); return r["content"] if r else ""
    def save_section_content(self,s,content,status="초안"): self.execute("INSERT INTO section_contents(section,content,status,updated_at) VALUES(?,?,?,?) ON CONFLICT(section) DO UPDATE SET content=excluded.content,status=excluded.status,updated_at=excluded.updated_at",(s,content,status,now()))

    def chapter_plans(self): return self.conn.execute("SELECT * FROM chapter_plans ORDER BY chapter_number").fetchall()
    def chapter_plan(self,n): return self.conn.execute("SELECT * FROM chapter_plans WHERE chapter_number=?",(n,)).fetchone()
    def save_chapter_plan(self,n,title,content,status="초안"): self.execute("INSERT INTO chapter_plans(chapter_number,title,content,status,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(chapter_number) DO UPDATE SET title=excluded.title,content=excluded.content,status=excluded.status,updated_at=excluded.updated_at",(n,title,content,status,now()))

    def sections(self): return self.conn.execute("SELECT * FROM story_sections ORDER BY start_chapter").fetchall()
    def section(self,s,e): return self.conn.execute("SELECT * FROM story_sections WHERE start_chapter=? AND end_chapter=?",(s,e)).fetchone()
    def save_section(self,s,e,status,content,snapshot=""): self.execute("INSERT INTO story_sections(start_chapter,end_chapter,status,content,snapshot,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(start_chapter,end_chapter) DO UPDATE SET status=excluded.status,content=excluded.content,snapshot=excluded.snapshot,updated_at=excluded.updated_at",(s,e,status,content,snapshot,now()))

    def characters(self): return self.conn.execute("SELECT * FROM characters ORDER BY id").fetchall()
    def save_character(self,d): self.execute("""INSERT INTO characters(name,role,profile,personality,speech_style,goal,secret,arc,status,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET role=excluded.role,profile=excluded.profile,personality=excluded.personality,speech_style=excluded.speech_style,goal=excluded.goal,secret=excluded.secret,arc=excluded.arc,status=excluded.status,updated_at=excluded.updated_at""",(d.get("name",""),d.get("role",""),d.get("profile",""),d.get("personality",""),d.get("speech_style",""),d.get("goal",""),d.get("secret",""),d.get("arc",""),d.get("status","초안"),now()))
    def world_entities(self): return self.conn.execute("SELECT * FROM world_entities ORDER BY id").fetchall()
    def save_world(self,d): self.execute("INSERT INTO world_entities(name,category,description,rules,status,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET category=excluded.category,description=excluded.description,rules=excluded.rules,status=excluded.status,updated_at=excluded.updated_at",(d.get("name",""),d.get("category",""),d.get("description",""),d.get("rules",""),d.get("status","초안"),now()))
    def foreshadows(self): return self.conn.execute("SELECT * FROM foreshadowing ORDER BY id").fetchall()
    def save_foreshadow(self,d): self.execute("INSERT INTO foreshadowing(code,title,first_chapter,latest_chapter,reveal_chapter,status,public_info,author_truth,related_characters,notes,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(code) DO UPDATE SET title=excluded.title,first_chapter=excluded.first_chapter,latest_chapter=excluded.latest_chapter,reveal_chapter=excluded.reveal_chapter,status=excluded.status,public_info=excluded.public_info,author_truth=excluded.author_truth,related_characters=excluded.related_characters,notes=excluded.notes,updated_at=excluded.updated_at",(d.get("code",""),d.get("title",""),d.get("first_chapter"),d.get("latest_chapter"),d.get("reveal_chapter"),d.get("status","활성"),d.get("public_info",""),d.get("author_truth",""),d.get("related_characters",""),d.get("notes",""),now()))
    def delete_character(self,n): self.execute("DELETE FROM characters WHERE name=?",(n,))
    def delete_world(self,n): self.execute("DELETE FROM world_entities WHERE name=?",(n,))
    def delete_foreshadow(self,c): self.execute("DELETE FROM foreshadowing WHERE code=?",(c,))
    def delete_timeline(self,i): self.execute("DELETE FROM timeline_events WHERE id=?",(i,))
    def delete_major_event(self,t): self.execute("DELETE FROM major_events WHERE title=?",(t,))
    def save_timeline(self,d): self.execute("INSERT INTO timeline_events(chapter_number,story_date,title,description,location,participants,updated_at) VALUES(?,?,?,?,?,?,?)",(d.get("chapter_number"),d.get("story_date",""),d.get("title",""),d.get("description",""),d.get("location",""),d.get("participants",""),now()))
    def save_major_event(self,d): self.execute("INSERT INTO major_events(title,start_chapter,end_chapter,description,consequence,status,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(title) DO UPDATE SET start_chapter=excluded.start_chapter,end_chapter=excluded.end_chapter,description=excluded.description,consequence=excluded.consequence,status=excluded.status,updated_at=excluded.updated_at",(d.get("title",""),d.get("start_chapter"),d.get("end_chapter"),d.get("description",""),d.get("consequence",""),d.get("status","계획"),now()))
    def timeline(self): return self.conn.execute("SELECT * FROM timeline_events ORDER BY COALESCE(chapter_number,999999),id").fetchall()
    def major_events(self): return self.conn.execute("SELECT * FROM major_events ORDER BY COALESCE(start_chapter,999999),id").fetchall()
    def summaries(self): return self.conn.execute("SELECT * FROM summaries ORDER BY chapter_number").fetchall()
    def summary(self,n): return self.conn.execute("SELECT * FROM summaries WHERE chapter_number=?",(n,)).fetchone()
    def save_summary(self,n,summary,state=""): self.execute("INSERT INTO summaries(chapter_number,summary,state_snapshot,updated_at) VALUES(?,?,?,?) ON CONFLICT(chapter_number) DO UPDATE SET summary=excluded.summary,state_snapshot=excluded.state_snapshot,updated_at=excluded.updated_at",(n,summary,state,now()))
    def snapshot(self,scope): return self.conn.execute("SELECT * FROM snapshots WHERE scope=?",(scope,)).fetchone()
    def save_snapshot(self,scope,content): self.execute("INSERT INTO snapshots(scope,content,updated_at) VALUES(?,?,?) ON CONFLICT(scope) DO UPDATE SET content=excluded.content,updated_at=excluded.updated_at",(scope,content,now()))
    def add_idea(self,content): self.execute("INSERT INTO ideas(content,created_at,used) VALUES(?,?,0)",(content,now()))
    def recent_ideas(self,limit=20): return self.conn.execute("SELECT content FROM ideas ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
    def use_idea(self,content): self.execute("UPDATE ideas SET used=0"); self.execute("UPDATE ideas SET used=1 WHERE content=?",(content,))
    def add_chat(self,role,content,chapter=None): self.execute("INSERT INTO chat_messages(role,content,chapter_number,created_at) VALUES(?,?,?,?)",(role,content,chapter,now()))
    def chat_messages(self): return self.conn.execute("SELECT * FROM chat_messages ORDER BY id").fetchall()
    def continuity(self): return self.conn.execute("SELECT * FROM continuity_checks ORDER BY id DESC").fetchall()
    def add_continuity(self,ch,severity,category,message,evidence=""): self.execute("INSERT INTO continuity_checks(chapter_number,severity,category,message,evidence,created_at) VALUES(?,?,?,?,?,?)",(ch,severity,category,message,evidence,now()))
    def start_job(self,typ,target,provider,model):
        c=self.conn.execute("INSERT INTO ai_jobs(job_type,target,status,provider,model,started_at) VALUES(?,?,?,?,?,?)",(typ,target,"실행중",provider,model,now())); self.conn.commit(); return c.lastrowid
    def finish_job(self,jid,status,error=""): self.execute("UPDATE ai_jobs SET status=?,completed_at=?,error=? WHERE id=?",(status,now(),error,jid))
    def search(self,q,limit=50):
        import re
        tokens=[x for x in re.findall(r"[^\s\W_]{2,}", q) if x not in {"써줘","알려줘","뭐야","해줘","정리해","현재"}]
        if not tokens: tokens=[q.strip()] if q.strip() else []
        out=[]; seen=set()
        specs=[("작품","meta",["key","value"]),("화별 플롯","chapter_plans",["chapter_number","title","content"]),("인물","characters",["name","role","profile","personality","goal","secret"]),("세계관","world_entities",["name","category","description","rules"]),("복선","foreshadowing",["code","title","public_info","author_truth","notes"]),("시간축","timeline_events",["chapter_number","story_date","title","description","location"]),("핵심 사건","major_events",["title","description","consequence"]),("요약","summaries",["chapter_number","summary","state_snapshot"]),("아이디어","ideas",["content"]),("설정","section_contents",["section","content"])]
        for token in tokens:
            like=f"%{token}%"
            for label,table,cols in specs:
                where=" OR ".join([f"CAST({c} AS TEXT) LIKE ?" for c in cols])
                try: rows=self.conn.execute(f"SELECT * FROM {table} WHERE {where} LIMIT ?",[like]*len(cols)+[limit]).fetchall()
                except Exception: rows=[]
                for r in rows:
                    key=(table,tuple(r));
                    if key not in seen: seen.add(key); out.append((label,dict(r)))
                    if len(out)>=limit:return out
        return out

