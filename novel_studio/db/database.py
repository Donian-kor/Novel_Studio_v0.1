from __future__ import annotations
import sqlite3
from pathlib import Path
from novel_studio.core.helpers import now

class Database:
    def __init__(self, path: Path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.init_schema()
    def init_schema(self):
        self.conn.executescript('''
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS chapters(number INTEGER PRIMARY KEY,title TEXT DEFAULT '',status TEXT DEFAULT '미작성',word_count INTEGER DEFAULT 0,target_chars INTEGER DEFAULT 5000,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS parts(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,part_number INTEGER,start_chapter INTEGER,end_chapter INTEGER,objective TEXT,content TEXT,status TEXT DEFAULT '계획',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS story_sections(id INTEGER PRIMARY KEY AUTOINCREMENT,start_chapter INTEGER,end_chapter INTEGER,status TEXT DEFAULT '미생성',objective TEXT,content TEXT,snapshot TEXT,updated_at TEXT,UNIQUE(start_chapter,end_chapter));
        CREATE TABLE IF NOT EXISTS chapter_plans(chapter_number INTEGER PRIMARY KEY,title TEXT,content TEXT,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS characters(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE,role TEXT,profile TEXT,personality TEXT,speech_style TEXT,goal TEXT,secret TEXT,arc TEXT,status TEXT DEFAULT '확정',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS character_states(id INTEGER PRIMARY KEY AUTOINCREMENT,character_id INTEGER,chapter_number INTEGER,location TEXT,cultivation TEXT,condition TEXT,injuries TEXT,possessions TEXT,emotions TEXT,knows TEXT,does_not_know TEXT,notes TEXT,updated_at TEXT,UNIQUE(character_id,chapter_number),FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS relationships(id INTEGER PRIMARY KEY AUTOINCREMENT,a INTEGER,b INTEGER,relation TEXT,intensity TEXT,status TEXT,history TEXT,updated_at TEXT,UNIQUE(a,b));
        CREATE TABLE IF NOT EXISTS world_entities(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE,category TEXT,description TEXT,rules TEXT,status TEXT DEFAULT '확정',updated_at TEXT);
        CREATE TABLE IF NOT EXISTS timelines(id INTEGER PRIMARY KEY AUTOINCREMENT,chapter_number INTEGER,story_date TEXT,title TEXT,description TEXT,location TEXT,participants TEXT,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS foreshadowing(id INTEGER PRIMARY KEY AUTOINCREMENT,code TEXT UNIQUE,title TEXT,first_chapter INTEGER,latest_chapter INTEGER,reveal_chapter INTEGER,status TEXT,public_info TEXT,author_truth TEXT,related_characters TEXT,notes TEXT,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS core_contract(id INTEGER PRIMARY KEY CHECK(id=1),content TEXT,locked INTEGER DEFAULT 0,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS summaries(chapter_number INTEGER PRIMARY KEY,summary TEXT,state_snapshot TEXT,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS snapshots(scope TEXT PRIMARY KEY,content TEXT,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS continuity_checks(id INTEGER PRIMARY KEY AUTOINCREMENT,chapter_number INTEGER,severity TEXT,category TEXT,message TEXT,evidence TEXT,status TEXT DEFAULT '미해결',created_at TEXT);
        CREATE TABLE IF NOT EXISTS ai_jobs(id INTEGER PRIMARY KEY AUTOINCREMENT,job_type TEXT,target TEXT,status TEXT,model TEXT,prompt_chars INTEGER DEFAULT 0,output_chars INTEGER DEFAULT 0,started_at TEXT,completed_at TEXT,error TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS ideas(id INTEGER PRIMARY KEY AUTOINCREMENT,content TEXT,created_at TEXT,used INTEGER DEFAULT 0);
        ''')
        self.conn.commit()
    def set_meta(self,k,v): self.conn.execute("INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(k,v)); self.conn.commit()
    def get_meta(self,k,default=''):
        r=self.conn.execute("SELECT value FROM meta WHERE key=?",(k,)).fetchone(); return str(r['value']) if r else default
    def upsert_chapter(self,n,target_chars=5000): self.conn.execute("INSERT INTO chapters(number,target_chars,updated_at) VALUES(?,?,?) ON CONFLICT(number) DO UPDATE SET target_chars=excluded.target_chars,updated_at=excluded.updated_at",(n,target_chars,now())); self.conn.commit()
    def chapter(self,n): return self.conn.execute("SELECT * FROM chapters WHERE number=?",(n,)).fetchone()
    def chapters(self): return self.conn.execute("SELECT * FROM chapters ORDER BY number").fetchall()
    def set_chapter_meta(self,n,title,status,count,target): self.upsert_chapter(n,target); self.conn.execute("UPDATE chapters SET title=?,status=?,word_count=?,target_chars=?,updated_at=? WHERE number=?",(title,status,count,target,now(),n)); self.conn.commit()
    def set_chapter_plan(self,n,title,content): self.conn.execute("INSERT INTO chapter_plans(chapter_number,title,content,updated_at) VALUES(?,?,?,?) ON CONFLICT(chapter_number) DO UPDATE SET title=excluded.title,content=excluded.content,updated_at=excluded.updated_at",(n,title,content,now())); self.conn.commit()
    def chapter_plan(self,n): return self.conn.execute("SELECT * FROM chapter_plans WHERE chapter_number=?",(n,)).fetchone()
    def save_contract(self,content,locked): self.conn.execute("INSERT INTO core_contract(id,content,locked,updated_at) VALUES(1,?,?,?) ON CONFLICT(id) DO UPDATE SET content=excluded.content,locked=excluded.locked,updated_at=excluded.updated_at",(content,int(locked),now())); self.conn.commit()
    def contract(self): return self.conn.execute("SELECT * FROM core_contract WHERE id=1").fetchone()
    def save_summary(self,n,summary,state=''): self.conn.execute("INSERT INTO summaries(chapter_number,summary,state_snapshot,updated_at) VALUES(?,?,?,?) ON CONFLICT(chapter_number) DO UPDATE SET summary=excluded.summary,state_snapshot=excluded.state_snapshot,updated_at=excluded.updated_at",(n,summary,state,now())); self.conn.commit()
    def summary(self,n): return self.conn.execute("SELECT * FROM summaries WHERE chapter_number=?",(n,)).fetchone()
    def set_snapshot(self,scope,content): self.conn.execute("INSERT INTO snapshots(scope,content,updated_at) VALUES(?,?,?) ON CONFLICT(scope) DO UPDATE SET content=excluded.content,updated_at=excluded.updated_at",(scope,content,now())); self.conn.commit()
    def snapshot(self,scope): return self.conn.execute("SELECT * FROM snapshots WHERE scope=?",(scope,)).fetchone()
    def upsert_story_section(self,start,end,status,objective,content,snapshot): self.conn.execute("INSERT INTO story_sections(start_chapter,end_chapter,status,objective,content,snapshot,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(start_chapter,end_chapter) DO UPDATE SET status=excluded.status,objective=excluded.objective,content=excluded.content,snapshot=excluded.snapshot,updated_at=excluded.updated_at",(start,end,status,objective,content,snapshot,now())); self.conn.commit()
    def sections(self): return self.conn.execute("SELECT * FROM story_sections ORDER BY start_chapter").fetchall()
    def characters(self): return self.conn.execute("SELECT * FROM characters ORDER BY id").fetchall()
    def character(self,n): return self.conn.execute("SELECT * FROM characters WHERE name=?",(n,)).fetchone()
    def save_character(self,data):
        self.conn.execute("INSERT INTO characters(name,role,profile,personality,speech_style,goal,secret,arc,status,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET role=excluded.role,profile=excluded.profile,personality=excluded.personality,speech_style=excluded.speech_style,goal=excluded.goal,secret=excluded.secret,arc=excluded.arc,status=excluded.status,updated_at=excluded.updated_at",(data['name'],data.get('role',''),data.get('profile',''),data.get('personality',''),data.get('speech_style',''),data.get('goal',''),data.get('secret',''),data.get('arc',''),data.get('status','확정'),now())); self.conn.commit()
    def worlds(self): return self.conn.execute("SELECT * FROM world_entities ORDER BY id").fetchall()
    def save_world(self,data): self.conn.execute("INSERT INTO world_entities(name,category,description,rules,status,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET category=excluded.category,description=excluded.description,rules=excluded.rules,status=excluded.status,updated_at=excluded.updated_at",(data['name'],data.get('category',''),data.get('description',''),data.get('rules',''),data.get('status','확정'),now())); self.conn.commit()
    def foreshadows(self): return self.conn.execute("SELECT * FROM foreshadowing ORDER BY id").fetchall()
    def save_foreshadow(self,data): self.conn.execute("INSERT INTO foreshadowing(code,title,first_chapter,latest_chapter,reveal_chapter,status,public_info,author_truth,related_characters,notes,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(code) DO UPDATE SET title=excluded.title,first_chapter=excluded.first_chapter,latest_chapter=excluded.latest_chapter,reveal_chapter=excluded.reveal_chapter,status=excluded.status,public_info=excluded.public_info,author_truth=excluded.author_truth,related_characters=excluded.related_characters,notes=excluded.notes,updated_at=excluded.updated_at",(data['code'],data.get('title',''),data.get('first_chapter'),data.get('latest_chapter'),data.get('reveal_chapter'),data.get('status','활성'),data.get('public_info',''),data.get('author_truth',''),data.get('related_characters',''),data.get('notes',''),now())); self.conn.commit()
    def timelines(self): return self.conn.execute("SELECT * FROM timelines ORDER BY COALESCE(chapter_number,999999),id").fetchall()
    def save_timeline(self,data): self.conn.execute("INSERT INTO timelines(chapter_number,story_date,title,description,location,participants,updated_at) VALUES(?,?,?,?,?,?,?)",(data.get('chapter_number'),data.get('story_date',''),data.get('title',''),data.get('description',''),data.get('location',''),data.get('participants',''),now())); self.conn.commit()
    def add_idea(self,content,used=0): self.conn.execute("INSERT INTO ideas(content,created_at,used) VALUES(?,?,?)",(content,now(),used)); self.conn.commit()
    def recent_ideas(self,limit=8): return self.conn.execute("SELECT content FROM ideas ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
    def close(self): self.conn.close()
