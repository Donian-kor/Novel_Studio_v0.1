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

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QPlainTextEdit, QPushButton, QSpinBox, QSplitter, QStatusBar, QTabWidget,
    QVBoxLayout, QWidget, QProgressBar, QCheckBox, QGroupBox
)

APP_NAME = "Novel Studio v0.2"
DEFAULT_BASE_URL = "http://localhost:1234"
DEFAULT_CHUNK_SIZE = 5


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def count_chars(text: str) -> int:
    return len(text.replace("\n", "").replace("\r", ""))


def extract_snapshot(text: str) -> str:
    m = re.search(r"\[CHUNK SNAPSHOT\]\s*(.*)$", text, re.I | re.S)
    return m.group(1).strip() if m else ""


def trim_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


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
        self._init()

    def _init(self) -> None:
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
            CREATE TABLE IF NOT EXISTS plan_contract (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                content TEXT NOT NULL DEFAULT '',
                locked INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS state_snapshots (
                chapter_number INTEGER PRIMARY KEY,
                content TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def set_meta(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO project_meta(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        self.conn.commit()

    def get_meta(self, key: str, default: str = "") -> str:
        row = self.conn.execute("SELECT value FROM project_meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def ensure_chapter(self, number: int) -> None:
        row = self.conn.execute("SELECT number FROM chapters WHERE number=?", (number,)).fetchone()
        if row:
            return
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
            "VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(start_chapter,end_chapter) DO UPDATE SET "
            "status=excluded.status,objective=excluded.objective,content=excluded.content,snapshot=excluded.snapshot,updated_at=excluded.updated_at",
            (start, end, status, objective, content, snapshot, now(), now()),
        )
        self.conn.commit()

    def get_chunk(self, start: int, end: int):
        return self.conn.execute("SELECT * FROM chunks WHERE start_chapter=? AND end_chapter=?", (start, end)).fetchone()

    def chunks(self):
        return self.conn.execute("SELECT * FROM chunks ORDER BY start_chapter").fetchall()

    def latest_completed_chunk_before(self, start: int):
        return self.conn.execute(
            "SELECT * FROM chunks WHERE end_chapter < ? AND status='완료' ORDER BY end_chapter DESC LIMIT 1",
            (start,),
        ).fetchone()

    def set_contract(self, content: str, locked: bool) -> None:
        self.conn.execute(
            "INSERT INTO plan_contract(id,content,locked,updated_at) VALUES(1,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET content=excluded.content,locked=excluded.locked,updated_at=excluded.updated_at",
            (content, 1 if locked else 0, now()),
        )
        self.conn.commit()

    def get_contract(self):
        return self.conn.execute("SELECT * FROM plan_contract WHERE id=1").fetchone()

    def save_state_snapshot(self, chapter_number: int, content: str) -> None:
        self.conn.execute(
            "INSERT INTO state_snapshots(chapter_number,content,updated_at) VALUES(?,?,?) "
            "ON CONFLICT(chapter_number) DO UPDATE SET content=excluded.content,updated_at=excluded.updated_at",
            (chapter_number, content, now()),
        )
        self.conn.commit()

    def get_state_snapshot(self, chapter_number: int):
        return self.conn.execute("SELECT * FROM state_snapshots WHERE chapter_number=?", (chapter_number,)).fetchone()

    def add_job(self, job_type: str, target: str, model: str, prompt_chars: int) -> int:
        cur = self.conn.execute(
            "INSERT INTO ai_jobs(job_type,target,model,status,prompt_chars,created_at) VALUES(?,?,?,?,?,?)",
            (job_type, target, model, "진행중", prompt_chars, now()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def finish_job(self, job_id: int, status: str, output_chars: int = 0, error: str = "") -> None:
        self.conn.execute(
            "UPDATE ai_jobs SET status=?,output_chars=?,completed_at=?,error=? WHERE id=?",
            (status, output_chars, now(), error, job_id),
        )
        self.conn.commit()

    def start_chunk_run(self, start: int, end: int) -> int:
        cur = self.conn.execute(
            "INSERT INTO chunk_runs(start_chapter,end_chapter,status,started_at) VALUES(?,?,?,?)",
            (start, end, "진행중", now()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def finish_chunk_run(self, run_id: int, status: str, message: str = "") -> None:
        self.conn.execute(
            "UPDATE chunk_runs SET status=?,message=?,completed_at=? WHERE id=?",
            (status, message, now(), run_id),
        )
        self.conn.commit()


class LMStudioClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, model: str = ""):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def list_models(self) -> list[str]:
        req = urllib.request.Request(self.base_url + "/v1/models")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [x.get("id", "") for x in data.get("data", []) if x.get("id")]

    def chat(self, system: str, user: str, temperature: float = 0.7, max_tokens: int = 5000) -> str:
        if not self.model:
            models = self.list_models()
            if not models:
                raise RuntimeError("LM Studio에서 모델을 찾지 못했습니다.")
            self.model = models[0]
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + "/v1/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=900) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LM Studio HTTP {e.code}: {detail}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"LM Studio 연결 실패: {e.reason}") from e
        choices = result.get("choices", [])
        if not choices:
            raise RuntimeError("AI 응답이 비어 있습니다.")
        return choices[0].get("message", {}).get("content", "").strip()


class AIWorker(QObject):
    finished = Signal(str, str)
    failed = Signal(str)
    progress = Signal(str)

    def __init__(self, client: LMStudioClient, system: str, user: str, temp: float, max_tokens: int):
        super().__init__()
        self.client = client
        self.system = system
        self.user = user
        self.temp = temp
        self.max_tokens = max_tokens

    def run(self) -> None:
        try:
            self.progress.emit("AI 생성 중...")
            text = self.client.chat(self.system, self.user, self.temp, self.max_tokens)
            self.finished.emit(text, self.client.model)
        except Exception as e:
            self.failed.emit(str(e))


class ProjectManager:
    def __init__(self):
        self.paths: ProjectPaths | None = None
        self.db: Database | None = None
        self.settings: dict = {}

    @property
    def active(self) -> bool:
        return self.paths is not None and self.db is not None

    def create(self, root: Path, title: str, genre: str, target_chapters: int, chapter_length: str) -> None:
        ensure_dir(root)
        paths = ProjectPaths(root)
        for p in (paths.chapters, paths.plans, paths.snapshots, paths.backups, paths.exports, paths.temp):
            ensure_dir(p)
        settings = {
            "title": title,
            "genre": genre,
            "target_chapters": target_chapters,
            "chapter_length": chapter_length,
            "chunk_size": DEFAULT_CHUNK_SIZE,
            "created_at": now(),
        }
        paths.settings.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
        self.paths = paths
        self.settings = settings
        self.db = Database(paths.db)
        self.db.ensure_chapter(1)
        for k, v in settings.items():
            self.db.set_meta(k, str(v))

    def open(self, root: Path) -> None:
        paths = ProjectPaths(root)
        if not paths.db.exists():
            raise RuntimeError("선택한 폴더에 novel.db가 없습니다.")
        self.paths = paths
        self.db = Database(paths.db)
        self.settings = json.loads(paths.settings.read_text(encoding="utf-8")) if paths.settings.exists() else {
            "title": self.db.get_meta("title", root.name),
            "genre": self.db.get_meta("genre", ""),
            "target_chapters": int(self.db.get_meta("target_chapters", "500")),
            "chapter_length": self.db.get_meta("chapter_length", "4,000~5,000자"),
            "chunk_size": int(self.db.get_meta("chunk_size", "5")),
        }
        self.settings.setdefault("chunk_size", 5)
        for p in (paths.chapters, paths.plans, paths.snapshots, paths.backups, paths.exports, paths.temp):
            ensure_dir(p)

    def chapter_path(self, number: int) -> Path:
        assert self.paths is not None
        return self.paths.chapters / f"{number:03d}.txt"

    def load_chapter(self, number: int) -> str:
        path = self.chapter_path(number)
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def save_chapter(self, number: int, text: str, title: str = "") -> None:
        assert self.db is not None
        path = self.chapter_path(number)
        path.write_text(text, encoding="utf-8")
        self.db.ensure_chapter(number)
        status = "확정" if text.strip() else "미작성"
        self.db.update_chapter(number, title, status, count_chars(text))

    def write_plan_file(self, name: str, text: str) -> None:
        assert self.paths is not None
        (self.paths.plans / name).write_text(text, encoding="utf-8")

    def write_snapshot_file(self, chapter_number: int, text: str) -> None:
        assert self.paths is not None
        (self.paths.snapshots / f"after_{chapter_number:03d}.txt").write_text(text, encoding="utf-8")


WRITER_SYSTEM = """당신은 한국 장편 웹소설 전문 작가다.
기존 설정, 확정된 플롯, Plan Contract를 임의로 변경하지 않는다.
장면, 행동, 대화, 감각을 중심으로 쓰며 과도한 설명과 요약을 피한다.
같은 표현과 문장 구조를 반복하지 않는다.
대사는 위아래로 한 줄씩 띄운다.
요청된 본문만 출력하고 해설, 메모, 자기평가를 덧붙이지 않는다.
AI가 쓴 듯한 상투적 표현을 피한다.
"""

PLANNER_SYSTEM = """당신은 한국 장편 웹소설 총괄 기획자다.
짧은 아이디어에서 작품의 핵심 주제, 주인공, 세계관, 장기 갈등, 성장선, 결말을 설계한다.
목표 화수가 크더라도 한 번에 모든 세부 화를 억지로 길게 출력하지 않는다.
먼저 일관된 상위 구조를 만든다.
확정해야 할 핵심 사실은 별도의 Plan Contract로 추출할 수 있도록 명확하게 적는다.
"""

CHUNK_SYSTEM = """당신은 장편 웹소설의 청크 플롯 설계자다.
입력으로 전체 기획, Plan Contract, 현재 아크, 직전 청크 상태가 주어진다.
지정된 화 범위만 상세화한다.
반드시 각 화를 다음 형식으로 작성한다.

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

청크 마지막에는 정확히 [CHUNK SNAPSHOT] 섹션을 만들고 다음을 정리한다.
- 주요 사건
- 주인공 상태
- 주요 인물 상태 변화
- 관계 변화
- 경지/능력 변화
- 위치/시간 변화
- 소지품 변화
- 활성/신규/회수 복선
- 미해결 사건
- 다음 청크 필수 연결점
"""

CHECKER_SYSTEM = """당신은 한국 장편 웹소설의 연속성 검수자다.
주어진 자료만 근거로 검사하고 새로운 설정을 확정하지 않는다.
문제는 심각도와 근거 화수를 함께 표시한다.
검사 항목: 시간, 장소, 인물 위치, 경지, 부상, 소지품, 인물 지식 범위, 사건 순서, 플롯 이탈, 복선 상태.
"""

EDITOR_SYSTEM = """당신은 한국 웹소설 전문 윤문가다.
사건, 정보, 설정, 인과관계를 바꾸지 않고 문장과 장면의 품질을 개선한다.
반복 표현, 문장 단절, 어색한 대화, 장면 전환, 과도한 감정 설명을 다듬는다.
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1550, 920)
        self.pm = ProjectManager()
        self.ai_thread: QThread | None = None
        self.ai_worker: AIWorker | None = None
        self.last_ai_result = ""
        self.last_ai_model = ""
        self.job_meta: dict[int, dict] = {}
        self.current_chapter = 1
        self.batch_queue: list[tuple[int, int]] = []
        self.batch_active = False
        self._build_menu()
        self._build_ui()
        self._set_enabled(False)

    def _build_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("파일")
        for text, slot in [("새 작품", self.create_project), ("작품 열기", self.open_project), ("원고 저장", self.save_current)]:
            act = QAction(text, self)
            act.triggered.connect(slot)
            file_menu.addAction(act)
        file_menu.addSeparator()
        ai_act = QAction("AI 설정", self)
        ai_act.triggered.connect(self.show_ai_settings)
        file_menu.addAction(ai_act)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        header = QHBoxLayout()
        self.project_label = QLabel("작품: 열리지 않음")
        self.ai_label = QLabel("AI: 미설정")
        self.ai_test_btn = QPushButton("AI 연결 테스트")
        self.ai_test_btn.clicked.connect(self.test_ai)
        header.addWidget(self.project_label)
        header.addStretch()
        header.addWidget(self.ai_label)
        header.addWidget(self.ai_test_btn)
        layout.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter, 1)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("화 목록"))
        self.chapter_list = QListWidget()
        self.chapter_list.currentRowChanged.connect(self.chapter_selected)
        left_layout.addWidget(self.chapter_list, 1)
        self.add_chapter_btn = QPushButton("다음 화 추가")
        self.add_chapter_btn.clicked.connect(self.add_next_chapter)
        left_layout.addWidget(self.add_chapter_btn)
        splitter.addWidget(left)

        center = QTabWidget()
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("원고를 입력하세요. TXT로 저장됩니다.")
        self.editor.textChanged.connect(self.on_editor_changed)
        center.addTab(self.editor, "원고")

        plot_widget = QWidget()
        pl = QVBoxLayout(plot_widget)
        self.plot_title = QLineEdit()
        self.plot_content = QPlainTextEdit()
        pl.addWidget(QLabel("화 제목"))
        pl.addWidget(self.plot_title)
        pl.addWidget(QLabel("화별 플롯"))
        pl.addWidget(self.plot_content, 1)
        row = QHBoxLayout()
        self.ai_plot_btn = QPushButton("AI 화별 플롯")
        self.ai_plot_btn.clicked.connect(self.generate_chapter_plot)
        self.save_plot_btn = QPushButton("플롯 저장")
        self.save_plot_btn.clicked.connect(self.save_plot)
        row.addWidget(self.ai_plot_btn)
        row.addWidget(self.save_plot_btn)
        pl.addLayout(row)
        center.addTab(plot_widget, "화별 플롯")

        planning = QWidget()
        p = QVBoxLayout(planning)
        self.seed_edit = QPlainTextEdit()
        self.seed_edit.setPlaceholderText("짧은 아이디어/Seed 입력")
        p.addWidget(QLabel("아이디어 / Seed"))
        p.addWidget(self.seed_edit, 1)
        form = QFormLayout()
        self.target_spin = QSpinBox(); self.target_spin.setRange(1, 5000); self.target_spin.setValue(500)
        self.chunk_spin = QSpinBox(); self.chunk_spin.setRange(1, 20); self.chunk_spin.setValue(5)
        form.addRow("목표 화수", self.target_spin)
        form.addRow("플롯 청크 크기", self.chunk_spin)
        p.addLayout(form)
        plan_buttons = QHBoxLayout()
        self.ai_plan_btn = QPushButton("AI 마스터 기획")
        self.ai_plan_btn.clicked.connect(self.generate_master_plan)
        self.ai_chunk_btn = QPushButton("선택 청크 생성")
        self.ai_chunk_btn.clicked.connect(self.generate_selected_chunk)
        self.ai_batch_plan_btn = QPushButton("전체 청크 자동 생성")
        self.ai_batch_plan_btn.clicked.connect(self.generate_all_chunks)
        plan_buttons.addWidget(self.ai_plan_btn); plan_buttons.addWidget(self.ai_chunk_btn); plan_buttons.addWidget(self.ai_batch_plan_btn)
        p.addLayout(plan_buttons)
        self.master_plan = QPlainTextEdit(); self.master_plan.setPlaceholderText("마스터 플랜")
        p.addWidget(QLabel("마스터 플랜")); p.addWidget(self.master_plan, 2)
        center.addTab(planning, "AI 기획")

        contract_widget = QWidget()
        cp = QVBoxLayout(contract_widget)
        contract_row = QHBoxLayout()
        self.contract_lock = QCheckBox("Plan Contract 잠금")
        self.contract_lock.toggled.connect(self.contract_lock_changed)
        contract_row.addWidget(self.contract_lock); contract_row.addStretch()
        self.extract_contract_btn = QPushButton("AI Contract 추출")
        self.extract_contract_btn.clicked.connect(self.extract_contract)
        self.save_contract_btn = QPushButton("Contract 저장")
        self.save_contract_btn.clicked.connect(self.save_contract)
        contract_row.addWidget(self.extract_contract_btn); contract_row.addWidget(self.save_contract_btn)
        cp.addLayout(contract_row)
        self.contract_edit = QPlainTextEdit(); cp.addWidget(self.contract_edit, 1)
        center.addTab(contract_widget, "Plan Contract")

        chunks_widget = QWidget()
        ch = QVBoxLayout(chunks_widget)
        ch.addWidget(QLabel("생성된 청크"))
        self.chunk_list = QListWidget(); self.chunk_list.currentRowChanged.connect(self.chunk_selected)
        ch.addWidget(self.chunk_list, 1)
        cr = QHBoxLayout()
        self.resume_btn = QPushButton("중단 지점부터 계속")
        self.resume_btn.clicked.connect(self.resume_batch)
        self.batch_stop_btn = QPushButton("자동 생성 중지")
        self.batch_stop_btn.clicked.connect(self.stop_batch)
        cr.addWidget(self.resume_btn); cr.addWidget(self.batch_stop_btn)
        ch.addLayout(cr)
        self.chunk_detail = QPlainTextEdit(); self.chunk_detail.setReadOnly(True)
        ch.addWidget(QLabel("선택 청크 상세")); ch.addWidget(self.chunk_detail, 2)
        center.addTab(chunks_widget, "청크 관리")

        self.ai_result = QPlainTextEdit(); self.ai_result.setReadOnly(True)
        ai_widget = QWidget(); al = QVBoxLayout(ai_widget)
        al.addWidget(QLabel("AI 결과 미리보기")); al.addWidget(self.ai_result, 1)
        ar = QHBoxLayout()
        self.apply_ai_btn = QPushButton("원고에 적용"); self.apply_ai_btn.clicked.connect(self.apply_ai_result)
        self.use_plot_btn = QPushButton("플롯에 적용"); self.use_plot_btn.clicked.connect(self.apply_ai_as_plot)
        ar.addWidget(self.apply_ai_btn); ar.addWidget(self.use_plot_btn); al.addLayout(ar)
        center.addTab(ai_widget, "AI 결과")

        splitter.addWidget(center)

        right = QWidget(); rl = QVBoxLayout(right)
        rl.addWidget(QLabel("현재 상태"))
        self.state_label = QLabel("작품을 열어주세요."); self.state_label.setWordWrap(True)
        rl.addWidget(self.state_label)
        rl.addWidget(QLabel("최근 작업"))
        self.log = QPlainTextEdit(); self.log.setReadOnly(True); rl.addWidget(self.log, 1)
        splitter.addWidget(right)
        splitter.setSizes([210, 1040, 300])

        bottom = QHBoxLayout()
        self.new_chapter_btn = QPushButton("새 화")
        self.next_write_btn = QPushButton("이어쓰기")
        self.edit_btn = QPushButton("AI 윤문")
        self.verify_btn = QPushButton("연속성 검사")
        self.save_btn = QPushButton("저장")
        self.batch_write_btn = QPushButton("범위 자동 집필")
        for btn, slot in [
            (self.new_chapter_btn, self.new_chapter), (self.next_write_btn, self.continue_writing),
            (self.edit_btn, self.rewrite_current), (self.verify_btn, self.verify_current),
            (self.save_btn, self.save_current), (self.batch_write_btn, self.batch_write),
        ]:
            btn.clicked.connect(slot); bottom.addWidget(btn)
        bottom.addStretch(); self.count_label = QLabel("0자"); bottom.addWidget(self.count_label)
        layout.addLayout(bottom)

        self.progress = QProgressBar(); self.progress.setRange(0, 0); self.progress.hide(); layout.addWidget(self.progress)
        self.status = QStatusBar(); self.setStatusBar(self.status); self.status.showMessage("준비됨")

    def _set_enabled(self, value: bool):
        widgets = [self.chapter_list, self.ai_test_btn, self.add_chapter_btn, self.ai_plot_btn, self.save_plot_btn,
                   self.ai_plan_btn, self.ai_chunk_btn, self.ai_batch_plan_btn, self.target_spin, self.chunk_spin,
                   self.editor, self.seed_edit, self.plot_title, self.plot_content, self.contract_edit,
                   self.extract_contract_btn, self.save_contract_btn, self.contract_lock, self.chunk_list,
                   self.resume_btn, self.batch_stop_btn, self.apply_ai_btn, self.use_plot_btn,
                   self.new_chapter_btn, self.next_write_btn, self.edit_btn, self.verify_btn, self.save_btn, self.batch_write_btn]
        for w in widgets: w.setEnabled(value)

    def append_log(self, text: str):
        self.log.appendPlainText(f"[{datetime.now().strftime('%H:%M:%S')}] {text}")

    def create_project(self):
        dialog = NewProjectDialog(self)
        if dialog.exec() != QDialog.Accepted: return
        root = Path(dialog.folder_edit.text()).expanduser()
        try:
            self.pm.create(root, dialog.title_edit.text().strip(), dialog.genre_edit.text().strip(), dialog.target_spin.value(), dialog.length_edit.text().strip())
            self.open_loaded_project()
        except Exception as e: QMessageBox.critical(self, "생성 실패", str(e))

    def open_project(self):
        folder = QFileDialog.getExistingDirectory(self, "프로젝트 폴더 선택")
        if not folder: return
        try:
            self.pm.open(Path(folder)); self.open_loaded_project()
        except Exception as e: QMessageBox.critical(self, "열기 실패", str(e))

    def open_loaded_project(self):
        assert self.pm.active and self.pm.db
        self.project_label.setText(f"작품: {self.pm.settings.get('title', self.pm.paths.root.name)}")
        self.target_spin.setValue(int(self.pm.settings.get('target_chapters', 500)))
        self.chunk_spin.setValue(int(self.pm.settings.get('chunk_size', 5)))
        self.master_plan.setPlainText(self.pm.db.get_meta("master_plan", ""))
        contract = self.pm.db.get_contract()
        self.contract_edit.setPlainText(contract["content"] if contract else "")
        self.contract_lock.setChecked(bool(contract and contract["locked"]))
        self.refresh_chapters(); self.refresh_chunks()
        if self.chapter_list.count(): self.chapter_list.setCurrentRow(0)
        self._set_enabled(True)
        self.status.showMessage(f"프로젝트 열림: {self.pm.paths.root}")
        self.append_log("프로젝트를 열었습니다.")

    def refresh_chapters(self):
        assert self.pm.db
        self.chapter_list.blockSignals(True); self.chapter_list.clear()
        rows = self.pm.db.chapter_rows(); existing = {int(r['number']) for r in rows}
        max_preload = min(self.target_spin.value(), max(50, (max(existing) + 10) if existing else 10))
        for n in range(1, max_preload + 1):
            if n not in existing: self.pm.db.ensure_chapter(n)
        for row in self.pm.db.chapter_rows():
            item = QListWidgetItem(f"{row['number']:03d}  {row['status']}")
            item.setData(Qt.UserRole, int(row['number'])); self.chapter_list.addItem(item)
        self.chapter_list.blockSignals(False)

    def refresh_chunks(self):
        assert self.pm.db
        self.chunk_list.blockSignals(True); self.chunk_list.clear()
        for row in self.pm.db.chunks():
            item = QListWidgetItem(f"{row['start_chapter']:03d}~{row['end_chapter']:03d}  {row['status']}")
            item.setData(Qt.UserRole, (int(row['start_chapter']), int(row['end_chapter'])))
            self.chunk_list.addItem(item)
        self.chunk_list.blockSignals(False)
        if self.chunk_list.count() and self.chunk_list.currentRow() < 0: self.chunk_list.setCurrentRow(0)

    def chapter_selected(self, row: int):
        if row < 0 or not self.pm.active: return
        self.load_chapter(int(self.chapter_list.item(row).data(Qt.UserRole)))

    def load_chapter(self, number: int):
        self.current_chapter = number
        self.editor.blockSignals(True); self.editor.setPlainText(self.pm.load_chapter(number)); self.editor.blockSignals(False)
        row = self.pm.db.chapter(number)
        self.plot_title.setText(row['title'] if row else '')
        plot = self.pm.db.get_plot(number); self.plot_content.setPlainText(plot['content'] if plot else '')
        self.update_count(); self.update_state_panel()

    def chunk_selected(self, row: int):
        if row < 0 or not self.pm.active: return
        start, end = self.chunk_list.item(row).data(Qt.UserRole)
        c = self.pm.db.get_chunk(start, end)
        if c:
            self.chunk_detail.setPlainText(f"상태: {c['status']}\n범위: {start}~{end}화\n\n{c['content']}\n\n[SNAPSHOT]\n{c['snapshot']}")

    def update_count(self): self.count_label.setText(f"{count_chars(self.editor.toPlainText()):,}자")
    def on_editor_changed(self): self.update_count()

    def add_next_chapter(self):
        if not self.pm.active: return
        n = self.current_chapter + 1; self.pm.db.ensure_chapter(n); self.refresh_chapters()
        for i in range(self.chapter_list.count()):
            if int(self.chapter_list.item(i).data(Qt.UserRole)) == n:
                self.chapter_list.setCurrentRow(i); break

    def save_current(self):
        if not self.pm.active: return
        self.pm.save_chapter(self.current_chapter, self.editor.toPlainText(), self.plot_title.text().strip())
        self.refresh_chapters(); self.update_state_panel(); self.status.showMessage(f"{self.current_chapter:03d}화 저장 완료"); self.append_log(f"{self.current_chapter:03d}화 저장")

    def save_plot(self):
        if not self.pm.active: return
        self.pm.db.ensure_chapter(self.current_chapter)
        self.pm.db.save_plot(self.current_chapter, self.plot_title.text().strip(), self.plot_content.toPlainText())
        self.status.showMessage(f"{self.current_chapter:03d}화 플롯 저장"); self.append_log(f"{self.current_chapter:03d}화 플롯 저장")

    def update_state_panel(self):
        if not self.pm.active: return
        row = self.pm.db.chapter(self.current_chapter); text = self.editor.toPlainText()
        title = row['title'] if row else ''; status = row['status'] if row else '미작성'
        self.state_label.setText(f"작품: {self.pm.settings.get('title','')}\n현재 화: {self.current_chapter:03d}화\n제목: {title or '(제목 없음)'}\n상태: {status}\n분량: {count_chars(text):,}자")

    def lm_client(self) -> LMStudioClient:
        return LMStudioClient(self.property("lm_url") or DEFAULT_BASE_URL, self.property("lm_model") or "")

    def show_ai_settings(self):
        d = AISettingsDialog(self, self.property("lm_url") or DEFAULT_BASE_URL, self.property("lm_model") or "")
        if d.exec() == QDialog.Accepted:
            self.setProperty("lm_url", d.url_edit.text().strip()); self.setProperty("lm_model", d.model_edit.text().strip())
            self.ai_label.setText(f"AI: {d.model_edit.text().strip() or '자동'}")

    def test_ai(self):
        try:
            client = self.lm_client(); models = client.list_models()
            if not models: raise RuntimeError("LM Studio에 모델이 없습니다.")
            self.setProperty("lm_model", models[0]); self.ai_label.setText(f"AI: {models[0]}")
            QMessageBox.information(self, "연결 성공", "LM Studio 연결 성공\n\n" + "\n".join(models[:10])); self.append_log(f"LM Studio 연결 성공: {models[0]}")
        except Exception as e: QMessageBox.critical(self, "연결 실패", str(e)); self.append_log(f"LM Studio 연결 실패: {e}")

    def _run_ai(self, job_type: str, system: str, user: str, temp: float, max_tokens: int, meta: dict | None = None):
        if not self.pm.active: return
        client = self.lm_client(); job_id = self.pm.db.add_job(job_type, str(self.current_chapter), client.model, len(system) + len(user))
        self.job_meta[job_id] = {"job_type": job_type, **(meta or {})}
        thread = QThread(); worker = AIWorker(client, system, user, temp, max_tokens); worker.moveToThread(thread)
        thread.started.connect(worker.run); worker.finished.connect(lambda text, m: self.ai_finished(job_id, text, m)); worker.failed.connect(lambda err: self.ai_failed(job_id, err))
        worker.progress.connect(self.status.showMessage); worker.finished.connect(thread.quit); worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater); thread.finished.connect(thread.deleteLater)
        self.ai_thread = thread; self.ai_worker = worker; self.progress.show(); self.append_log(f"AI 작업 시작: {job_type}"); thread.start()

    def ai_finished(self, job_id: int, text: str, model: str):
        self.progress.hide(); self.last_ai_result = text; self.last_ai_model = model; self.ai_result.setPlainText(text)
        self.pm.db.finish_job(job_id, "완료", len(text)); meta = self.job_meta.pop(job_id, {})
        try:
            self.handle_ai_result(meta, text)
        except Exception as e: self.append_log(f"결과 후처리 실패: {e}")
        self.status.showMessage(f"AI 생성 완료 - {len(text):,}자"); self.append_log(f"AI 완료: {meta.get('job_type','')} / {model}")

    def ai_failed(self, job_id: int, err: str):
        self.progress.hide(); self.pm.db.finish_job(job_id, "실패", 0, err); meta = self.job_meta.pop(job_id, {})
        if meta.get("job_type") == "chunk_batch":
            self.batch_active = False
        QMessageBox.critical(self, "AI 작업 실패", err); self.status.showMessage("AI 작업 실패"); self.append_log(f"AI 실패: {err}")

    def handle_ai_result(self, meta: dict, text: str):
        jt = meta.get("job_type")
        if jt == "master_plan":
            self.master_plan.setPlainText(text); self.pm.db.set_meta("master_plan", text)
            self.pm.write_plan_file("master_plan.txt", text)
        elif jt == "contract":
            self.contract_edit.setPlainText(text); self.pm.db.set_contract(text, False); self.pm.write_plan_file("plan_contract.txt", text)
        elif jt == "chunk_plot":
            start, end = meta["start"], meta["end"]
            snap = extract_snapshot(text)
            self.pm.db.ensure_chapters_range(start, end)
            self.pm.db.save_chunk(start, end, "완료", meta.get("objective", ""), text, snap)
            self.pm.write_plan_file(f"chunk_{start:03d}_{end:03d}.txt", text)
            if snap: self.pm.write_snapshot_file(end, snap); self.pm.db.save_state_snapshot(end, snap)
            # chapter-level plots are kept synchronized when recognizable sections exist
            for n in range(start, end + 1):
                sec = self.extract_chapter_section(text, n)
                if sec:
                    title = self.extract_title(sec) or ""
                    self.pm.db.save_plot(n, title, sec)
            self.refresh_chunks(); self.refresh_chapters()
            if self.batch_active:
                self.finish_batch_chunk_and_continue(start, end)
        elif jt == "chapter_plot":
            self.plot_content.setPlainText(text); self.pm.db.ensure_chapter(self.current_chapter); self.pm.db.save_plot(self.current_chapter, self.plot_title.text().strip(), text)
        elif jt == "chapter_write_batch":
            n = int(meta.get("chapter", self.current_chapter))
            self.current_chapter = n
            # Batch write is only auto-applied after generation; the normal single write still requires review.
            self.pm.save_chapter(n, text, self.pm.db.get_plot(n)["title"] if self.pm.db.get_plot(n) else "")
            snap = self.make_light_snapshot(n, text)
            self.pm.db.save_state_snapshot(n, snap)
            self.pm.write_snapshot_file(n, snap)
            self.refresh_chapters()
            if getattr(self, "write_batch_active", False):
                self.process_next_write()
        elif jt in {"chapter_write", "rewrite", "verify"}:
            pass

    def extract_chapter_section(self, chunk_text: str, number: int) -> str:
        pattern = rf"(\[(?:화 번호/제목|{number}화[^\]]*)\].*?)(?=\n\[(?:화 번호/제목|{number + 1}화[^\]]*)\]|\n\[CHUNK SNAPSHOT\]|\Z)"
        m = re.search(pattern, chunk_text, re.I | re.S)
        return m.group(1).strip() if m else ""

    def extract_title(self, section: str) -> str:
        m = re.search(r"\[(?:화 번호/제목)\]\s*\n?\s*(?:\d+화\s*)?([^\n]+)", section, re.I)
        return m.group(1).strip() if m else ""

    def build_context(self, chapter_number: int, include_full_prev: bool = True) -> str:
        assert self.pm.db
        contract = self.pm.db.get_contract(); contract_text = contract["content"] if contract else ""
        master = self.pm.db.get_meta("master_plan", "")
        plot = self.pm.db.get_plot(chapter_number); plot_text = plot["content"] if plot else ""
        prev = self.pm.load_chapter(chapter_number - 1) if chapter_number > 1 else ""
        prev2 = self.pm.load_chapter(chapter_number - 2) if chapter_number > 2 else ""
        snap = self.pm.db.get_state_snapshot(chapter_number - 1) if chapter_number > 1 else None
        chunk = None
        for c in self.pm.db.chunks():
            if c["start_chapter"] <= chapter_number <= c["end_chapter"]:
                chunk = c; break
        current_chunk = chunk["content"] if chunk else ""
        return (
            f"[PLAN CONTRACT]\n{trim_text(contract_text, 7000)}\n\n"
            f"[MASTER PLAN]\n{trim_text(master, 9000)}\n\n"
            f"[CURRENT CHUNK]\n{trim_text(current_chunk, 9000)}\n\n"
            f"[CURRENT CHAPTER PLOT]\n{trim_text(plot_text, 9000)}\n\n"
            f"[PREVIOUS SNAPSHOT]\n{trim_text(snap['content'] if snap else '', 7000)}\n\n"
            f"[PREVIOUS CHAPTER]\n{trim_text(prev, 12000 if include_full_prev else 3000)}\n\n"
            f"[PREVIOUS-2 SUMMARY/PROSE]\n{trim_text(prev2, 5000)}"
        )

    def generate_master_plan(self):
        seed = self.seed_edit.toPlainText().strip()
        if not seed: QMessageBox.warning(self, "입력 필요", "아이디어/Seed를 입력하세요."); return
        target = self.target_spin.value(); genre = self.pm.settings.get("genre", "장편 웹소설")
        user = f"장르: {genre}\n목표 화수: {target}\n\n[아이디어]\n{seed}\n\n다음 구조로 마스터 플랜을 작성하라.\n1. 제목 후보\n2. 로그라인\n3. 세계관 핵심\n4. 주인공/주요 인물\n5. 핵심 갈등\n6. 수련/성장 구조\n7. 전체 결말\n8. 부/막/아크 구조\n9. 주요 복선\n10. Plan Contract 후보"
        self._run_ai("master_plan", PLANNER_SYSTEM, user, 0.85, 7000)

    def extract_contract(self):
        master = self.master_plan.toPlainText().strip()
        if not master: QMessageBox.warning(self, "마스터 플랜 없음", "먼저 마스터 플랜을 생성하세요."); return
        user = f"다음 마스터 플랜에서 전체 장편의 핵심 불변 조건만 추출하여 Plan Contract를 작성하라.\n\n{master}\n\n포함: 주인공, 최종 목표, 최종 갈등, 핵심 세계 법칙, 결말, 회귀/비밀의 핵심, 반드시 유지할 성장축, 변경 금지 항목."
        self._run_ai("contract", PLANNER_SYSTEM, user, 0.35, 3500)

    def save_contract(self):
        if not self.pm.active: return
        locked = self.contract_lock.isChecked()
        self.pm.db.set_contract(self.contract_edit.toPlainText(), locked)
        self.pm.write_plan_file("plan_contract.txt", self.contract_edit.toPlainText())
        self.status.showMessage("Plan Contract 저장")

    def contract_lock_changed(self, locked: bool):
        self.contract_edit.setReadOnly(locked)
        if self.pm.active:
            content = self.contract_edit.toPlainText(); self.pm.db.set_contract(content, locked)

    def chunk_range_dialog(self, default_start: int | None = None):
        start = default_start or self.current_chapter
        d = QDialog(self); d.setWindowTitle("청크 범위")
        form = QFormLayout(d); s = QSpinBox(); s.setRange(1, self.target_spin.value()); s.setValue(start)
        e = QSpinBox(); e.setRange(1, self.target_spin.value()); e.setValue(min(self.target_spin.value(), start + self.chunk_spin.value() - 1))
        form.addRow("시작 화", s); form.addRow("끝 화", e)
        r = QHBoxLayout(); ok = QPushButton("확인"); cancel = QPushButton("취소"); ok.clicked.connect(d.accept); cancel.clicked.connect(d.reject); r.addWidget(ok); r.addWidget(cancel); form.addRow(r)
        if d.exec() != QDialog.Accepted: return None
        if e.value() < s.value(): QMessageBox.warning(self, "범위 오류", "끝 화가 시작 화보다 작습니다."); return None
        return s.value(), e.value()

    def build_chunk_user(self, start: int, end: int) -> str:
        assert self.pm.db
        master = self.pm.db.get_meta("master_plan", "")
        contract = self.pm.db.get_contract(); contract_text = contract["content"] if contract else ""
        previous = self.pm.db.latest_completed_chunk_before(start)
        current_chunk_existing = self.pm.db.get_chunk(start, end)
        return (
            f"[MASTER PLAN]\n{trim_text(master, 14000)}\n\n"
            f"[PLAN CONTRACT]\n{trim_text(contract_text, 8000)}\n\n"
            f"[PREVIOUS CHUNK SNAPSHOT]\n{trim_text(previous['snapshot'] if previous else '', 10000)}\n\n"
            f"[CURRENT CHUNK]\n{start}~{end}화\n"
            f"기존 생성물이 있다면 덮어쓸 수 있도록 더 일관된 버전으로 재생성한다.\n\n"
            f"[EXISTING CHUNK]\n{trim_text(current_chunk_existing['content'] if current_chunk_existing else '', 7000)}\n\n"
            "각 화를 고정 형식으로 작성하고 마지막에 [CHUNK SNAPSHOT]을 작성하라."
        )

    def generate_selected_chunk(self):
        rng = self.chunk_range_dialog()
        if not rng: return
        start, end = rng
        self._run_ai("chunk_plot", CHUNK_SYSTEM, self.build_chunk_user(start, end), 0.75, 7500, {"start": start, "end": end})

    def generate_all_chunks(self):
        if not self.pm.db: return
        if not self.master_plan.toPlainText().strip():
            QMessageBox.warning(self, "마스터 플랜 필요", "먼저 마스터 플랜을 생성하세요."); return
        self.start_batch_plan(1, self.target_spin.value())

    def start_batch_plan(self, start: int, target: int):
        size = self.chunk_spin.value()
        self.batch_queue = []
        n = max(1, start)
        while n <= target:
            e = min(target, n + size - 1)
            row = self.pm.db.get_chunk(n, e)
            if not row or row["status"] != "완료": self.batch_queue.append((n, e))
            n = e + 1
        if not self.batch_queue:
            QMessageBox.information(self, "완료", "생성되지 않은 청크가 없습니다."); return
        self.batch_active = True; self.status.showMessage(f"청크 자동 생성 시작: {len(self.batch_queue)}개"); self.process_next_batch_chunk()

    def process_next_batch_chunk(self):
        if not self.batch_active: return
        if not self.batch_queue:
            self.batch_active = False; self.status.showMessage("모든 청크 생성 완료"); self.append_log("전체 청크 자동 생성 완료"); return
        start, end = self.batch_queue.pop(0)
        self.current_batch_range = (start, end)
        self._run_ai("chunk_batch", CHUNK_SYSTEM, self.build_chunk_user(start, end), 0.75, 7500, {"start": start, "end": end})

    def finish_batch_chunk_and_continue(self, start: int, end: int):
        self.append_log(f"청크 완료: {start:03d}~{end:03d}")
        self.refresh_chunks()
        if self.batch_active: self.process_next_batch_chunk()

    def resume_batch(self):
        self.start_batch_plan(1, self.target_spin.value())

    def stop_batch(self):
        self.batch_active = False; self.batch_queue = []; self.status.showMessage("청크 자동 생성을 중지했습니다."); self.append_log("배치 중지")

    def generate_chapter_plot(self):
        master = self.pm.db.get_meta("master_plan", "") if self.pm.db else ""
        user = self.build_context(self.current_chapter, include_full_prev=False) + f"\n\n현재 화: {self.current_chapter}화\n이 화의 세부 플롯을 고정 형식으로 작성하라."
        self._run_ai("chapter_plot", CHUNK_SYSTEM, trim_text(user, 28000), 0.7, 4500)

    def continue_writing(self):
        plot = self.plot_content.toPlainText().strip()
        if not plot: QMessageBox.warning(self, "플롯 없음", "현재 화 플롯을 먼저 준비하세요."); return
        user = self.build_context(self.current_chapter) + f"\n\n[CURRENT CHAPTER]\n{self.current_chapter}화\n\n이 플롯을 충실히 따르며 4,000~5,000자 내외의 본문을 작성하라."
        self._run_ai("chapter_write", WRITER_SYSTEM, trim_text(user, 32000), 0.75, 7000)

    def batch_write(self):
        d = self.chunk_range_dialog()
        if not d: return
        start, end = d
        self.write_batch_queue = list(range(start, end + 1)); self.write_batch_active = True; self.process_next_write()

    def process_next_write(self):
        if not getattr(self, "write_batch_active", False) or not self.write_batch_queue: 
            self.write_batch_active = False; self.status.showMessage("범위 자동 집필 완료"); return
        n = self.write_batch_queue.pop(0); self.current_chapter = n
        # ensure chapter is available in UI/list
        self.pm.db.ensure_chapter(n); self.refresh_chapters()
        for i in range(self.chapter_list.count()):
            if int(self.chapter_list.item(i).data(Qt.UserRole)) == n: self.chapter_list.setCurrentRow(i); break
        plot = self.pm.db.get_plot(n)
        if not plot:
            self.append_log(f"{n}화 플롯 없음 - 집필 중단"); self.write_batch_active = False; return
        user = self.build_context(n) + f"\n\n[CURRENT CHAPTER]\n{n}화\n\n4,000~5,000자 내외로 집필하라."
        self._run_ai("chapter_write_batch", WRITER_SYSTEM, trim_text(user, 32000), 0.75, 7000, {"chapter": n})


    def make_light_snapshot(self, chapter: int, text: str) -> str:
        """Lightweight deterministic snapshot for v0.2; full semantic extraction is reserved for v0.3."""
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        last = lines[-8:] if lines else []
        return (
            f"[CHAPTER {chapter} END SNAPSHOT]\n"
            f"마지막 장면/문장:\n" + "\n".join(last) + "\n\n"
            f"주의: v0.2의 자동 상태 스냅샷은 원고 마지막 부분 기반의 경량 기록이며, "
            f"정식 인물/세계관/복선 추출은 v0.3에서 제공한다."
        )

    def rewrite_current(self):
        text = self.editor.toPlainText().strip()
        if not text: QMessageBox.warning(self, "원고 없음", "현재 화에 원고가 없습니다."); return
        user = f"[원고]\n{text}\n\n사건/정보/설정은 변경하지 말고 윤문하라."
        self._run_ai("rewrite", EDITOR_SYSTEM, user, 0.45, 7000)

    def verify_current(self):
        text = self.editor.toPlainText().strip(); plot = self.plot_content.toPlainText().strip()
        context = self.build_context(self.current_chapter, include_full_prev=False)
        user = f"{context}\n\n[현재 플롯]\n{plot}\n\n[현재 원고]\n{text}\n\n문제 목록을 우선 보여라."
        self._run_ai("verify", CHECKER_SYSTEM, trim_text(user, 30000), 0.2, 4000)

    def apply_ai_result(self):
        if not self.last_ai_result: return
        self.editor.setPlainText(self.last_ai_result); self.status.showMessage("AI 결과를 원고에 적용했습니다. 저장하세요.")

    def apply_ai_as_plot(self):
        if not self.last_ai_result: return
        self.plot_content.setPlainText(self.last_ai_result); self.status.showMessage("AI 결과를 플롯에 적용했습니다. 저장하세요.")

    def new_chapter(self): self.add_next_chapter()


class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("새 작품")
        layout = QFormLayout(self)
        self.title_edit = QLineEdit("새로운 소설"); self.genre_edit = QLineEdit("선협")
        self.target_spin = QSpinBox(); self.target_spin.setRange(1, 5000); self.target_spin.setValue(500)
        self.length_edit = QLineEdit("4,000~5,000자"); self.folder_edit = QLineEdit(str(Path.home() / "NovelProjects" / "새로운_소설"))
        browse = QPushButton("찾기"); browse.clicked.connect(self.browse)
        folder = QHBoxLayout(); folder.addWidget(self.folder_edit); folder.addWidget(browse)
        layout.addRow("작품명", self.title_edit); layout.addRow("장르", self.genre_edit); layout.addRow("목표 화수", self.target_spin); layout.addRow("화당 분량", self.length_edit); layout.addRow("저장 폴더", folder)
        b = QHBoxLayout(); ok = QPushButton("생성"); cancel = QPushButton("취소"); ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject); b.addWidget(ok); b.addWidget(cancel); layout.addRow(b)
    def browse(self):
        f = QFileDialog.getExistingDirectory(self, "프로젝트 폴더 선택")
        if f: self.folder_edit.setText(f)


class AISettingsDialog(QDialog):
    def __init__(self, parent, url: str, model: str):
        super().__init__(parent); self.setWindowTitle("AI 설정")
        layout = QFormLayout(self); self.url_edit = QLineEdit(url); self.model_edit = QLineEdit(model)
        layout.addRow("LM Studio 주소", self.url_edit); layout.addRow("모델 ID (비워두면 자동)", self.model_edit); layout.addRow(QLabel("기본값: http://localhost:1234"))
        b = QHBoxLayout(); ok = QPushButton("저장"); cancel = QPushButton("취소"); ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject); b.addWidget(ok); b.addWidget(cancel); layout.addRow(b)


def main():
    app = QApplication(sys.argv); app.setApplicationName(APP_NAME)
    w = MainWindow(); w.setProperty("lm_url", DEFAULT_BASE_URL); w.setProperty("lm_model", ""); w.show(); sys.exit(app.exec())


if __name__ == "__main__": main()
