from __future__ import annotations

import json
import os
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
    QVBoxLayout, QWidget, QProgressBar, QCheckBox
)

APP_NAME = "Novel Studio"
DEFAULT_BASE_URL = "http://localhost:1234"


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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
            "INSERT INTO chapters(number,file_path,created_at,updated_at) VALUES(?,?,?,?,?)",
            (number, f"chapters/{number:03d}.txt", now(), now()),
        )
        self.conn.commit()

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

    def chunks(self):
        return self.conn.execute("SELECT * FROM chunks ORDER BY start_chapter").fetchall()

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
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + "/v1/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
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
        for p in (paths.chapters, paths.backups, paths.exports, paths.temp):
            ensure_dir(p)
        settings = {
            "title": title,
            "genre": genre,
            "target_chapters": target_chapters,
            "chapter_length": chapter_length,
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
        }
        ensure_dir(paths.chapters)
        ensure_dir(paths.backups)
        ensure_dir(paths.exports)
        ensure_dir(paths.temp)

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
        self.db.update_chapter(number, title, status, len(text.replace("\n", "")))


WRITER_SYSTEM = """당신은 한국 장편 웹소설 전문 작가다.
기존 설정과 플롯을 임의로 변경하지 않는다.
지나친 설명보다 장면, 행동, 대화, 감각으로 보여준다.
문장과 표현의 반복을 피한다.
대사는 위아래 한 줄씩 띄운다.
소설 본문을 요청받으면 본문만 출력한다. 해설이나 메모를 덧붙이지 않는다.
AI가 쓴 티가 나는 기계적인 표현을 피한다.
"""

PLANNER_SYSTEM = """당신은 한국 장편 웹소설의 총괄 플래너다.
주어진 짧은 아이디어를 바탕으로 일관된 장편 작품 기획을 설계한다.
장르적 매력, 장기 갈등, 인물 성장, 세계관 확장, 복선과 회수를 고려한다.
500화를 요청받더라도 한 번에 세부 화별 원고를 만들지 말고 상위 구조를 먼저 설계한다.
결과는 명확한 제목과 섹션으로 작성한다.
"""

