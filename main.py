from __future__ import annotations

import json
import re
import sqlite3
import sys
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QLineEdit,
    QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton,
    QSpinBox, QSplitter, QStatusBar, QTabWidget, QVBoxLayout, QWidget
)

APP_NAME = "Novel Studio v0.3"
DEFAULT_BASE_URL = "http://localhost:1234"
DEFAULT_CHUNK_SIZE = 5


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def count_chars(text: str) -> int:
    return len(text.replace("\r", "").replace("\n", ""))


def trim_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def safe_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip() or "unnamed"


@dataclass
class ProjectPaths:
    root: Path

    @property
    def db(self) -> Path:
        return self.root / "novel.db"

    @property
    def chapters(self) -> Path:
        return self.root / "chapters"

    @property
    def plans(self) -> Path:
        return self.root / "plans"

    @property
    def memory(self) -> Path:
        return self.root / "memory"

    @property
    def snapshots(self) -> Path:
        return self.root / "snapshots"

    @property
    def backups(self) -> Path:
        return self.root / "backups"

    @property
    def exports(self) -> Path:
        return self.root / "exports"

    @property
    def temp(self) -> Path:
        return self.root / "temp"

    @property
    def settings(self) -> Path:
        return self.root / "project.json"


class Database:
    def __init__(self, path: Path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_schema()

    def init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS project_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number INTEGER UNIQUE NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '미작성',
                file_path TEXT NOT NULL,
                word_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS plots (
                chapter_number INTEGER PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS arcs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                part_number INTEGER NOT NULL DEFAULT 1,
                start_chapter INTEGER NOT NULL,
                end_chapter INTEGER NOT NULL,
                objective TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '계획',
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_chapter INTEGER NOT NULL,
                end_chapter INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT '미생성',
                objective TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL DEFAULT '',
                snapshot TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(start_chapter, end_chapter)
            );
            CREATE TABLE IF NOT EXISTS chunk_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_chapter INTEGER NOT NULL,
                end_chapter INTEGER NOT NULL,
                status TEXT NOT NULL,
                message TEXT NOT NULL DEFAULT '',
                started_at TEXT NOT NULL,
                completed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL DEFAULT '',
                profile TEXT NOT NULL DEFAULT '',
                personality TEXT NOT NULL DEFAULT '',
                speech_style TEXT NOT NULL DEFAULT '',
                goal TEXT NOT NULL DEFAULT '',
                secret TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS character_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                chapter_number INTEGER NOT NULL,
                location TEXT NOT NULL DEFAULT '',
                cultivation TEXT NOT NULL DEFAULT '',
                condition TEXT NOT NULL DEFAULT '',
                injuries TEXT NOT NULL DEFAULT '',
                possessions TEXT NOT NULL DEFAULT '',
                emotions TEXT NOT NULL DEFAULT '',
                knows TEXT NOT NULL DEFAULT '',
                does_not_know TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL,
                UNIQUE(character_id, chapter_number),
                FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_a INTEGER NOT NULL,
                character_b INTEGER NOT NULL,
                relation TEXT NOT NULL DEFAULT '',
                intensity TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '',
                history TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL,
                UNIQUE(character_a, character_b),
                FOREIGN KEY(character_a) REFERENCES characters(id) ON DELETE CASCADE,
                FOREIGN KEY(character_b) REFERENCES characters(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS world_entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                rules TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '확정',
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS timeline_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_number INTEGER,
                story_date TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                location TEXT NOT NULL DEFAULT '',
                participants TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS foreshadowing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                first_chapter INTEGER,
                latest_chapter INTEGER,
                planned_reveal_chapter INTEGER,
                status TEXT NOT NULL DEFAULT '활성',
                public_info TEXT NOT NULL DEFAULT '',
                author_truth TEXT NOT NULL DEFAULT '',
                related_characters TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS thread_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT '진행중',
                first_chapter INTEGER,
                latest_chapter INTEGER,
                description TEXT NOT NULL DEFAULT '',
                next_step TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_number INTEGER UNIQUE NOT NULL,
                summary TEXT NOT NULL DEFAULT '',
                state_snapshot TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS state_snapshots (
                chapter_number INTEGER PRIMARY KEY,
                content TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS continuity_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_number INTEGER NOT NULL,
                severity TEXT NOT NULL,
                category TEXT NOT NULL,
                message TEXT NOT NULL,
                evidence TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '미해결',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS plan_contract (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                content TEXT NOT NULL DEFAULT '',
                locked INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ai_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_type TEXT NOT NULL,
                target TEXT NOT NULL DEFAULT '',
                model TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL,
                prompt_chars INTEGER NOT NULL DEFAULT 0,
                output_chars INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                error TEXT NOT NULL DEFAULT ''
            );
            """
        )
        self.conn.commit()

    def set_meta(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO project_meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        self.conn.commit()

    def get_meta(self, key: str, default: str = "") -> str:
        row = self.conn.execute("SELECT value FROM project_meta WHERE key=?", (key,)).fetchone()
        return str(row["value"]) if row else default

    def ensure_chapter(self, number: int) -> None:
        row = self.conn.execute("SELECT 1 FROM chapters WHERE number=?", (number,)).fetchone()
        if not row:
            self.conn.execute(
                "INSERT INTO chapters(number,file_path,created_at,updated_at) VALUES(?,?,?,?)",
                (number, f"chapters/{number:03d}.txt", now(), now()),
            )
            self.conn.commit()

    def ensure_chapters_range(self, start: int, end: int) -> None:
        for n in range(start, end + 1):
            self.ensure_chapter(n)

    def chapter_rows(self):
        return self.conn.execute("SELECT * FROM chapters ORDER BY number").fetchall()

    def chapter(self, number: int):
        return self.conn.execute("SELECT * FROM chapters WHERE number=?", (number,)).fetchone()

    def update_chapter(self, number: int, title: str, status: str, word_count: int) -> None:
        self.conn.execute(
            "UPDATE chapters SET title=?,status=?,word_count=?,updated_at=? WHERE number=?",
            (title, status, word_count, now(), number),
        )
        self.conn.commit()

    def save_plot(self, chapter_number: int, title: str, content: str) -> None:
        self.conn.execute(
            "INSERT INTO plots(chapter_number,title,content,updated_at) VALUES(?,?,?,?) "
            "ON CONFLICT(chapter_number) DO UPDATE SET title=excluded.title,content=excluded.content,updated_at=excluded.updated_at",
            (chapter_number, title, content, now()),
        )
        self.conn.commit()

    def get_plot(self, chapter_number: int):
        return self.conn.execute("SELECT * FROM plots WHERE chapter_number=?", (chapter_number,)).fetchone()

    def save_chunk(self, start: int, end: int, status: str, objective: str, content: str, snapshot: str = "") -> None:
        self.conn.execute(
            "INSERT INTO chunks(start_chapter,end_chapter,status,objective,content,snapshot,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(start_chapter,end_chapter) DO UPDATE SET status=excluded.status,objective=excluded.objective,content=excluded.content,snapshot=excluded.snapshot,updated_at=excluded.updated_at",
            (start, end, status, objective, content, snapshot, now(), now()),
        )
        self.conn.commit()

    def get_chunk(self, start: int, end: int):
        return self.conn.execute("SELECT * FROM chunks WHERE start_chapter=? AND end_chapter=?", (start, end)).fetchone()

    def chunks(self):
        return self.conn.execute("SELECT * FROM chunks ORDER BY start_chapter").fetchall()

    def previous_chunk(self, start: int):
        return self.conn.execute("SELECT * FROM chunks WHERE end_chapter<? ORDER BY end_chapter DESC LIMIT 1", (start,)).fetchone()

    def save_contract(self, content: str, locked: bool) -> None:
        self.conn.execute(
            "INSERT INTO plan_contract(id,content,locked,updated_at) VALUES(1,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET content=excluded.content,locked=excluded.locked,updated_at=excluded.updated_at",
            (content, int(locked), now()),
        )
        self.conn.commit()

    def contract(self):
        return self.conn.execute("SELECT * FROM plan_contract WHERE id=1").fetchone()

    def save_state_snapshot(self, chapter: int, content: str) -> None:
        self.conn.execute(
            "INSERT INTO state_snapshots(chapter_number,content,updated_at) VALUES(?,?,?) ON CONFLICT(chapter_number) DO UPDATE SET content=excluded.content,updated_at=excluded.updated_at",
            (chapter, content, now()),
        )
        self.conn.commit()

    def state_snapshot(self, chapter: int):
        return self.conn.execute("SELECT * FROM state_snapshots WHERE chapter_number=?", (chapter,)).fetchone()

    def save_summary(self, chapter: int, summary: str, state: str) -> None:
        self.conn.execute(
            "INSERT INTO summaries(chapter_number,summary,state_snapshot,created_at,updated_at) VALUES(?,?,?,?,?) "
            "ON CONFLICT(chapter_number) DO UPDATE SET summary=excluded.summary,state_snapshot=excluded.state_snapshot,updated_at=excluded.updated_at",
            (chapter, summary, state, now(), now()),
        )
        self.conn.commit()

    def recent_summaries(self, before_chapter: int, limit: int = 4):
        return self.conn.execute(
            "SELECT * FROM summaries WHERE chapter_number<? ORDER BY chapter_number DESC LIMIT ?",
            (before_chapter, limit),
        ).fetchall()

    def add_ai_job(self, job_type: str, target: str, model: str, prompt_chars: int) -> int:
        cur = self.conn.execute(
            "INSERT INTO ai_jobs(job_type,target,model,status,prompt_chars,created_at) VALUES(?,?,?,?,?,?)",
            (job_type, target, model, "진행중", prompt_chars, now()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def finish_ai_job(self, job_id: int, status: str, output_chars: int = 0, error: str = "") -> None:
        self.conn.execute(
            "UPDATE ai_jobs SET status=?,output_chars=?,completed_at=?,error=? WHERE id=?",
            (status, output_chars, now(), error, job_id),
        )
        self.conn.commit()

    def upsert_character(self, data: dict) -> int:
        self.conn.execute(
            "INSERT INTO characters(name,role,profile,personality,speech_style,goal,secret,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(name) DO UPDATE SET role=excluded.role,profile=excluded.profile,personality=excluded.personality,speech_style=excluded.speech_style,goal=excluded.goal,secret=excluded.secret,updated_at=excluded.updated_at",
            (data["name"], data.get("role", ""), data.get("profile", ""), data.get("personality", ""), data.get("speech_style", ""), data.get("goal", ""), data.get("secret", ""), now(), now()),
        )
        row = self.conn.execute("SELECT id FROM characters WHERE name=?", (data["name"],)).fetchone()
        self.conn.commit()
        return int(row["id"])

    def characters(self):
        return self.conn.execute("SELECT * FROM characters ORDER BY name").fetchall()

    def character(self, char_id: int):
        return self.conn.execute("SELECT * FROM characters WHERE id=?", (char_id,)).fetchone()

    def save_character_state(self, data: dict) -> None:
        self.conn.execute(
            "INSERT INTO character_states(character_id,chapter_number,location,cultivation,condition,injuries,possessions,emotions,knows,does_not_know,notes,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(character_id,chapter_number) DO UPDATE SET location=excluded.location,cultivation=excluded.cultivation,condition=excluded.condition,injuries=excluded.injuries,possessions=excluded.possessions,emotions=excluded.emotions,knows=excluded.knows,does_not_know=excluded.does_not_know,notes=excluded.notes,updated_at=excluded.updated_at",
            (data["character_id"], data["chapter_number"], data.get("location", ""), data.get("cultivation", ""), data.get("condition", ""), data.get("injuries", ""), data.get("possessions", ""), data.get("emotions", ""), data.get("knows", ""), data.get("does_not_know", ""), data.get("notes", ""), now()),
        )
        self.conn.commit()

    def character_state(self, char_id: int, chapter: int):
        return self.conn.execute("SELECT * FROM character_states WHERE character_id=? AND chapter_number=?", (char_id, chapter)).fetchone()

    def latest_character_state(self, char_id: int, before_chapter: int):
        return self.conn.execute("SELECT * FROM character_states WHERE character_id=? AND chapter_number<? ORDER BY chapter_number DESC LIMIT 1", (char_id, before_chapter)).fetchone()

    def upsert_world(self, data: dict) -> None:
        self.conn.execute(
            "INSERT INTO world_entities(name,category,description,rules,status,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET category=excluded.category,description=excluded.description,rules=excluded.rules,status=excluded.status,updated_at=excluded.updated_at",
            (data["name"], data.get("category", ""), data.get("description", ""), data.get("rules", ""), data.get("status", "확정"), now()),
        )
        self.conn.commit()

    def worlds(self):
        return self.conn.execute("SELECT * FROM world_entities ORDER BY category,name").fetchall()

    def upsert_timeline(self, data: dict) -> None:
        if data.get("id"):
            self.conn.execute(
                "UPDATE timeline_events SET chapter_number=?,story_date=?,title=?,description=?,location=?,participants=?,updated_at=? WHERE id=?",
                (data.get("chapter_number"), data.get("story_date", ""), data.get("title", ""), data.get("description", ""), data.get("location", ""), data.get("participants", ""), now(), data["id"]),
            )
        else:
            self.conn.execute(
                "INSERT INTO timeline_events(chapter_number,story_date,title,description,location,participants,updated_at) VALUES(?,?,?,?,?,?,?)",
                (data.get("chapter_number"), data.get("story_date", ""), data.get("title", ""), data.get("description", ""), data.get("location", ""), data.get("participants", ""), now()),
            )
        self.conn.commit()

    def timeline(self, limit: int = 200):
        return self.conn.execute("SELECT * FROM timeline_events ORDER BY COALESCE(chapter_number,999999), id LIMIT ?", (limit,)).fetchall()

    def upsert_foreshadow(self, data: dict) -> None:
        self.conn.execute(
            "INSERT INTO foreshadowing(code,title,first_chapter,latest_chapter,planned_reveal_chapter,status,public_info,author_truth,related_characters,notes,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(code) DO UPDATE SET title=excluded.title,first_chapter=excluded.first_chapter,latest_chapter=excluded.latest_chapter,planned_reveal_chapter=excluded.planned_reveal_chapter,status=excluded.status,public_info=excluded.public_info,author_truth=excluded.author_truth,related_characters=excluded.related_characters,notes=excluded.notes,updated_at=excluded.updated_at",
            (data["code"], data.get("title", ""), data.get("first_chapter"), data.get("latest_chapter"), data.get("planned_reveal_chapter"), data.get("status", "활성"), data.get("public_info", ""), data.get("author_truth", ""), data.get("related_characters", ""), data.get("notes", ""), now()),
        )
        self.conn.commit()

    def foreshadows(self):
        return self.conn.execute("SELECT * FROM foreshadowing ORDER BY code").fetchall()


class ProjectManager:
    def __init__(self):
        self.paths: Optional[ProjectPaths] = None
        self.db: Optional[Database] = None
        self.settings: dict = {}

    @property
    def active(self) -> bool:
        return self.paths is not None and self.db is not None

    def create(self, root: Path, title: str, genre: str, target_chapters: int, chapter_length: str) -> None:
        root.mkdir(parents=True, exist_ok=True)
        self.paths = ProjectPaths(root)
        for p in (self.paths.chapters, self.paths.plans, self.paths.memory, self.paths.snapshots, self.paths.backups, self.paths.exports, self.paths.temp):
            p.mkdir(parents=True, exist_ok=True)
        self.settings = {
            "title": title,
            "genre": genre,
            "target_chapters": target_chapters,
            "chapter_length": chapter_length,
            "chunk_size": DEFAULT_CHUNK_SIZE,
            "lmstudio_url": DEFAULT_BASE_URL,
            "model": "",
            "created_at": now(),
            "version": APP_NAME,
        }
        self.paths.settings.write_text(json.dumps(self.settings, ensure_ascii=False, indent=2), encoding="utf-8")
        self.db = Database(self.paths.db)
        for k, v in self.settings.items():
            self.db.set_meta(k, str(v))
        self.db.ensure_chapter(1)

    def open(self, root: Path) -> None:
        self.paths = ProjectPaths(root)
        if not self.paths.db.exists():
            raise RuntimeError("선택한 폴더에 novel.db가 없습니다.")
        self.db = Database(self.paths.db)
        if self.paths.settings.exists():
            self.settings = json.loads(self.paths.settings.read_text(encoding="utf-8"))
        else:
            self.settings = {
                "title": self.db.get_meta("title", root.name),
                "genre": self.db.get_meta("genre", ""),
                "target_chapters": int(self.db.get_meta("target_chapters", "500")),
                "chapter_length": self.db.get_meta("chapter_length", "4,000~5,000자"),
                "chunk_size": int(self.db.get_meta("chunk_size", "5")),
                "lmstudio_url": self.db.get_meta("lmstudio_url", DEFAULT_BASE_URL),
                "model": self.db.get_meta("model", ""),
            }
        self.settings.setdefault("chunk_size", 5)
        self.settings.setdefault("lmstudio_url", DEFAULT_BASE_URL)
        self.settings.setdefault("model", "")
        for p in (self.paths.chapters, self.paths.plans, self.paths.memory, self.paths.snapshots, self.paths.backups, self.paths.exports, self.paths.temp):
            p.mkdir(parents=True, exist_ok=True)

    def chapter_path(self, n: int) -> Path:
        assert self.paths
        return self.paths.chapters / f"{n:03d}.txt"

    def load_chapter(self, n: int) -> str:
        p = self.chapter_path(n)
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def save_chapter(self, n: int, text: str, title: str = "") -> None:
        assert self.db
        p = self.chapter_path(n)
        p.write_text(text, encoding="utf-8")
        self.db.ensure_chapter(n)
        self.db.update_chapter(n, title, "확정" if text.strip() else "미작성", count_chars(text))


class LMStudioClient:
    def __init__(self, base_url: str, model: str = ""):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def list_models(self) -> list[str]:
        req = urllib.request.Request(self.base_url + "/v1/models")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [m.get("id", "") for m in data.get("data", []) if m.get("id")]

    def chat(self, system: str, user: str, temperature: float, max_tokens: int) -> str:
        model = self.model
        if not model:
            models = self.list_models()
            if not models:
                raise RuntimeError("LM Studio에서 모델을 찾지 못했습니다.")
            model = models[0]
            self.model = model
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        req = urllib.request.Request(
            self.base_url + "/v1/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=900) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"LM Studio HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"LM Studio 연결 실패: {e.reason}") from e
        choices = result.get("choices") or []
        if not choices:
            raise RuntimeError("AI 응답이 비어 있습니다.")
        content = choices[0].get("message", {}).get("content", "")
        if isinstance(content, list):
            content = "\n".join(str(x.get("text", x)) for x in content)
        return str(content).strip()


class AIWorker(QObject):
    finished = Signal(str, str)
    failed = Signal(str)
    progress = Signal(str)

    def __init__(self, client: LMStudioClient, system: str, user: str, temperature: float, max_tokens: int):
        super().__init__()
        self.client = client
        self.system = system
        self.user = user
        self.temperature = temperature
        self.max_tokens = max_tokens

    def run(self):
        try:
            self.progress.emit("AI 생성 중...")
            result = self.client.chat(self.system, self.user, self.temperature, self.max_tokens)
            self.finished.emit(result, self.client.model)
        except Exception as exc:
            self.failed.emit(str(exc))


WRITER_SYSTEM = """당신은 한국 장편 웹소설 전문 작가다.
기존 확정 설정과 플롯을 임의로 바꾸지 않는다.
장면, 행동, 대화, 감각을 중심으로 쓰고 과도한 요약을 피한다.
AI 특유의 상투적 표현과 반복적인 문장 구조를 피한다.
대사는 위아래로 한 줄씩 띄운다.
요청된 소설 본문만 출력하고 해설이나 자기평가를 출력하지 않는다."""

PLANNER_SYSTEM = """당신은 한국 장편 웹소설 총괄 기획자다.
짧은 아이디어에서 장기적으로 유지 가능한 작품 기획을 설계한다.
작품의 핵심 주제, 주인공 목표, 세계관, 성장선, 대립 구조, 결말을 먼저 확정한다.
전체 화수의 세부사항을 한 번에 억지로 늘리지 말고 상위 구조와 불변 핵심을 명확히 한다."""

CHUNK_SYSTEM = """당신은 장편 웹소설의 5화 단위 청크 플롯 설계자다.
전체 계획과 Plan Contract를 지키면서 지정된 범위의 화만 상세화한다.
각 화는 반드시 다음 형식을 사용한다.

[화 번호/제목]
[목표]
[시작 상황]
[핵심 사건]
[갈등]
[전환점]
[인물 변화]
[세계관 정보]
[복선]
[복선 회수]
[엔딩]
[다음 화 연결]

청크 끝에는 반드시 [CHUNK SNAPSHOT]을 작성한다.
Snapshot에는 주요 사건, 주인공 상태, 주요 인물 변화, 관계 변화, 경지/능력 변화,
위치/시간 변화, 소지품 변화, 활성/신규/회수 복선, 미해결 사건, 다음 청크 필수 연결점을 기록한다."""

SUMMARIZER_SYSTEM = """당신은 장편소설 기억 관리자다.
직전 원고와 관련 상태를 읽고 다음 화 집필에 필요한 정보를 압축한다.
문학적 줄거리 요약과 구조화된 상태 정보를 분리한다.
확정 사실과 추측을 섞지 않는다."""

CHECKER_SYSTEM = """당신은 장편 웹소설 연속성 검수자다.
입력된 자료만 근거로 문제를 찾는다.
시간, 장소, 인물 위치, 경지, 부상, 소지품, 인물의 지식 범위, 사건 순서,
플롯 이탈, 복선 상태를 검사한다.
문제마다 심각도, 근거, 관련 화를 표시한다."""

EDITOR_SYSTEM = """당신은 한국 웹소설 전문 윤문가다.
사건과 설정을 바꾸지 않고 문장과 장면의 품질을 높인다.
반복 표현, 문장 단절, 어색한 대화, 장면 전환, 설명 과잉을 다듬는다."""


class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("새 작품")
        form = QFormLayout(self)
        self.title_edit = QLineEdit("새 소설")
        self.genre_edit = QLineEdit("선협")
        self.folder_edit = QLineEdit(str(Path.home() / "NovelProjects" / "새_소설"))
        self.target_spin = QSpinBox(); self.target_spin.setRange(1, 10000); self.target_spin.setValue(500)
        self.length_edit = QLineEdit("4,000~5,000자")
        browse = QPushButton("찾아보기"); browse.clicked.connect(self.browse)
        folder_row = QHBoxLayout(); folder_row.addWidget(self.folder_edit); folder_row.addWidget(browse)
        form.addRow("작품명", self.title_edit)
        form.addRow("장르", self.genre_edit)
        form.addRow("프로젝트 폴더", folder_row)
        form.addRow("목표 화수", self.target_spin)
        form.addRow("기본 분량", self.length_edit)
        buttons = QHBoxLayout(); ok = QPushButton("생성"); cancel = QPushButton("취소")
        ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject)
        buttons.addWidget(ok); buttons.addWidget(cancel); form.addRow(buttons)

    def browse(self):
        folder = QFileDialog.getExistingDirectory(self, "프로젝트 폴더 선택")
        if folder:
            self.folder_edit.setText(folder)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1600, 950)
        self.pm = ProjectManager()
        self.current_chapter = 1
        self.last_ai_result = ""
        self.ai_thread: Optional[QThread] = None
        self.ai_worker: Optional[AIWorker] = None
        self.batch_active = False
        self.batch_queue: list[tuple[int, int]] = []
        self.batch_mode = ""
        self._build_menu()
        self._build_ui()
        self._set_enabled(False)

    def _build_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("파일")
        for name, slot in (("새 작품", self.create_project), ("작품 열기", self.open_project), ("원고 저장", self.save_current), ("프로젝트 백업", self.backup_project), ("종료", self.close)):
            act = QAction(name, self); act.triggered.connect(slot); file_menu.addAction(act)
        ai_menu = menu.addMenu("AI")
        for name, slot in (("LM Studio 연결 확인", self.test_ai), ("현재 화 기억 업데이트", self.generate_memory_for_current), ("선택 화 연속성 검사", self.verify_current)):
            act = QAction(name, self); act.triggered.connect(slot); ai_menu.addAction(act)

    def _build_ui(self):
        root = QWidget(); root_layout = QVBoxLayout(root)
        self.setCentralWidget(root)
        header = QHBoxLayout(); self.project_label = QLabel("작품을 열어주세요."); self.ai_label = QLabel("AI ● 미연결")
        header.addWidget(self.project_label); header.addStretch(); header.addWidget(self.ai_label); root_layout.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)
        self.chapter_list = QListWidget(); self.chapter_list.currentRowChanged.connect(self.chapter_selected)
        splitter.addWidget(self.chapter_list)

        center = QTabWidget()
        center.addTab(self._build_manuscript_tab(), "원고")
        center.addTab(self._build_planning_tab(), "AI 기획")
        center.addTab(self._build_chunks_tab(), "청크")
        center.addTab(self._build_characters_tab(), "인물")
        center.addTab(self._build_world_tab(), "세계관")
        center.addTab(self._build_timeline_tab(), "시간축")
        center.addTab(self._build_foreshadow_tab(), "복선")
        center.addTab(self._build_continuity_tab(), "연속성")
        splitter.addWidget(center)

        right = QWidget(); rl = QVBoxLayout(right)
        rl.addWidget(QLabel("현재 상태"))
        self.state_panel = QPlainTextEdit(); self.state_panel.setReadOnly(True); rl.addWidget(self.state_panel, 2)
        rl.addWidget(QLabel("AI 작업 로그"))
        self.log = QPlainTextEdit(); self.log.setReadOnly(True); rl.addWidget(self.log, 1)
        splitter.addWidget(right)
        splitter.setSizes([220, 1050, 330])
        root_layout.addWidget(splitter, 1)

        actions = QHBoxLayout()
        for text, slot in (("새 화", self.new_chapter), ("이어쓰기", self.continue_writing), ("AI 윤문", self.edit_current), ("기억 갱신", self.generate_memory_for_current), ("연속성 검사", self.verify_current), ("자동 집필", self.batch_write_dialog), ("저장", self.save_current)):
            b = QPushButton(text); b.clicked.connect(slot); actions.addWidget(b)
        actions.addStretch(); self.count_label = QLabel("0자"); actions.addWidget(self.count_label)
        root_layout.addLayout(actions)
        self.progress = QProgressBar(); self.progress.hide(); root_layout.addWidget(self.progress)
        self.status = QStatusBar(); self.setStatusBar(self.status); self.status.showMessage("준비됨")

    def _build_manuscript_tab(self):
        w = QWidget(); l = QVBoxLayout(w)
        header = QHBoxLayout(); self.chapter_title = QLineEdit(); header.addWidget(QLabel("제목")); header.addWidget(self.chapter_title); l.addLayout(header)
        self.editor = QPlainTextEdit(); self.editor.textChanged.connect(self.update_count); l.addWidget(self.editor, 1)
        return w

    def _build_planning_tab(self):
        w = QWidget(); l = QVBoxLayout(w)
        row = QHBoxLayout(); self.seed_edit = QPlainTextEdit(); self.seed_edit.setPlaceholderText("짧은 아이디어 / Seed")
        l.addWidget(QLabel("아이디어")); l.addWidget(self.seed_edit, 1)
        controls = QHBoxLayout(); self.target_spin = QSpinBox(); self.target_spin.setRange(1, 10000); self.target_spin.setValue(500)
        self.chunk_spin = QSpinBox(); self.chunk_spin.setRange(1, 50); self.chunk_spin.setValue(5)
        controls.addWidget(QLabel("목표 화수")); controls.addWidget(self.target_spin); controls.addWidget(QLabel("청크 크기")); controls.addWidget(self.chunk_spin)
        self.plan_btn = QPushButton("AI 마스터 기획"); self.plan_btn.clicked.connect(self.generate_master_plan); controls.addWidget(self.plan_btn)
        self.contract_btn = QPushButton("AI Contract 추출"); self.contract_btn.clicked.connect(self.extract_contract); controls.addWidget(self.contract_btn)
        l.addLayout(controls)
        self.master_plan = QPlainTextEdit(); l.addWidget(QLabel("Master Plan")); l.addWidget(self.master_plan, 2)
        contract_row = QHBoxLayout(); self.contract_edit = QPlainTextEdit(); self.contract_edit.setPlaceholderText("불변 핵심 계획"); contract_row.addWidget(self.contract_edit, 1)
        self.contract_lock = QCheckBox("잠금")
        self.save_contract_btn = QPushButton("Contract 저장"); self.save_contract_btn.clicked.connect(self.save_contract)
        cr = QVBoxLayout(); cr.addWidget(self.contract_lock); cr.addWidget(self.save_contract_btn); contract_row.addLayout(cr)
        l.addWidget(QLabel("Plan Contract")); l.addLayout(contract_row, 1)
        return w

    def _build_chunks_tab(self):
        w = QWidget(); l = QVBoxLayout(w)
        controls = QHBoxLayout(); self.chunk_list = QListWidget(); self.chunk_list.currentRowChanged.connect(self.chunk_selected)
        self.make_chunk_btn = QPushButton("선택 청크 생성"); self.make_chunk_btn.clicked.connect(self.generate_selected_chunk)
        self.all_chunk_btn = QPushButton("전체 청크 자동 생성"); self.all_chunk_btn.clicked.connect(self.generate_all_chunks)
        self.resume_chunk_btn = QPushButton("중단 지점부터 계속"); self.resume_chunk_btn.clicked.connect(self.resume_chunks)
        for b in (self.make_chunk_btn, self.all_chunk_btn, self.resume_chunk_btn): controls.addWidget(b)
        l.addLayout(controls); l.addWidget(self.chunk_list, 1)
        self.chunk_detail = QPlainTextEdit(); self.chunk_detail.setReadOnly(True); l.addWidget(QLabel("청크 상세 / Snapshot")); l.addWidget(self.chunk_detail, 2)
        return w

    def _build_characters_tab(self):
        w = QWidget(); l = QVBoxLayout(w); split = QSplitter(Qt.Horizontal)
        self.char_list = QListWidget(); self.char_list.currentRowChanged.connect(self.character_selected); split.addWidget(self.char_list)
        form_w = QWidget(); form = QFormLayout(form_w)
        self.char_name = QLineEdit(); self.char_role = QLineEdit(); self.char_profile = QPlainTextEdit(); self.char_personality = QPlainTextEdit(); self.char_speech = QPlainTextEdit(); self.char_goal = QPlainTextEdit(); self.char_secret = QPlainTextEdit()
        for label, widget in (("이름", self.char_name), ("역할", self.char_role), ("기본정보", self.char_profile), ("성격", self.char_personality), ("말투", self.char_speech), ("목표", self.char_goal), ("비밀", self.char_secret)): form.addRow(label, widget)
        btn = QPushButton("인물 저장"); btn.clicked.connect(self.save_character); form.addRow(btn); split.addWidget(form_w); split.setSizes([250, 700]); l.addWidget(split); return w

    def _build_world_tab(self):
        w = QWidget(); l = QVBoxLayout(w); split = QSplitter(Qt.Horizontal)
        self.world_list = QListWidget(); self.world_list.currentRowChanged.connect(self.world_selected); split.addWidget(self.world_list)
        fw = QWidget(); form = QFormLayout(fw)
        self.world_name = QLineEdit(); self.world_category = QLineEdit(); self.world_description = QPlainTextEdit(); self.world_rules = QPlainTextEdit(); self.world_status = QComboBox(); self.world_status.addItems(["확정", "제안", "폐기"])
        form.addRow("이름", self.world_name); form.addRow("분류", self.world_category); form.addRow("설명", self.world_description); form.addRow("규칙/제약", self.world_rules); form.addRow("상태", self.world_status)
        b = QPushButton("세계관 저장"); b.clicked.connect(self.save_world); form.addRow(b); split.addWidget(fw); l.addWidget(split); return w

    def _build_timeline_tab(self):
        w = QWidget(); l = QVBoxLayout(w); split = QSplitter(Qt.Horizontal)
        self.timeline_list = QListWidget(); self.timeline_list.currentRowChanged.connect(self.timeline_selected); split.addWidget(self.timeline_list)
        fw = QWidget(); form = QFormLayout(fw)
        self.tl_chapter = QSpinBox(); self.tl_chapter.setRange(0, 10000); self.tl_date = QLineEdit(); self.tl_title = QLineEdit(); self.tl_desc = QPlainTextEdit(); self.tl_location = QLineEdit(); self.tl_participants = QLineEdit()
        form.addRow("화", self.tl_chapter); form.addRow("스토리 날짜", self.tl_date); form.addRow("사건명", self.tl_title); form.addRow("설명", self.tl_desc); form.addRow("장소", self.tl_location); form.addRow("참여 인물", self.tl_participants)
        b = QPushButton("시간축 저장"); b.clicked.connect(self.save_timeline); form.addRow(b); split.addWidget(fw); l.addWidget(split); return w

    def _build_foreshadow_tab(self):
        w = QWidget(); l = QVBoxLayout(w); split = QSplitter(Qt.Horizontal)
        self.foreshadow_list = QListWidget(); self.foreshadow_list.currentRowChanged.connect(self.foreshadow_selected); split.addWidget(self.foreshadow_list)
        fw = QWidget(); form = QFormLayout(fw)
        self.fs_code = QLineEdit(); self.fs_title = QLineEdit(); self.fs_first = QSpinBox(); self.fs_first.setRange(0, 10000); self.fs_latest = QSpinBox(); self.fs_latest.setRange(0, 10000); self.fs_reveal = QSpinBox(); self.fs_reveal.setRange(0, 10000); self.fs_status = QComboBox(); self.fs_status.addItems(["활성", "암시", "진행중", "부분회수", "완전회수", "폐기"]); self.fs_public = QPlainTextEdit(); self.fs_truth = QPlainTextEdit(); self.fs_related = QLineEdit(); self.fs_notes = QPlainTextEdit()
        form.addRow("ID", self.fs_code); form.addRow("제목", self.fs_title); form.addRow("최초 등장", self.fs_first); form.addRow("최근 등장", self.fs_latest); form.addRow("예정 회수", self.fs_reveal); form.addRow("상태", self.fs_status); form.addRow("독자 공개 정보", self.fs_public); form.addRow("작가 진실", self.fs_truth); form.addRow("관련 인물", self.fs_related); form.addRow("메모", self.fs_notes)
        b = QPushButton("복선 저장"); b.clicked.connect(self.save_foreshadow); form.addRow(b); split.addWidget(fw); l.addWidget(split); return w

    def _build_continuity_tab(self):
        w = QWidget(); l = QVBoxLayout(w)
        self.continuity_result = QPlainTextEdit(); self.continuity_result.setReadOnly(True); l.addWidget(self.continuity_result, 1)
        b = QPushButton("현재 화 연속성 검사"); b.clicked.connect(self.verify_current); l.addWidget(b)
        return w

    def _set_enabled(self, on: bool):
        for name in ("editor", "chapter_title", "seed_edit", "master_plan", "contract_edit", "contract_lock", "save_contract_btn", "plan_btn", "contract_btn", "chunk_spin", "target_spin", "chunk_list", "make_chunk_btn", "all_chunk_btn", "resume_chunk_btn", "char_list", "world_list", "timeline_list", "foreshadow_list"):
            getattr(self, name).setEnabled(on)

    def append_log(self, text: str):
        self.log.appendPlainText(f"[{datetime.now().strftime('%H:%M:%S')}] {text}")

    def create_project(self):
        d = NewProjectDialog(self)
        if d.exec() != QDialog.Accepted: return
        try:
            self.pm.create(Path(d.folder_edit.text()).expanduser(), d.title_edit.text().strip(), d.genre_edit.text().strip(), d.target_spin.value(), d.length_edit.text().strip())
            self.load_project_ui()
        except Exception as e:
            QMessageBox.critical(self, "생성 실패", str(e))

    def open_project(self):
        folder = QFileDialog.getExistingDirectory(self, "프로젝트 폴더 선택")
        if not folder: return
        try:
            self.pm.open(Path(folder)); self.load_project_ui()
        except Exception as e:
            QMessageBox.critical(self, "열기 실패", str(e))

    def load_project_ui(self):
        assert self.pm.active and self.pm.db
        self.project_label.setText(f"작품: {self.pm.settings.get('title', self.pm.paths.root.name)}")
        self.target_spin.setValue(int(self.pm.settings.get("target_chapters", 500)))
        self.chunk_spin.setValue(int(self.pm.settings.get("chunk_size", 5)))
        self.master_plan.setPlainText(self.pm.db.get_meta("master_plan", ""))
        contract = self.pm.db.contract(); self.contract_edit.setPlainText(contract["content"] if contract else ""); self.contract_lock.setChecked(bool(contract and contract["locked"]))
        self.refresh_all()
        self._set_enabled(True)
        self.ai_label.setText("AI ● 미연결")
        if self.chapter_list.count(): self.chapter_list.setCurrentRow(0)
        self.status.showMessage(f"프로젝트 열림: {self.pm.paths.root}")
        self.append_log("프로젝트를 열었습니다.")

    def refresh_all(self):
        self.refresh_chapters(); self.refresh_chunks(); self.refresh_characters(); self.refresh_worlds(); self.refresh_timeline(); self.refresh_foreshadows()

    def refresh_chapters(self):
        assert self.pm.db
        self.chapter_list.blockSignals(True); self.chapter_list.clear()
        rows = self.pm.db.chapter_rows(); existing = {int(r["number"]) for r in rows}; target = self.target_spin.value()
        max_n = min(target, max(30, (max(existing) + 10) if existing else 30))
        for n in range(1, max_n + 1):
            if n not in existing: self.pm.db.ensure_chapter(n)
        for r in self.pm.db.chapter_rows():
            item = QListWidgetItem(f"{int(r['number']):03d}  {r['status']}  {int(r['word_count']):,}자")
            item.setData(Qt.UserRole, int(r["number"])); self.chapter_list.addItem(item)
        self.chapter_list.blockSignals(False)

    def chapter_selected(self, row: int):
        if row < 0 or not self.pm.active: return
        n = int(self.chapter_list.item(row).data(Qt.UserRole)); self.load_chapter(n)

    def load_chapter(self, n: int):
        assert self.pm.db
        self.current_chapter = n
        self.editor.blockSignals(True); self.editor.setPlainText(self.pm.load_chapter(n)); self.editor.blockSignals(False)
        ch = self.pm.db.chapter(n); self.chapter_title.setText(ch["title"] if ch else "")
        self.update_count(); self.update_state_panel()

    def save_current(self):
        if not self.pm.active: return
        self.pm.save_chapter(self.current_chapter, self.editor.toPlainText(), self.chapter_title.text().strip()); self.refresh_chapters(); self.append_log(f"{self.current_chapter}화 저장")

    def new_chapter(self):
        if not self.pm.active: return
        n = self.current_chapter + 1; self.pm.db.ensure_chapter(n); self.refresh_chapters()
        for i in range(self.chapter_list.count()):
            if int(self.chapter_list.item(i).data(Qt.UserRole)) == n: self.chapter_list.setCurrentRow(i); break

    def update_count(self):
        self.count_label.setText(f"{count_chars(self.editor.toPlainText()):,}자")

    def update_state_panel(self):
        if not self.pm.active or not self.pm.db: return
        state = self.pm.db.state_snapshot(self.current_chapter)
        lines = [f"현재 화: {self.current_chapter}화", f"제목: {self.chapter_title.text()}"]
        if state: lines += ["", "[기억 Snapshot]", state["content"]]
        prev = self.pm.db.previous_chunk(self.current_chapter + 1)
        if prev: lines += ["", f"[최근 청크] {prev['start_chapter']}~{prev['end_chapter']}화", prev["snapshot"][:2500]]
        self.state_panel.setPlainText("\n".join(lines))

    def save_contract(self):
        assert self.pm.db
        self.pm.db.save_contract(self.contract_edit.toPlainText(), self.contract_lock.isChecked()); self.append_log("Plan Contract 저장")

    def test_ai(self):
        if not self.pm.active: return
        try:
            client = LMStudioClient(self.pm.settings.get("lmstudio_url", DEFAULT_BASE_URL), self.pm.settings.get("model", ""))
            models = client.list_models(); self.ai_label.setText(f"AI ● 연결됨 ({models[0] if models else '모델 없음'})"); self.append_log("LM Studio 연결 확인 완료")
        except Exception as e:
            self.ai_label.setText("AI ● 연결 실패"); QMessageBox.warning(self, "AI 연결 실패", str(e))

    def start_ai(self, job_type: str, target: str, system: str, user: str, temp: float = 0.7, max_tokens: int = 6000, on_done=None):
        if not self.pm.active or not self.pm.db: return
        try:
            client = LMStudioClient(self.pm.settings.get("lmstudio_url", DEFAULT_BASE_URL), self.pm.settings.get("model", ""))
            self._pending_callback = on_done
            self._pending_job = self.pm.db.add_ai_job(job_type, target, client.model, len(user))
            self.progress.setRange(0, 0); self.progress.show(); self.status.showMessage("AI 작업 중...")
            self.ai_thread = QThread(); self.ai_worker = AIWorker(client, system, user, temp, max_tokens); self.ai_worker.moveToThread(self.ai_thread)
            self.ai_thread.started.connect(self.ai_worker.run); self.ai_worker.progress.connect(self.status.showMessage); self.ai_worker.finished.connect(self.ai_finished); self.ai_worker.failed.connect(self.ai_failed); self.ai_thread.start()
        except Exception as e:
            QMessageBox.critical(self, "AI 준비 실패", str(e))

    def ai_finished(self, text: str, model: str):
        if self.pm.db:
            self.pm.db.finish_ai_job(self._pending_job, "완료", len(text), "")
        self.last_ai_result = text
        self.last_ai_model = model
        cb = getattr(self, "_pending_callback", None)
        self.progress.hide(); self.status.showMessage("AI 작업 완료"); self.append_log(f"AI 완료: {model}, {len(text):,}자")
        if cb: cb(text)
        self._cleanup_ai_thread()

    def ai_failed(self, error: str):
        if self.pm.db:
            self.pm.db.finish_ai_job(self._pending_job, "실패", 0, error)
        self.progress.hide(); self.status.showMessage("AI 작업 실패"); self.append_log(f"AI 오류: {error}"); QMessageBox.warning(self, "AI 오류", error); self._cleanup_ai_thread()

    def _cleanup_ai_thread(self):
        if self.ai_thread:
            self.ai_thread.quit(); self.ai_thread.wait(2000)
        self.ai_thread = None; self.ai_worker = None

    def generate_master_plan(self):
        seed = self.seed_edit.toPlainText().strip()
        if not seed:
            QMessageBox.information(self, "입력 필요", "짧은 아이디어를 입력해주세요."); return
        target = self.target_spin.value()
        user = f"""[작품 Seed]\n{seed}\n\n[목표 화수]\n{target}\n\n다음 순서로 설계하라.\n1. 작품 핵심\n2. 세계관\n3. 주인공/주요 인물\n4. 수련 및 성장 구조\n5. 핵심 세력과 갈등\n6. {target}화 전체 장기 구조\n7. 각 부/아크별 핵심 전환점\n8. 최종 결말\n9. 향후 세부화 시 반드시 지켜야 할 불변 핵심"""
        def done(text: str):
            self.master_plan.setPlainText(text); self.pm.db.set_meta("master_plan", text); self.append_log("마스터 플랜 저장")
        self.start_ai("MASTER_PLAN", str(target), PLANNER_SYSTEM, user, 0.75, 7000, done)

    def extract_contract(self):
        plan = self.master_plan.toPlainText().strip()
        if not plan: return
        user = "다음 마스터 플랜에서 이후 모든 청크와 본문이 임의로 바꾸면 안 되는 불변 핵심을 추출해 Plan Contract 형식으로 정리하라.\n\n" + plan
        self.start_ai("PLAN_CONTRACT", "master", PLANNER_SYSTEM + "\nPlan Contract를 간결하게 구조화하라.", user, 0.3, 4000, lambda t: self.contract_edit.setPlainText(t))

    def generate_selected_chunk(self):
        row = self.chunk_list.currentRow()
        if row < 0: return
        start, end = self.chunk_list.item(row).data(Qt.UserRole)
        self.generate_chunk(start, end)

    def generate_chunk(self, start: int, end: int, after=None):
        assert self.pm.db
        contract = self.pm.db.contract(); contract_text = contract["content"] if contract else ""
        prev = self.pm.db.previous_chunk(start); prev_snapshot = prev["snapshot"] if prev else "(첫 청크)"
        arc = self._find_arc_context(start, end)
        context = self._build_plan_context(start, end)
        user = f"""[PLAN CONTRACT]\n{contract_text}\n\n[MASTER PLAN]\n{self.pm.db.get_meta('master_plan','')}\n\n[현재 아크]\n{arc}\n\n[직전 청크 SNAPSHOT]\n{prev_snapshot}\n\n[관련 기억]\n{context}\n\n[생성 범위]\n{start}~{end}화\n\n지정 범위의 화별 플롯과 청크 Snapshot을 작성하라."""
        def done(text: str):
            self.pm.db.ensure_chapters_range(start, end)
            objective = self._extract_section(text, "[목표]", max_chars=1000)
            snapshot = self._extract_snapshot(text)
            self.pm.db.save_chunk(start, end, "완료", objective, text, snapshot)
            for n in range(start, end + 1):
                self.pm.db.save_plot(n, self._extract_title_for_chapter(text, n), self._extract_chapter_block(text, n))
            self.save_chunk_file(start, end, text); self.refresh_chunks(); self.update_state_panel(); self.append_log(f"{start}~{end}화 청크 생성 완료")
            if after: after()
        self.start_ai("CHUNK_PLAN", f"{start}-{end}", CHUNK_SYSTEM, user, 0.65, 7000, done)

    def _build_plan_context(self, start: int, end: int) -> str:
        assert self.pm.db
        parts = []
        for r in self.pm.db.recent_summaries(start, 4): parts.append(f"[SUMMARY {r['chapter_number']}]\n{r['summary']}\n[STATE]\n{r['state_snapshot']}")
        return "\n\n".join(parts)[:12000]

    def _find_arc_context(self, start: int, end: int) -> str:
        assert self.pm.db
        rows = self.pm.db.conn.execute("SELECT * FROM arcs WHERE start_chapter<=? AND end_chapter>=? ORDER BY id LIMIT 3", (end, start)).fetchall()
        return "\n\n".join(f"{r['name']} ({r['start_chapter']}~{r['end_chapter']})\n{r['objective']}\n{r['content']}" for r in rows) or "현재 아크 정보 없음"

    def _extract_section(self, text: str, heading: str, max_chars: int = 1000) -> str:
        idx = text.find(heading)
        if idx < 0: return ""
        tail = text[idx + len(heading):]
        m = re.search(r"\n\[", tail)
        return tail[:m.start()].strip()[:max_chars] if m else tail.strip()[:max_chars]

    def _extract_snapshot(self, text: str) -> str:
        m = re.search(r"\[CHUNK SNAPSHOT\]\s*(.*)$", text, re.I | re.S)
        return m.group(1).strip() if m else ""

    def _extract_title_for_chapter(self, text: str, n: int) -> str:
        block = self._extract_chapter_block(text, n)
        first = block.splitlines()[0] if block else ""
        return re.sub(r"^\[?\s*" + re.escape(str(n)) + r"화\s*[/\-:]?\s*", "", first, flags=re.I).strip(" []")[:120]

    def _extract_chapter_block(self, text: str, n: int) -> str:
        patterns = [rf"(?m)^\[?\s*{n}화.*?$", rf"(?m)^###\s*제?\s*{n}화.*?$"]
        start = None
        for p in patterns:
            m = re.search(p, text)
            if m: start = m.start(); break
        if start is None: return ""
        nxt = re.search(r"(?m)^\[?\s*\d+화.*?$", text[start + 1:])
        end = start + 1 + nxt.start() if nxt else text.find("[CHUNK SNAPSHOT]", start)
        if end < start: end = len(text)
        return text[start:end].strip()

    def save_chunk_file(self, start: int, end: int, text: str):
        assert self.pm.paths
        (self.pm.paths.plans / f"chunk_{start:03d}_{end:03d}.txt").write_text(text, encoding="utf-8")
        snapshot = self._extract_snapshot(text)
        (self.pm.paths.snapshots / f"chunk_{start:03d}_{end:03d}_snapshot.txt").write_text(snapshot, encoding="utf-8")

    def refresh_chunks(self):
        if not self.pm.active or not self.pm.db: return
        target = self.target_spin.value(); size = self.chunk_spin.value()
        self.pm.db.ensure_chapters_range(1, min(target, max(size, 100)))
        rows = {(int(r["start_chapter"]), int(r["end_chapter"])): r for r in self.pm.db.chunks()}
        self.chunk_list.blockSignals(True); self.chunk_list.clear()
        for start in range(1, target + 1, size):
            end = min(start + size - 1, target); r = rows.get((start, end)); status = r["status"] if r else "미생성"
            item = QListWidgetItem(f"{start:03d}~{end:03d}  {status}"); item.setData(Qt.UserRole, (start, end)); self.chunk_list.addItem(item)
        self.chunk_list.blockSignals(False)

    def chunk_selected(self, row: int):
        if row < 0 or not self.pm.active: return
        start, end = self.chunk_list.item(row).data(Qt.UserRole); c = self.pm.db.get_chunk(start, end)
        self.chunk_detail.setPlainText((c["content"] + "\n\n[SNAPSHOT]\n" + c["snapshot"]) if c else "미생성")

    def generate_all_chunks(self):
        if self.batch_active: return
        target = self.target_spin.value(); size = self.chunk_spin.value(); self.batch_queue = [(s, min(s + size - 1, target)) for s in range(1, target + 1, size)]; self.batch_mode = "plan"; self.batch_active = True; self._process_batch_queue()

    def resume_chunks(self):
        if self.batch_active: return
        target = self.target_spin.value(); size = self.chunk_spin.value(); pending = []
        for s in range(1, target + 1, size):
            e = min(s + size - 1, target); c = self.pm.db.get_chunk(s, e)
            if not c or c["status"] != "완료": pending.append((s, e))
        if not pending:
            QMessageBox.information(self, "완료", "미완료 청크가 없습니다."); return
        self.batch_queue = pending; self.batch_mode = "plan"; self.batch_active = True; self._process_batch_queue()

    def _process_batch_queue(self):
        if not self.batch_queue:
            self.batch_active = False; self.status.showMessage("자동 청크 생성 완료"); self.refresh_chunks(); return
        s, e = self.batch_queue.pop(0); self.status.showMessage(f"청크 생성: {s}~{e}화")
        self.generate_chunk(s, e, self._process_batch_queue)

    def continue_writing(self):
        self.generate_chapter(self.current_chapter)

    def generate_chapter(self, n: int, after=None):
        assert self.pm.db
        plot = self.pm.db.get_plot(n); plot_text = plot["content"] if plot else ""
        prev = self.pm.load_chapter(n - 1) if n > 1 else ""
        recent = self._recent_chapter_context(n)
        state = self.pm.db.state_snapshot(n - 1) if n > 1 else None
        characters = self._characters_context(n)
        fs = self._foreshadow_context()
        contract = self.pm.db.contract(); contract_text = contract["content"] if contract else ""
        user = f"""[PLAN CONTRACT]\n{contract_text}\n\n[현재 화 플롯]\n{plot_text}\n\n[직전 화]\n{trim_text(prev, 16000)}\n\n[최근 4화 요약]\n{recent}\n\n[状态 SNAPSHOT]\n{state['content'] if state else '(없음)'}\n\n[관련 인물]\n{characters}\n\n[활성 복선]\n{fs}\n\n[집필 목표]\n{n}화를 {self.pm.settings.get('chapter_length','4,000~5,000자')} 분량으로 작성하라."""
        def done(text: str):
            self.chapter_title.setText(plot["title"] if plot else "")
            self.editor.setPlainText(text); self.pm.save_chapter(n, text, self.chapter_title.text())
            self.generate_memory_after_write(n, after)
        self.start_ai("WRITE_CHAPTER", str(n), WRITER_SYSTEM, user, 0.75, 9000, done)

    def _recent_chapter_context(self, n: int) -> str:
        assert self.pm.db
        return "\n\n".join(f"{r['chapter_number']}화\n{r['summary']}\n{r['state_snapshot']}" for r in self.pm.db.recent_summaries(n, 4))[:10000]

    def _characters_context(self, n: int) -> str:
        assert self.pm.db
        chunks = []
        for c in self.pm.db.characters():
            st = self.pm.db.latest_character_state(int(c["id"]), n)
            if st:
                chunks.append(f"{c['name']} | {c['personality']} | 위치={st['location']} | 경지={st['cultivation']} | 상태={st['condition']} | 부상={st['injuries']} | 알고 있음={st['knows']} | 모름={st['does_not_know']}")
            else:
                chunks.append(f"{c['name']} | {c['personality']} | 목표={c['goal']}")
        return "\n".join(chunks)[:10000]

    def _foreshadow_context(self) -> str:
        assert self.pm.db
        return "\n".join(f"{r['code']} | {r['title']} | 상태={r['status']} | 최초={r['first_chapter']} | 예정회수={r['planned_reveal_chapter']} | 공개={r['public_info']}" for r in self.pm.db.foreshadows() if r["status"] not in ("완전회수", "폐기"))[:8000]

    def edit_current(self):
        text = self.editor.toPlainText().strip()
        if not text: return
        user = f"[현재 원고]\n{text}\n\n원고의 사건, 정보, 설정을 유지하면서 최종 웹소설 문체로 윤문하라."
        self.start_ai("EDIT", str(self.current_chapter), EDITOR_SYSTEM, user, 0.4, 9000, lambda t: self.editor.setPlainText(t))

    def generate_memory_for_current(self):
        self.generate_memory_after_write(self.current_chapter)

    def generate_memory_after_write(self, n: int, after=None):
        text = self.pm.load_chapter(n)
        prev_snapshot = self.pm.db.state_snapshot(n - 1) if n > 1 else None
        user = f"""[제{n}화 원고]\n{text}\n\n[이전 상태]\n{prev_snapshot['content'] if prev_snapshot else '(없음)'}\n\n다음 형식으로 작성하라.\n[CHAPTER SUMMARY]\n장면과 사건 중심의 5~10문장 요약\n\n[STATE SNAPSHOT]\n현재 시간:\n현재 장소:\n주요 인물:\n경지/능력:\n부상/체력:\n소지품 변화:\n관계 변화:\n인물 지식 변화:\n진행 중 사건:\n활성 복선:\n회수된 복선:\n미해결 사건:\n다음 화 필수 연결점:\n"""
        def done(t: str):
            summary = self._extract_memory_section(t, "[CHAPTER SUMMARY]", "[STATE SNAPSHOT]")
            state = self._extract_memory_section(t, "[STATE SNAPSHOT]", None)
            self.pm.db.save_summary(n, summary, state); self.pm.db.save_state_snapshot(n, state)
            (self.pm.paths.memory / f"chapter_{n:03d}_memory.txt").write_text(t, encoding="utf-8")
            self.update_state_panel(); self.append_log(f"{n}화 기억/Snapshot 갱신")
            if after: after()
        self.start_ai("MEMORY", str(n), SUMMARIZER_SYSTEM, user, 0.25, 5000, done)

    def _extract_memory_section(self, text: str, start_heading: str, end_heading: Optional[str]) -> str:
        i = text.find(start_heading)
        if i < 0: return ""
        s = text[i + len(start_heading):]
        if end_heading and end_heading in s: s = s.split(end_heading, 1)[0]
        return s.strip()

    def verify_current(self):
        n = self.current_chapter; current = self.pm.load_chapter(n); prev = self.pm.load_chapter(n - 1) if n > 1 else ""; plot = self.pm.db.get_plot(n); state = self.pm.db.state_snapshot(n - 1) if n > 1 else None
        user = f"""[현재 화 {n}]\n{current}\n\n[직전 화]\n{trim_text(prev,12000)}\n\n[현재 플롯]\n{plot['content'] if plot else ''}\n\n[이전 상태]\n{state['content'] if state else ''}\n\n연속성 문제를 심각도/근거/관련 화와 함께 검사하라. 문제가 없으면 '문제 없음'이라고 명시하라."""
        self.start_ai("CONTINUITY", str(n), CHECKER_SYSTEM, user, 0.2, 5000, lambda t: self.continuity_result.setPlainText(t))

    def batch_write_dialog(self):
        d = QDialog(self); d.setWindowTitle("범위 자동 집필"); form = QFormLayout(d)
        start = QSpinBox(); start.setRange(1,10000); start.setValue(self.current_chapter)
        end = QSpinBox(); end.setRange(1,10000); end.setValue(min(self.current_chapter+4, self.target_spin.value()))
        checkpoint = QComboBox(); checkpoint.addItems(["매화", "5화마다", "10화마다"])
        form.addRow("시작 화", start); form.addRow("종료 화", end); form.addRow("체크포인트", checkpoint)
        run = QPushButton("시작"); form.addRow(run); run.clicked.connect(d.accept)
        if d.exec() != QDialog.Accepted: return
        self.batch_queue = [(n, n) for n in range(start.value(), end.value()+1)]; self.batch_mode = "write"; self.batch_checkpoint = checkpoint.currentText(); self.batch_active = True; self._process_write_queue()

    def _process_write_queue(self):
        if not self.batch_queue:
            self.batch_active = False; self.status.showMessage("자동 집필 완료"); return
        n, _ = self.batch_queue.pop(0); self.current_chapter = n
        self.generate_chapter(n, self._process_write_queue)

    def refresh_characters(self):
        if not self.pm.active: return
        self.char_list.blockSignals(True); self.char_list.clear()
        for c in self.pm.db.characters():
            i = QListWidgetItem(c["name"]); i.setData(Qt.UserRole, int(c["id"])); self.char_list.addItem(i)
        self.char_list.blockSignals(False)

    def character_selected(self, row: int):
        if row < 0: return
        c = self.pm.db.character(int(self.char_list.item(row).data(Qt.UserRole)))
        for w, key in ((self.char_name,"name"),(self.char_role,"role"),(self.char_profile,"profile"),(self.char_personality,"personality"),(self.char_speech,"speech_style"),(self.char_goal,"goal"),(self.char_secret,"secret")): w.setPlainText(c[key]) if isinstance(w,QPlainTextEdit) else w.setText(c[key])

    def save_character(self):
        self.pm.db.upsert_character({"name":self.char_name.text().strip(),"role":self.char_role.text(),"profile":self.char_profile.toPlainText(),"personality":self.char_personality.toPlainText(),"speech_style":self.char_speech.toPlainText(),"goal":self.char_goal.toPlainText(),"secret":self.char_secret.toPlainText()}); self.refresh_characters()

    def refresh_worlds(self):
        if not self.pm.active: return
        self.world_list.clear()
        for r in self.pm.db.worlds(): i=QListWidgetItem(f"{r['category']} | {r['name']}"); i.setData(Qt.UserRole,int(r['id'])); self.world_list.addItem(i)

    def world_selected(self,row:int):
        if row<0:return
        r=self.pm.db.conn.execute("SELECT * FROM world_entities WHERE id=?",(self.world_list.item(row).data(Qt.UserRole),)).fetchone()
        self.world_name.setText(r['name']); self.world_category.setText(r['category']); self.world_description.setPlainText(r['description']); self.world_rules.setPlainText(r['rules']); self.world_status.setCurrentText(r['status'])

    def save_world(self):
        self.pm.db.upsert_world({"name":self.world_name.text().strip(),"category":self.world_category.text(),"description":self.world_description.toPlainText(),"rules":self.world_rules.toPlainText(),"status":self.world_status.currentText()}); self.refresh_worlds()

    def refresh_timeline(self):
        if not self.pm.active:return
        self.timeline_list.clear()
        for r in self.pm.db.timeline(): i=QListWidgetItem(f"{r['chapter_number'] or '-'}화 | {r['story_date']} | {r['title']}"); i.setData(Qt.UserRole,int(r['id'])); self.timeline_list.addItem(i)

    def timeline_selected(self,row:int):
        if row<0:return
        r=self.pm.db.conn.execute("SELECT * FROM timeline_events WHERE id=?",(self.timeline_list.item(row).data(Qt.UserRole),)).fetchone(); self.tl_chapter.setValue(r['chapter_number'] or 0); self.tl_date.setText(r['story_date']); self.tl_title.setText(r['title']); self.tl_desc.setPlainText(r['description']); self.tl_location.setText(r['location']); self.tl_participants.setText(r['participants'])

    def save_timeline(self):
        self.pm.db.upsert_timeline({"chapter_number":self.tl_chapter.value() or None,"story_date":self.tl_date.text(),"title":self.tl_title.text(),"description":self.tl_desc.toPlainText(),"location":self.tl_location.text(),"participants":self.tl_participants.text()}); self.refresh_timeline()

    def refresh_foreshadows(self):
        if not self.pm.active:return
        self.foreshadow_list.clear()
        for r in self.pm.db.foreshadows(): i=QListWidgetItem(f"{r['code']} | {r['title']} | {r['status']}"); i.setData(Qt.UserRole,int(r['id'])); self.foreshadow_list.addItem(i)

    def foreshadow_selected(self,row:int):
        if row<0:return
        r=self.pm.db.conn.execute("SELECT * FROM foreshadowing WHERE id=?",(self.foreshadow_list.item(row).data(Qt.UserRole),)).fetchone()
        self.fs_code.setText(r['code']); self.fs_title.setText(r['title']); self.fs_first.setValue(r['first_chapter'] or 0); self.fs_latest.setValue(r['latest_chapter'] or 0); self.fs_reveal.setValue(r['planned_reveal_chapter'] or 0); self.fs_status.setCurrentText(r['status']); self.fs_public.setPlainText(r['public_info']); self.fs_truth.setPlainText(r['author_truth']); self.fs_related.setText(r['related_characters']); self.fs_notes.setPlainText(r['notes'])

    def save_foreshadow(self):
        self.pm.db.upsert_foreshadow({"code":self.fs_code.text().strip(),"title":self.fs_title.text().strip(),"first_chapter":self.fs_first.value() or None,"latest_chapter":self.fs_latest.value() or None,"planned_reveal_chapter":self.fs_reveal.value() or None,"status":self.fs_status.currentText(),"public_info":self.fs_public.toPlainText(),"author_truth":self.fs_truth.toPlainText(),"related_characters":self.fs_related.text(),"notes":self.fs_notes.toPlainText()}); self.refresh_foreshadows()

    def backup_project(self):
        if not self.pm.active: return
        from zipfile import ZipFile, ZIP_DEFLATED
        assert self.pm.paths
        target = self.pm.paths.backups / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        with ZipFile(target, "w", ZIP_DEFLATED) as z:
            for p in self.pm.paths.root.rglob("*"):
                if p.is_file() and p != target: z.write(p, p.relative_to(self.pm.paths.root))
        self.append_log(f"백업 생성: {target.name}")
        QMessageBox.information(self, "백업 완료", str(target))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow(); win.show(); sys.exit(app.exec())
