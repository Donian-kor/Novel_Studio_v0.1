"""서비스 구현체."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from novel_studio.ai.context import ContextManager
from novel_studio.ai.engine import AIEngine
from novel_studio.ai.provider_manager import ProviderManager
from novel_studio.continuity.checker import ContinuityChecker
from novel_studio.core.app_settings import AppSettings
from novel_studio.core.project import ProjectManager
from novel_studio.db.database import now
from novel_studio.db.threadsafe_database import ThreadSafeDatabase as Database
from novel_studio.intelligence.ledger import StateLedger
from novel_studio.manuscript.chapter_writer import ChapterWriter
from novel_studio.memory.memory_manager import MemoryManager
from novel_studio.plot.plot_manager import PlotManager
from novel_studio.utils.text import count_chars
from novel_studio.services.interfaces import (
    AIService,
    ChapterInfo,
    ContinuityResult,
    ContextService,
    ContinuityService,
    DatabaseService,
    ExportService,
    MemoryService,
    ProjectService,
    SettingsService,
    WritingService,
)


class ProjectServiceImpl(ProjectService):
    def __init__(self, project_manager: ProjectManager, db: Database) -> None:
        self.pm = project_manager
        self.db = db

    def get_settings(self) -> dict:
        return dict(self.pm.settings)

    def save_settings(self, settings: dict) -> None:
        self.pm.save_settings(settings)
        total = int(self.pm.settings.get("target_chapters", 500))
        target = int(self.pm.settings.get("chapter_chars", 5000))
        self.db.ensure_chapters(total, target)

    def get_chapter_count(self) -> int:
        return int(self.pm.settings.get("target_chapters", 500))

    def get_chapter_info(self, chapter: int) -> Optional[ChapterInfo]:
        row = self.db.chapter(chapter)
        if not row:
            return None
        return ChapterInfo(
            number=row["number"],
            title=row["title"],
            status=row["status"],
            char_count=row["char_count"],
            char_count_spaces=row["char_count_spaces"],
            target_chars=row["target_chars"],
        )

    def update_chapter(
        self,
        chapter: int,
        title: str,
        status: str,
        char_count: int,
        char_count_spaces: int,
        target_chars: int,
    ) -> None:
        self.db.set_chapter_meta(
            chapter, title, status, char_count, char_count_spaces, target_chars
        )


class AIServiceImpl(AIService):
    def __init__(self, ai_engine: AIEngine) -> None:
        self.ai = ai_engine

    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 60,
    ) -> str:
        return self.ai.generate(
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def generate_stream(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 60,
    ):
        return self.ai.generate_stream(
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def list_models(self) -> list:
        return self.ai.providers.provider().list_models()


class DatabaseServiceImpl(DatabaseService):
    def __init__(self, db: Database, project_manager: ProjectManager) -> None:
        self.db = db
        self.pm = project_manager

    def get_chapters(self) -> List[ChapterInfo]:
        rows = self.db.chapters()
        return [
            ChapterInfo(
                number=r["number"],
                title=r["title"],
                status=r["status"],
                char_count=r["char_count"],
                char_count_spaces=r["char_count_spaces"],
                target_chars=r["target_chars"],
            )
            for r in rows
        ]

    def get_chapter_content(self, chapter: int) -> str:
        row = self.db.chapter(chapter)
        return row["content"] if row else ""

    def save_chapter(self, chapter: int, content: str) -> None:
        text = content or ""
        self.pm.save_chapter(chapter, text)
        row = self.db.chapter(chapter)
        title = row["title"] if row else f"{int(chapter)}화"
        target = int(self.pm.settings.get("chapter_chars", 5000))
        self.db.set_chapter_meta(
            int(chapter), title, "작성완료" if text.strip() else "미작성",
            count_chars(text), count_chars(text, True), target
        )

    def get_chapter_plan(self, chapter: int) -> Optional[str]:
        row = self.db.chapter_plan(chapter)
        return row["content"] if row else None

    def save_chapter_plan(
        self, chapter: int, title: str, content: str, status: str
    ) -> None:
        self.db.save_chapter_plan(chapter, title, content, status)

    def get_continuity_checks(self, chapter: int) -> List[ContinuityResult]:
        rows = self.db.continuity_for_chapter(chapter)
        return [
            ContinuityResult(
                chapter=r["chapter_number"],
                severity=r["severity"],
                category=r["category"],
                message=r["message"],
                evidence=r["evidence"],
            )
            for r in rows
        ]

    def add_continuity_check(
        self,
        chapter: int,
        severity: str,
        category: str,
        message: str,
        evidence: str,
    ) -> None:
        self.db.add_continuity(
            chapter, severity, category, message, evidence
        )


class ContextServiceImpl(ContextService):
    def __init__(self, context_manager: ContextManager) -> None:
        self.cm = context_manager

    def build_context(self, chapter: int, extra: str = "") -> str:
        return self.cm.build(chapter, extra)

    def get_token_budget(self) -> int:
        try:
            return int(self.cm.settings.data["ai"].get("context_budget_tokens", 60000))
        except Exception:
            return 60000


class SettingsServiceImpl(SettingsService):
    def __init__(self, app_settings: AppSettings, providers: ProviderManager) -> None:
        self.app = app_settings
        self.providers = providers

    def get_active_provider(self) -> str:
        return self.app.data.get("active_provider", "lmstudio")

    def get_provider_config(self, provider_id: str) -> dict:
        return self.providers.config(provider_id)

    def save_provider_config(self, provider_id: str, config: dict) -> None:
        self.providers.set_config(provider_id, config)

    def get_ai_settings(self) -> dict:
        return {
            "active_provider": self.app.data.get("active_provider", "lmstudio"),
            "providers": self.app.data.get("providers", {}),
        }


class ContinuityServiceImpl(ContinuityService):
    def __init__(self, checker: ContinuityChecker, plot_manager: PlotManager) -> None:
        self.checker = checker
        self.plot_manager = plot_manager

    def check_chapter(self, chapter: int, text: str) -> ContinuityResult:
        out = self.checker.check(chapter, text)
        severity = "warning" if any(x in out for x in ("오류", "문제", "실패")) else "info"
        if "플롯" in out:
            category = "plot"
        elif "인물" in out:
            category = "character"
        else:
            category = "consistency"
        return ContinuityResult(
            chapter=chapter,
            severity=severity,
            category=category,
            message=out,
            evidence="",
        )

    def audit_long_form(
        self,
        size: int = 50,
        progress_callback=None,
        cancelled_check=None,
    ) -> str:
        return self.plot_manager.audit_long_form(
            size=size,
            progress=progress_callback,
            cancelled_check=cancelled_check,
        )


class WritingServiceImpl(WritingService):
    def __init__(
        self,
        writer: ChapterWriter,
        ai_engine: AIEngine,
        checker: ContinuityChecker,
    ) -> None:
        self.writer = writer
        self.ai = ai_engine
        self.checker = checker

    def write_chapter(self, chapter: int, stream_callback=None) -> str:
        chunks: list[str] = []
        for token in self.writer.write_stream(chapter):
            if token:
                chunks.append(token)
                if stream_callback:
                    stream_callback(token)
        return "".join(chunks)

    def revise_chapter(self, text: str) -> str:
        return self.ai.generate(
            "사건과 설정을 변경하지 말고 다음 원고를 자연스럽게 윤문하라. 본문만 출력.\n" + text,
            temperature=0.38,
            max_tokens=14000,
        )

    def check_consistency(self, chapter: int, text: str) -> str:
        return self.checker.check(chapter, text)

    def adjust_length(self, text: str, target: int, tolerance: int) -> str:
        return self.writer.adjust(text, target, tolerance)


class MemoryServiceImpl(MemoryService):
    def __init__(self, memory_manager: MemoryManager, db: Database) -> None:
        self.memory = memory_manager
        self.db = db

    def update_memory(self, chapter: int, text: str, previous_state: str) -> tuple:
        return self.memory.update(chapter, text, previous_state)

    def get_memory_notes(self) -> str:
        return self.db.get_meta("memory_notes", "")

    def save_memory_notes(self, notes: str) -> bool:
        if not notes.strip():
            return False
        self.db.set_meta("memory_notes", notes)
        return True


class ExportServiceImpl(ExportService):
    def __init__(self, project_manager: ProjectManager) -> None:
        self.pm = project_manager

    def export_manuscript(self) -> str:
        return self.pm.export_all_chapters()


def create_services(project_root: str | Path) -> Dict[str, object]:
    """서비스 팩토리 호환 함수."""
    root = Path(project_root)
    pm = ProjectManager()
    pm.open(root)
    app = AppSettings()
    db = Database(root / "novel.db")
    total = int(pm.settings.get("target_chapters", 500))
    target = int(pm.settings.get("chapter_chars", 5000))
    db.ensure_chapters(total, target)
    providers = ProviderManager(app)
    ai = AIEngine(providers, app)
    context = ContextManager(db, pm, app)
    plot = PlotManager(db, ai, pm)
    checker = ContinuityChecker(db, ai, context)
    writer = ChapterWriter(db, ai, pm, context)
    memory = MemoryManager(db, ai, StateLedger(db))
    return {
        "project": ProjectServiceImpl(pm, db),
        "ai": AIServiceImpl(ai),
        "db": DatabaseServiceImpl(db, pm),
        "context": ContextServiceImpl(context),
        "settings": SettingsServiceImpl(app, providers),
        "continuity": ContinuityServiceImpl(checker, plot),
        "writing": WritingServiceImpl(writer, ai, checker),
        "memory": MemoryServiceImpl(memory, db),
        "export": ExportServiceImpl(pm),
        "_db": db,
        "_pm": pm,
        "_app": app,
        "_providers": providers,
        "_ai": ai,
        "_context": context,
        "_plot": plot,
        "_checker": checker,
        "_writer": writer,
        "_memory": memory,
    }