PLOTTER_SYSTEM = """당신은 장편 웹소설 플롯 설계자다.
반드시 아래 화별 플롯 형식을 지킨다.

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

5화 청크를 만들 경우 각 화를 독립적으로 작성하되 청크 전체의 흐름이 하나의 작은 사건 단위를 이루게 한다.
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1450, 900)
        self.pm = ProjectManager()
        self.ai_thread: QThread | None = None
        self.ai_worker: AIWorker | None = None
        self.last_ai_result = ""
        self.last_ai_model = ""
        self.job_meta = {}
        self.current_chapter = 1
        self._build_menu()
        self._build_ui()
        self._set_enabled(False)

    def _build_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("파일")
        new_action = QAction("새 작품", self)
        new_action.triggered.connect(self.create_project)
        open_action = QAction("작품 열기", self)
        open_action.triggered.connect(self.open_project)
        save_action = QAction("원고 저장", self)
        save_action.triggered.connect(self.save_current)
        settings_action = QAction("AI 설정", self)
        settings_action.triggered.connect(self.show_ai_settings)
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        file_menu.addAction(settings_action)

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

        # left
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("화 목록"))
        self.chapter_list = QListWidget()
        self.chapter_list.currentRowChanged.connect(self.chapter_selected)
        left_layout.addWidget(self.chapter_list, 1)
        add_chapter = QPushButton("다음 화 추가")
        add_chapter.clicked.connect(self.add_next_chapter)
        left_layout.addWidget(add_chapter)
        splitter.addWidget(left)

        # center tabs
        center = QTabWidget()
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("원고를 입력하세요. TXT로 저장됩니다.")
        self.editor.textChanged.connect(self.on_editor_changed)
        center.addTab(self.editor, "원고")

        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        self.plot_title = QLineEdit()
        self.plot_content = QPlainTextEdit()
        self.plot_content.setPlaceholderText("현재 화의 플롯을 입력하거나 AI로 생성하세요.")
        plot_layout.addWidget(QLabel("화 제목"))
        plot_layout.addWidget(self.plot_title)
        plot_layout.addWidget(QLabel("플롯"))
        plot_layout.addWidget(self.plot_content, 1)
        plot_buttons = QHBoxLayout()
        self.ai_plot_btn = QPushButton("AI 화별 플롯")
        self.ai_plot_btn.clicked.connect(self.generate_chapter_plot)
        self.save_plot_btn = QPushButton("플롯 저장")
        self.save_plot_btn.clicked.connect(self.save_plot)
        plot_buttons.addWidget(self.ai_plot_btn)
        plot_buttons.addWidget(self.save_plot_btn)
        plot_layout.addLayout(plot_buttons)
        center.addTab(plot_widget, "화별 플롯")

        planning_widget = QWidget()
        planning_layout = QVBoxLayout(planning_widget)
        self.seed_edit = QPlainTextEdit()
        self.seed_edit.setPlaceholderText("짧은 아이디어/시드 입력\n예: 시간 회귀 능력을 가진 수련자의 선협 이야기")
        planning_layout.addWidget(QLabel("아이디어 / Seed"))
        planning_layout.addWidget(self.seed_edit, 1)
        self.target_spin = QSpinBox()
        self.target_spin.setRange(1, 5000)
        self.target_spin.setValue(500)
        self.chunk_spin = QSpinBox()
        self.chunk_spin.setRange(1, 20)
        self.chunk_spin.setValue(5)
        form = QFormLayout()
        form.addRow("목표 화수", self.target_spin)
        form.addRow("플롯 청크 크기", self.chunk_spin)
        planning_layout.addLayout(form)
        self.master_plan = QPlainTextEdit()
        self.master_plan.setPlaceholderText("AI가 생성한 마스터 플랜이 여기에 표시됩니다.")
        planning_layout.addWidget(QLabel("마스터 플랜"))
        planning_layout.addWidget(self.master_plan, 2)
        buttons = QHBoxLayout()
        self.ai_plan_btn = QPushButton("AI 장편 기획")
        self.ai_plan_btn.clicked.connect(self.generate_master_plan)
        self.ai_chunk_btn = QPushButton("선택 구간 Chunk 플롯")
        self.ai_chunk_btn.clicked.connect(self.generate_selected_chunk)
        buttons.addWidget(self.ai_plan_btn)
        buttons.addWidget(self.ai_chunk_btn)
        planning_layout.addLayout(buttons)
        center.addTab(planning_widget, "AI 기획")

        self.ai_result = QPlainTextEdit()
        self.ai_result.setReadOnly(True)
        ai_widget = QWidget()
        ai_layout = QVBoxLayout(ai_widget)
        ai_layout.addWidget(QLabel("AI 결과 미리보기"))
        ai_layout.addWidget(self.ai_result, 1)
        ai_buttons = QHBoxLayout()
        self.apply_ai_btn = QPushButton("현재 작업에 적용")
        self.apply_ai_btn.clicked.connect(self.apply_ai_result)
        self.use_as_plot_btn = QPushButton("플롯으로 적용")
        self.use_as_plot_btn.clicked.connect(self.apply_ai_as_plot)
        ai_buttons.addWidget(self.apply_ai_btn)
        ai_buttons.addWidget(self.use_as_plot_btn)
        ai_layout.addLayout(ai_buttons)
        center.addTab(ai_widget, "AI 결과")

        splitter.addWidget(center)

        # right
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("현재 상태"))
        self.state_label = QLabel("작품을 열어주세요.")
        self.state_label.setWordWrap(True)
        right_layout.addWidget(self.state_label)
        right_layout.addWidget(QLabel("최근 AI/작업 로그"))
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        right_layout.addWidget(self.log, 1)
        splitter.addWidget(right)

        splitter.setSizes([200, 950, 280])

        bottom = QHBoxLayout()
        self.new_chapter_btn = QPushButton("새 화")
        self.next_write_btn = QPushButton("이어쓰기")
        self.edit_btn = QPushButton("AI 윤문")
        self.verify_btn = QPushButton("기본 검증")
        self.save_btn = QPushButton("저장")
        self.count_label = QLabel("0자")
        for btn, slot in [
            (self.new_chapter_btn, self.new_chapter),
            (self.next_write_btn, self.continue_writing),
            (self.edit_btn, self.rewrite_current),
            (self.verify_btn, self.verify_current),
            (self.save_btn, self.save_current),
        ]:
            btn.clicked.connect(slot)
            bottom.addWidget(btn)
        bottom.addStretch()
        bottom.addWidget(self.count_label)
        layout.addLayout(bottom)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("준비됨")
        layout.addWidget(self.progress)

    def _set_enabled(self, value: bool):
        widgets = [
            self.chapter_list, self.ai_test_btn, self.ai_plan_btn, self.ai_chunk_btn,
            self.new_chapter_btn, self.next_write_btn, self.edit_btn, self.verify_btn,
            self.save_btn, self.ai_plot_btn, self.save_plot_btn, self.target_spin, self.chunk_spin,
            self.editor, self.seed_edit, self.plot_title, self.plot_content,
            self.apply_ai_btn, self.use_as_plot_btn,
        ]
        for w in widgets:
            w.setEnabled(value)

    def append_log(self, text: str):
        self.log.appendPlainText(f"[{datetime.now().strftime('%H:%M:%S')}] {text}")

    def create_project(self):
        dialog = NewProjectDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        root = Path(dialog.folder_edit.text()).expanduser()
        try:
            self.pm.create(root, dialog.title_edit.text().strip(), dialog.genre_edit.text().strip(), dialog.target_spin.value(), dialog.length_edit.text().strip())
            self.open_loaded_project()
        except Exception as e:
            QMessageBox.critical(self, "생성 실패", str(e))

    def open_project(self):
        folder = QFileDialog.getExistingDirectory(self, "프로젝트 폴더 선택")
        if not folder:
            return
        try:
            self.pm.open(Path(folder))
            self.open_loaded_project()
        except Exception as e:
            QMessageBox.critical(self, "열기 실패", str(e))

    def open_loaded_project(self):
        assert self.pm.active
        self.project_label.setText(f"작품: {self.pm.settings.get('title', self.pm.paths.root.name)}")
        self.target_spin.setValue(int(self.pm.settings.get('target_chapters', 500)))
        self.master_plan.setPlainText(self.pm.db.get_meta("master_plan", ""))
        self.refresh_chapters()
        if self.chapter_list.count():
            self.chapter_list.setCurrentRow(0)
        self._set_enabled(True)
        self.status.showMessage(f"프로젝트 열림: {self.pm.paths.root}")
        self.append_log("프로젝트를 열었습니다.")

    def refresh_chapters(self):
        assert self.pm.db is not None
        self.chapter_list.blockSignals(True)
        self.chapter_list.clear()
        rows = self.pm.db.chapter_rows()
        existing = {int(r['number']) for r in rows}
        for n in range(1, max(1, self.target_spin.value()) + 1):
            if n not in existing:
                # 목록 전체를 미리 DB에 만들지 않고 보이는 번호만 생성
                if n > 50 and not rows:
                    break
                self.pm.db.ensure_chapter(n)
        rows = self.pm.db.chapter_rows()
        for row in rows:
            item = QListWidgetItem(f"{row['number']:03d}  {row['status']}")
            item.setData(Qt.UserRole, int(row['number']))
            self.chapter_list.addItem(item)
        self.chapter_list.blockSignals(False)

    def chapter_selected(self, row: int):
        if row < 0 or not self.pm.active:
            return
        number = int(self.chapter_list.item(row).data(Qt.UserRole))
        self.load_chapter(number)

    def load_chapter(self, number: int):
        self.current_chapter = number
        text = self.pm.load_chapter(number)
        self.editor.blockSignals(True)
        self.editor.setPlainText(text)
        self.editor.blockSignals(False)
        row = self.pm.db.chapter(number)
        self.plot_title.setText(row['title'] if row else '')
        plot = self.pm.db.get_plot(number)
        self.plot_content.setPlainText(plot['content'] if plot else '')
        self.update_count()
        self.update_state_panel()

    def update_count(self):
        txt = self.editor.toPlainText()
        self.count_label.setText(f"{len(txt.replace(chr(10), '')):,}자")

    def on_editor_changed(self):
        self.update_count()

    def add_next_chapter(self):
        if not self.pm.active:
            return
        number = self.current_chapter + 1
        self.pm.db.ensure_chapter(number)
        self.refresh_chapters()
        for i in range(self.chapter_list.count()):
            if int(self.chapter_list.item(i).data(Qt.UserRole)) == number:
                self.chapter_list.setCurrentRow(i)
                break

    def save_current(self):
        if not self.pm.active:
            return
        title = self.plot_title.text().strip()
        self.pm.save_chapter(self.current_chapter, self.editor.toPlainText(), title)
        self.pm.db.ensure_chapter(self.current_chapter)
        self.pm.db.update_chapter(self.current_chapter, title, "확정" if self.editor.toPlainText().strip() else "미작성", len(self.editor.toPlainText().replace("\n", "")))
        self.refresh_chapters()
        self.status.showMessage(f"{self.current_chapter:03d}화 저장 완료")
        self.append_log(f"{self.current_chapter:03d}화 저장")

    def save_plot(self):
        if not self.pm.active:
            return
        self.pm.db.ensure_chapter(self.current_chapter)
        self.pm.db.save_plot(self.current_chapter, self.plot_title.text().strip(), self.plot_content.toPlainText())
        self.status.showMessage(f"{self.current_chapter:03d}화 플롯 저장")
        self.append_log(f"{self.current_chapter:03d}화 플롯 저장")

    def update_state_panel(self):
        if not self.pm.active:
            return
        row = self.pm.db.chapter(self.current_chapter)
        text = self.editor.toPlainText()
        title = row['title'] if row else ''
        status = row['status'] if row else '미작성'
        self.state_label.setText(
            f"작품: {self.pm.settings.get('title','')}\n"
            f"현재 화: {self.current_chapter:03d}화\n"
            f"제목: {title or '(제목 없음)'}\n"
            f"상태: {status}\n"
            f"분량: {len(text.replace(chr(10), '')):,}자"
        )

    def lm_client(self) -> LMStudioClient:
        return LMStudioClient(self.window().property("lm_url") or DEFAULT_BASE_URL, self.window().property("lm_model") or "")

    def show_ai_settings(self):
        dialog = AISettingsDialog(self, self.property("lm_url") or DEFAULT_BASE_URL, self.property("lm_model") or "")
        if dialog.exec() == QDialog.Accepted:
            self.setProperty("lm_url", dialog.url_edit.text().strip())
            self.setProperty("lm_model", dialog.model_edit.text().strip())
            self.ai_label.setText(f"AI: {dialog.model_edit.text().strip() or '자동'}")
            self.status.showMessage("AI 설정 저장")

    def test_ai(self):
        try:
            client = self.lm_client()
            models = client.list_models()
            if models:
                self.setProperty("lm_model", client.model or models[0])
                self.ai_label.setText(f"AI: {models[0]}")
                QMessageBox.information(self, "연결 성공", "LM Studio 연결 성공\n\n모델:\n" + "\n".join(models[:10]))
                self.append_log(f"LM Studio 연결 성공: {models[0]}")
            else:
                raise RuntimeError("모델이 없습니다.")
        except Exception as e:
            QMessageBox.critical(self, "연결 실패", str(e))
            self.append_log(f"LM Studio 연결 실패: {e}")

    def _run_ai(self, job_type: str, system: str, user: str, temp: float = 0.7, max_tokens: int = 5000):
        client = self.lm_client()
        model = client.model
        job_id = self.pm.db.add_job(job_type, str(self.current_chapter), model, len(system) + len(user))
        self.job_meta[job_id] = {"job_type": job_type, "target": str(self.current_chapter)}
        thread = QThread()
        worker = AIWorker(client, system, user, temp, max_tokens)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(lambda text, m: self.ai_finished(job_id, text, m))
        worker.failed.connect(lambda err: self.ai_failed(job_id, err))
        worker.progress.connect(self.status.showMessage)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self.ai_thread = thread
        self.ai_worker = worker
        self.progress.show()
        self.append_log(f"AI 작업 시작: {job_type}")
        thread.start()

    def ai_finished(self, job_id: int, text: str, model: str):
        self.progress.hide()
        self.last_ai_result = text
        self.last_ai_model = model
        self.ai_result.setPlainText(text)
        self.pm.db.finish_job(job_id, "완료", len(text))
        meta = self.job_meta.pop(job_id, {})
        job_type = meta.get("job_type", "")
        try:
            if job_type == "master_plan":
                self.master_plan.setPlainText(text)
                self.pm.db.set_meta("master_plan", text)
            elif job_type == "chunk_plot":
                m = re.search(r"(?:Chunk|청크)[^0-9]*(\d+)[^0-9]+(?:~|-)\s*(\d+)", text, re.I)
                start, end = (self.current_chapter, min(self.target_spin.value(), self.current_chapter + self.chunk_spin.value() - 1))
                if m:
                    start, end = int(m.group(1)), int(m.group(2))
                snapshot = ""
                snap_match = re.search(r"\[CHUNK SNAPSHOT\](.*)", text, re.I | re.S)
                if snap_match:
                    snapshot = snap_match.group(1).strip()
                self.pm.db.save_chunk(start, end, "완료", "", text, snapshot)
            elif job_type == "chapter_plot":
                title = self.plot_title.text().strip()
                self.plot_content.setPlainText(text)
                self.pm.db.ensure_chapter(self.current_chapter)
                self.pm.db.save_plot(self.current_chapter, title, text)
        except Exception as e:
            self.append_log(f"AI 결과 저장 보조 작업 실패: {e}")
        self.status.showMessage(f"AI 생성 완료 - {len(text):,}자")
        self.append_log(f"AI 완료: {len(text):,}자 / {model} / {job_type}")

    def ai_failed(self, job_id: int, err: str):
        self.progress.hide()
        self.pm.db.finish_job(job_id, "실패", 0, err)
        QMessageBox.critical(self, "AI 작업 실패", err)
        self.status.showMessage("AI 작업 실패")
        self.append_log(f"AI 실패: {err}")

    def generate_master_plan(self):
        seed = self.seed_edit.toPlainText().strip()
        if not seed:
            QMessageBox.warning(self, "입력 필요", "아이디어/Seed를 입력하세요.")
            return
        target = self.target_spin.value()
        genre = self.pm.settings.get("genre", "장편 웹소설")
        user = f"""장르: {genre}\n목표 분량: {target}화\n\n[아이디어]\n{seed}\n\n다음 구조로 장편 기획을 설계해라.\n1. 작품 제목 후보\n2. 로그라인\n3. 세계관 핵심\n4. 주인공과 주요 인물\n5. 핵심 갈등\n6. 수련/성장 구조\n7. 전체 결말\n8. 전체 {target}화의 부/막/아크 구조\n9. 핵심 복선 목록\n10. 장편에서 절대 바뀌면 안 되는 Plan Contract\n"""
        self._run_ai("master_plan", PLANNER_SYSTEM, user, 0.85, 7000)

    def generate_selected_chunk(self):
        start, ok = self._ask_int("청크 시작 화", self.current_chapter)
        if not ok:
            return
        size = self.chunk_spin.value()
        end = min(self.target_spin.value(), start + size - 1)
        master = self.master_plan.toPlainText().strip()
        previous_chunk = ""
        chunks = self.pm.db.chunks()
        for row in reversed(chunks):
            if row["end_chapter"] < start:
                previous_chunk = row["snapshot"] or row["content"]
                break
        user = f"""[MASTER PLAN]\n{master[:16000]}\n\n[이전 청크 상태]\n{previous_chunk[:10000]}\n\n[이번 청크]\n{start}~{end}화\n\n각 화의 플롯을 정해진 형식으로 만들어라.\n청크 전체가 하나의 사건 단위로 이어져야 한다.\n마지막에 [CHUNK SNAPSHOT]을 작성하고, 다음 청크로 이어질 상태/미해결 사건/필수 연결점을 정리하라.\n"""
        self._run_ai("chunk_plot", PLOTTER_SYSTEM, user, 0.75, 7000)

    def generate_chapter_plot(self):
        master = self.master_plan.toPlainText().strip()
        seed = self.seed_edit.toPlainText().strip()
        prev = self.pm.load_chapter(self.current_chapter - 1) if self.current_chapter > 1 else ""
        user = f"""[작품 아이디어]\n{seed[:6000]}\n\n[마스터 플랜]\n{master[:10000]}\n\n[직전 화]\n{prev[-7000:]}\n\n[현재 화]\n{self.current_chapter}화\n\n현재 화에 맞는 플롯을 아래 고정 형식으로 작성하라.\n[화 번호/제목]\n[목표]\n[시작 상황]\n[핵심 사건]\n[갈등]\n[전환점]\n[인물 변화]\n[세계관 정보]\n[복선]\n[복선 회수]\n[엔딩]\n[다음 화 연결]"""
        self._run_ai("chapter_plot", PLOTTER_SYSTEM, user, 0.75, 4500)

    def continue_writing(self):
        plot = self.plot_content.toPlainText().strip()
        prev = self.pm.load_chapter(self.current_chapter - 1) if self.current_chapter > 1 else ""
        user = f"""[현재 화 플롯]\n{plot[:10000]}\n\n[직전 화 원고]\n{prev[-10000:]}\n\n[현재 화]\n{self.current_chapter}화\n\n이 플롯을 충실히 따르면서 한국 웹소설 본문을 4,000~5,000자 내외로 작성하라.\n직전 화의 문체와 장면을 자연스럽게 이어가되 내용을 반복하지 마라."""
        self._run_ai("chapter_write", WRITER_SYSTEM, user, 0.75, 7000)

    def new_chapter(self):
        self.add_next_chapter()

    def rewrite_current(self):
        text = self.editor.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "원고 없음", "현재 화에 원고가 없습니다.")
            return
        user = f"""다음 원고를 사건/설정/정보는 바꾸지 않고 윤문하라.\n\n목표:\n- 문장 단절 개선\n- 반복 표현 감소\n- 대화 자연스러움 개선\n- 장면 전환 개선\n- 감정선의 과잉 설명 감소\n- AI 느낌의 표현 제거\n- 분량은 크게 줄이지 않는다.\n\n[원고]\n{text}\n"""
        self._run_ai("rewrite", WRITER_SYSTEM + "\n윤문 시 새 사건을 추가하지 않는다.", user, 0.45, 7000)

    def verify_current(self):
        text = self.editor.toPlainText().strip()
        plot = self.plot_content.toPlainText().strip()
        user = f"""현재 화의 기본 검증을 수행하라. 점수보다 문제 목록을 명확히 보여라.\n\n[플롯]\n{plot}\n\n[원고]\n{text}\n\n검사 항목:\n1. 플롯 이탈\n2. 시간/장소 모순\n3. 인물 행동/지식 모순\n4. 반복 표현\n5. 문장 이상\n6. 엔딩 연결 부족\n\n문제가 없다면 '주요 문제 없음'이라고 써라."""
        self._run_ai("verify", "당신은 장편소설 품질검수자다. 사실과 설정을 추측해 새로 만들지 말고 주어진 정보만 검토한다.", user, 0.2, 3500)

    def apply_ai_result(self):
        if not self.last_ai_result:
            QMessageBox.information(self, "AI 결과 없음", "먼저 AI 작업을 실행하세요.")
            return
        self.editor.setPlainText(self.last_ai_result)
        self.status.showMessage("AI 결과를 원고 편집기에 적용했습니다. 저장을 눌러 확정하세요.")
        self.append_log("AI 결과 → 원고 편집기에 적용")

    def apply_ai_as_plot(self):
        if not self.last_ai_result:
            return
        self.plot_content.setPlainText(self.last_ai_result)
        self.status.showMessage("AI 결과를 플롯으로 적용했습니다. 저장하세요.")

    def _ask_int(self, label: str, default: int):
        dlg = QDialog(self)
        dlg.setWindowTitle(label)
        layout = QVBoxLayout(dlg)
        spin = QSpinBox()
        spin.setRange(1, self.target_spin.value())
        spin.setValue(default)
        layout.addWidget(spin)
        row = QHBoxLayout()
        ok = QPushButton("확인")
        cancel = QPushButton("취소")
        ok.clicked.connect(dlg.accept)
        cancel.clicked.connect(dlg.reject)
        row.addWidget(ok)
        row.addWidget(cancel)
        layout.addLayout(row)
        accepted = dlg.exec() == QDialog.Accepted
        return (spin.value(), True) if accepted else (default, False)


class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("새 작품")
        layout = QFormLayout(self)
        self.title_edit = QLineEdit("새로운 소설")
        self.genre_edit = QLineEdit("선협")
        self.target_spin = QSpinBox()
        self.target_spin.setRange(1, 5000)
        self.target_spin.setValue(500)
        self.length_edit = QLineEdit("4,000~5,000자")
        self.folder_edit = QLineEdit(str(Path.home() / "NovelProjects" / "새로운_소설"))
        browse = QPushButton("찾기")
        browse.clicked.connect(self.browse)
        folder = QHBoxLayout()
        folder.addWidget(self.folder_edit)
        folder.addWidget(browse)
        layout.addRow("작품명", self.title_edit)
        layout.addRow("장르", self.genre_edit)
        layout.addRow("목표 화수", self.target_spin)
        layout.addRow("화당 분량", self.length_edit)
        layout.addRow("저장 폴더", folder)
        buttons = QHBoxLayout()
        ok = QPushButton("생성")
        cancel = QPushButton("취소")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        layout.addRow(buttons)

    def browse(self):
        folder = QFileDialog.getExistingDirectory(self, "프로젝트 폴더 선택")
        if folder:
            self.folder_edit.setText(folder)


class AISettingsDialog(QDialog):
    def __init__(self, parent, url: str, model: str):
        super().__init__(parent)
        self.setWindowTitle("AI 설정")
        layout = QFormLayout(self)
        self.url_edit = QLineEdit(url)
        self.model_edit = QLineEdit(model)
        layout.addRow("LM Studio 주소", self.url_edit)
        layout.addRow("모델 ID (비워두면 자동)", self.model_edit)
        note = QLabel("기본값: http://localhost:1234")
        note.setWordWrap(True)
        layout.addRow(note)
        buttons = QHBoxLayout()
        ok = QPushButton("저장")
        cancel = QPushButton("취소")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        layout.addRow(buttons)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = MainWindow()
    window.setProperty("lm_url", DEFAULT_BASE_URL)
    window.setProperty("lm_model", "")
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
