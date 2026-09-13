"""
서비스 팩토리 - 모든 서비스와 컨트롤러 인스턴스 생성
"""
from pathlib import Path
from novel_studio.db.threadsafe_database import ThreadSafeDatabase as Database
from novel_studio.ai.provider_manager import ProviderManager
from novel_studio.ai.engine import AIEngine
from novel_studio.ai.context import ContextManager
from novel_studio.continuity.checker import ContinuityChecker
from novel_studio.memory.memory_manager import MemoryManager
from novel_studio.intelligence.ledger import StateLedger
from novel_studio.core.app_settings import AppSettings
from novel_studio.core.project import ProjectManager
from novel_studio.plot.plot_manager import PlotManager
from novel_studio.manuscript.chapter_writer import ChapterWriter
from novel_studio.memory.memory_manager import MemoryManager
from novel_studio.intelligence.ledger import StateLedger
from novel_studio.intelligence.diff import MasterDiffService
from novel_studio.services.interfaces import (
    ProjectService, AIService, DatabaseService, ContextService,
    SettingsService, ContinuityService, WritingService, MemoryService, ExportService
)
from novel_studio.services.implementations import (
    ProjectServiceImpl, AIServiceImpl, DatabaseServiceImpl,
    ContextServiceImpl, SettingsServiceImpl, ContinuityServiceImpl,
    WritingServiceImpl, MemoryServiceImpl, ExportServiceImpl
)
from novel_studio.controllers.novel_controller import NovelController
from novel_studio.plot.plot_manager import PlotManager
from novel_studio.ai.provider_manager import ProviderManager
from novel_studio.ai.engine import AIEngine
from novel_studio.ai.context import ContextManager
from novel_studio.continuity.checker import ContinuityChecker
from novel_studio.memory.memory_manager import MemoryManager
from novel_studio.intelligence.ledger import StateLedger
from novel_studio.intelligence.diff import MasterDiffService
from novel_studio.core.app_settings import AppSettings
from novel_studio.core.project import ProjectManager
from novel_studio.plot.plot_manager import PlotManager
from novel_studio.manuscript.chapter_writer import ChapterWriter
from novel_studio.memory.memory_manager import MemoryManager
from novel_studio.intelligence.ledger import StateLedger
from novel_studio.intelligence.diff import MasterDiffService
from novel_studio.core.app_settings import AppSettings
from novel_studio.core.project import ProjectManager
from pathlib import Path


class ServiceFactory:
    """서비스 및 컨트롤러 팩토리"""
    
    @staticmethod
    def create_all(project_root: str) -> dict:
        """모든 서비스와 컨트롤러 인스턴스 생성"""
        project_root = Path(project_root)
        
        # 핵심 인프라
        db = Database(project_root / 'novel.db')
        pm = ProjectManager()
        pm.open(project_root)
        app = AppSettings()
        providers = ProviderManager(app)
        ai_engine = AIEngine(providers, app)
        
        # Context Manager
        pm_for_context = ProjectManager()
        pm_for_context.open(project_root)
        context_mgr = ContextManager(db, pm, app)
        
        # PlotManager
        plot_mgr = PlotManager(db, ai_engine, pm)
        
        # 서비스 구현체 생성
        project_service = ProjectServiceImpl(pm, db)
        ai_service = AIServiceImpl(ai_engine)
        db_service = DatabaseServiceImpl(db)
        context_service = ContextServiceImpl(context_mgr)
        settings_service = SettingsServiceImpl(app, providers)
        continuity_service = ContinuityServiceImpl(
            ContinuityChecker(db, ai_engine, context_mgr)
        )
        
        writer = ChapterWriter(db, ai_engine, pm, None)
        writing_service = WritingServiceImpl(ai_engine)
        
        memory_service = MemoryServiceImpl(
            MemoryManager(db, ai_engine, None), db
        )
        export_service = ExportServiceImpl(pm)
        
        # 서비스 딕셔너리 구성
        services = {
            'project': project_service,
            'ai': ai_service,
            'db': db_service,
            'context': context_service,
            'settings': settings_service,
            'continuity': continuity_service,
            'writing': writing_service,
            'memory': memory_service,
            'export': export_service,
        }
        
        # Controller 생성
        controller = NovelController({})
        controller.set_services({
            'project': None,
            'ai': None,
            'db': None,
            'context': None,
            'settings': None,
            'continuity': None,
            'writing': None,
            'memory': None,
            'export': None,
        })
        
        return {
            'services': services,
            'controller': controller,
            'db': db,
            'pm': pm,
            'app': app,
            'ai_engine': ai_engine,
            'providers': providers,
            'context_mgr': context_mgr,
            'plot_mgr': plot_mgr,
        }