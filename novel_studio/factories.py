"""애플리케이션 구성요소를 생성하는 단일 팩토리."""
from __future__ import annotations

from pathlib import Path

from novel_studio.ai.context import ContextManager
from novel_studio.ai.engine import AIEngine
from novel_studio.ai.provider_manager import ProviderManager
from novel_studio.controllers.novel_controller import NovelController
from novel_studio.core.app_settings import AppSettings
from novel_studio.core.project import ProjectManager
from novel_studio.db.project_database import ProjectDatabase
from novel_studio.intelligence.diff import MasterDiffService
from novel_studio.manuscript.chapter_writer import ChapterWriter
from novel_studio.plot.plot_manager import PlotManager
from novel_studio.continuity.checker import ContinuityChecker
from novel_studio.services.end_state_service import EndStateService
from novel_studio.services.idea_service import IdeaService
from novel_studio.services.implementations import (
    AIServiceImpl,
    ContextServiceImpl,
    ContinuityServiceImpl,
    DatabaseServiceImpl,
    ExportServiceImpl,
    ProjectServiceImpl,
    SettingsServiceImpl,
    WritingServiceImpl,
)


class ServiceFactory:
    """프로젝트 단위의 모든 서비스와 Controller를 한 번에 만든다."""

    @staticmethod
    def create_all(project_root: str | Path) -> dict:
        root = Path(project_root)
        pm = ProjectManager()
        pm.open(root)
        app = AppSettings()
        db = ProjectDatabase(root)
        db.ensure_chapters(
            int(pm.settings.get("target_chapters", 500)),
            int(pm.settings.get("chapter_chars", 5000)),
        )
        providers = ProviderManager(app)
        ai = AIEngine(providers, app)
        context = ContextManager(db, pm, app)
        plot = PlotManager(db, ai, pm)
        checker = ContinuityChecker(db, ai, context)
        writer = ChapterWriter(db, ai, pm, context)
        end_state = EndStateService(db, ai)
        idea_service = IdeaService(db, ai, pm)
        master_diff = MasterDiffService(db, ai)

        services = {
            "project": ProjectServiceImpl(pm, db),
            "ai": AIServiceImpl(ai),
            "db": DatabaseServiceImpl(db, pm),
            "context": ContextServiceImpl(context),
            "settings": SettingsServiceImpl(app, providers),
            "continuity": ContinuityServiceImpl(checker, plot),
            "writing": WritingServiceImpl(writer, ai, checker),
            "export": ExportServiceImpl(pm),
            "idea": idea_service,
        }
        controller = NovelController()
        controller.set_services(services)
        return {
            "services": services,
            "controller": controller,
            "db": db,
            "pm": pm,
            "app": app,
            "ai_engine": ai,
            "providers": providers,
            "context_mgr": context,
            "plot_mgr": plot,
            "checker": checker,
            "writer": writer,
            "master_diff": master_diff,
            "end_state": end_state,
            "idea_service": idea_service,
        }
