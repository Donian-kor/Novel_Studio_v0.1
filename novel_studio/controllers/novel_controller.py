"""
컨트롤러 - View와 Service 사이의 조정자
"""
from typing import Optional, Callable, List, Dict, Any
from PySide6.QtCore import QObject, Signal
from novel_studio.services.interfaces import (
    ProjectService, AIService, DatabaseService, ContextService,
    SettingsService, ContinuityService, WritingService, MemoryService, ExportService
)
from novel_studio.services.interfaces import (
    ChapterInfo, ContinuityResult, EntityState
)
from novel_studio.jobs.worker import Job, StreamJob
from PySide6.QtCore import QThreadPool
from novel_studio.services.interfaces import (
    ProjectService, AIService, DatabaseService, ContextService,
    SettingsService, ContinuityService, WritingService, MemoryService, ExportService
)
from novel_studio.services.interfaces import (
    ChapterInfo, ContinuityResult, EntityState
)
from novel_studio.jobs.worker import Job, StreamJob
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QMessageBox
from pathlib import Path
from novel_studio.core.app_settings import AppSettings
from novel_studio.core.project import ProjectManager
from novel_studio.db.threadsafe_database import ThreadSafeDatabase as Database
from novel_studio.ai.provider_manager import ProviderManager
from novel_studio.ai.engine import AIEngine
from novel_studio.ai.context import ContextManager
from novel_studio.continuity.checker import ContinuityChecker
from novel_studio.memory.memory_manager import MemoryManager
from novel_studio.intelligence.ledger import StateLedger
from novel_studio.intelligence.diff import MasterDiffService
from novel_studio.manuscript.chapter_writer import ChapterWriter
from novel_studio.memory.memory_manager import MemoryManager
from novel_studio.intelligence.ledger import StateLedger
from novel_studio.intelligence.diff import MasterDiffService
from novel_studio.ai.provider_manager import ProviderManager
from novel_studio.ai.engine import AIEngine
from novel_studio.ai.context import ContextManager
from novel_studio.ai.prompts import (chat_system, entity_extra, master as master_prompt,
                                     contract as contract_prompt,
                                     master_plot as master_plot_prompt, idea as idea_prompt, repair_chapter_plans,
                                     SECTIONS)
from novel_studio.services.idea_service import IdeaService
from novel_studio.planning.master_planner import MasterPlanner
from novel_studio.plot.plot_manager import PlotManager
from novel_studio.plot.parser import parse_chapter_plans, validate_chapter_plans
from novel_studio.manuscript.chapter_writer import ChapterWriter
from novel_studio.memory.memory_manager import MemoryManager
from novel_studio.continuity.checker import ContinuityChecker
from novel_studio.intelligence.ledger import StateLedger
from novel_studio.intelligence.diff import MasterDiffService
from novel_studio.jobs.worker import Job, StreamJob
from novel_studio.ui.dialogs import AISettingsDialog, ProjectSettingsDialog
from novel_studio.utils.text import count_chars, strip_ai_marks, check_spelling
from novel_studio.ai.prompts import (chat_system, entity_extra, master as master_prompt,
                                     contract as contract_prompt,
                                     master_plot as master_plot_prompt, idea as idea_prompt, repair_chapter_plans,
                                     SECTIONS)
from novel_studio.services.idea_service import IdeaService
from novel_studio.planning.master_planner import MasterPlanner
from novel_studio.plot.plot_manager import PlotManager
from novel_studio.plot.parser import parse_chapter_plans, validate_chapter_plans
from novel_studio.manuscript.chapter_writer import ChapterWriter
from novel_studio.memory.memory_manager import MemoryManager
from novel_studio.continuity.checker import ContinuityChecker
from novel_studio.intelligence.ledger import StateLedger
from novel_studio.intelligence.diff import MasterDiffService
from novel_studio.jobs.worker import Job, StreamJob
from novel_studio.ai.provider_manager import ProviderManager
from novel_studio.ai.engine import AIEngine
from novel_studio.ai.context import ContextManager
from novel_studio.ai.prompts import (chat_system, entity_extra, master as master_prompt,
                                     contract as contract_prompt,
                                     master_plot as master_plot_prompt, idea as idea_prompt, repair_chapter_plans,
                                     SECTIONS)
from novel_studio.services.idea_service import IdeaService
from novel_studio.planning.master_planner import MasterPlanner
from novel_studio.plot.plot_manager import PlotManager
from novel_studio.plot.parser import parse_chapter_plans, validate_chapter_plans
from novel_studio.manuscript.chapter_writer import ChapterWriter
from novel_studio.memory.memory_manager import MemoryManager
from novel_studio.continuity.checker import ContinuityChecker
from novel_studio.intelligence.ledger import StateLedger
from novel_studio.intelligence.diff import MasterDiffService
from novel_studio.jobs.worker import Job, StreamJob
from novel_studio.ai.provider_manager import ProviderManager
from novel_studio.ai.engine import AIEngine
from novel_studio.ai.context import ContextManager
from novel_studio.ai.prompts import (chat_system, entity_extra, master as master_prompt,
                                     contract as contract_prompt,
                                     master_plot as master_plot_prompt, idea as idea_prompt, repair_chapter_plans,
                                     SECTIONS)
from novel_studio.services.idea_service import IdeaService
from novel_studio.planning.master_planner import MasterPlanner
from novel_studio.plot.plot_manager import PlotManager
from novel_studio.plot.parser import parse_chapter_plans, validate_chapter_plans
from novel_studio.manuscript.chapter_writer import ChapterWriter
from novel_studio.memory.memory_manager import MemoryManager
from novel_studio.continuity.checker import ContinuityChecker
from novel_studio.intelligence.ledger import StateLedger
from novel_studio.intelligence.diff import MasterDiffService
from novel_studio.jobs.worker import Job, StreamJob
from novel_studio.ai.provider_manager import ProviderManager
from novel_studio.ai.engine import AIEngine
from novel_studio.ai.context import ContextManager
from novel_studio.ai.prompts import (chat_system, entity_extra, master as master_prompt,
                                     contract as contract_prompt,
                                     master_plot as master_plot_prompt, idea as idea_prompt, repair_chapter_plans,
                                     SECTIONS)
from novel_studio.services.idea_service import IdeaService
from novel_studio.planning.master_planner import MasterPlanner
from novel_studio.plot.plot_manager import PlotManager
from novel_studio.plot.parser import parse_chapter_plans, validate_chapter_plans
from novel_studio.manuscript.chapter_writer import ChapterWriter
from novel_studio.memory.memory_manager import MemoryManager
from novel_studio.continuity.checker import ContinuityChecker
from novel_studio.intelligence.ledger import StateLedger
from novel_studio.intelligence.diff import MasterDiffService
from novel_studio.jobs.worker import Job, StreamJob
from novel_studio.ai.provider_manager import ProviderManager
from novel_studio.ai.engine import AIEngine
from novel_studio.ai.context import ContextManager
from novel_studio.ai.prompts import (chat_system, entity_extra, master as master_prompt,
                                     contract as contract_prompt,
                                     master_plot as master_plot_prompt, idea as idea_prompt, repair_chapter_plans,
                                     SECTIONS)
from novel_studio.services.idea_service import IdeaService
from novel_studio.planning.master_planner import MasterPlanner
from novel_studio.plot.plot_manager import PlotManager
from novel_studio.plot.parser import parse_chapter_plans, validate_chapter_plans
from novel_studio.manuscript.chapter_writer import ChapterWriter
from novel_studio.memory.memory_manager import MemoryManager
from novel_studio.continuity.checker import ContinuityChecker
from novel_studio.intelligence.ledger import StateLedger
from novel_studio.intelligence.diff import MasterDiffService
from novel_studio.jobs.worker import Job, StreamJob
from novel_studio.ai.provider_manager import ProviderManager
from novel_studio.ai.engine import AIEngine
from novel_studio.ai.context import ContextManager
from novel_studio.ai.prompts import (chat_system, entity_extra, master as master_prompt,
                                     contract as contract_prompt,
                                     master_plot as master_plot_prompt, idea as idea_prompt, repair_chapter_plans,
                                     SECTIONS)
from novel_studio.services.idea_service import IdeaService
from novel_studio.planning.master_planner import MasterPlanner
from novel_studio.plot.plot_manager import PlotManager
from novel_studio.plot.parser import parse_chapter_plans, validate_chapter_plans
from novel_studio.manuscript.chapter_writer import ChapterWriter
from novel_studio.memory.memory_manager import MemoryManager
from novel_studio.continuity.checker import ContinuityChecker
from novel_studio.intelligence.ledger import StateLedger
from novel_studio.intelligence.diff import MasterDiffService
from novel_studio.jobs.worker import Job, StreamJob


class NovelController(QObject):
    """
    메인 컨트롤러 - View와 Service 사이의 조정자
    - View에서 오는 UI 이벤트를 Service 호출로 변환
    - 백그라운드 작업 관리 (Job/StreamJob)
    - 상태 변화 Signal 발행
    """
    
    # UI 업데이트용 Signal
    status_changed = Signal(str)
    progress_updated = Signal(int, int, str)  # current, total, message
    chapter_changed = Signal(int)
    ai_status_changed = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        # Services will be set via set_services
        self.project_service = None
        self.ai_service = None
        self.db_service = None
        self.context_service = None
        self.settings_service = None
        self.continuity_service = None
        self.writing_service = None
        self.memory_service = None
        self.export_service = None
        
        # Qt 스레드 풀
        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(1)
        
        self._busy = False
        self._current_job = None
        self._current_chapter = 1
        self._adjust_attempts = 0
        
        # MainWindow 참조
        self.main_window = None
        
    def set_main_window(self, main_window):
        """MainWindow 참조 설정"""
        self.main_window = main_window
        # Services will be set via set_services
        
    def set_services(self, services: dict):
        """서비스 의존성 주입"""
        self.project_service = services.get('project')
        self.ai_service = services.get('ai')
        self.db_service = services.get('db')
        self.context_service = services.get('context')
        self.settings_service = services.get('settings')
        self.continuity_service = services.get('continuity')
        self.writing_service = services.get('writing')
        self.memory_service = services.get('memory')
        self.export_service = services.get('export')
        self.export_service = services.get('export')
        
    @property
    def busy(self) -> bool:
        return self._busy
    
    @property
    def current_chapter(self) -> int:
        return self._current_chapter
    
    @property
    def main_window_ref(self):
        return self._main_window_ref
    
    def set_main_window_ref(self, main_window):
        self._main_window_ref = main_window
        
    @property
    def busy(self) -> bool:
        return self._busy
    
    @property
    def current_chapter(self) -> int:
        return self._current_chapter
    
    @current_chapter.setter
    def current_chapter(self, value: int):
        self._current_chapter = value
        self.chapter_changed.emit(value)
    
    # ========== 작업 실행 인프라 ==========
    
    def _run_job(self, label: str, fn: callable, done_callback: callable,
                 error_callback=None, cancelled_callback=None):
        """일반 작업 실행 (Job)"""
        if self._busy:
            self.error_occurred.emit('이미 작업이 실행 중입니다.')
            return
        
        self._busy = True
        self.status_changed.emit(label)
        
        job = Job(fn)
        job.signals.finished.connect(lambda v: self._on_job_done(done_callback, v))
        job.signals.error.connect(lambda e: self._on_job_error(error_callback, e))
        job.signals.cancelled.connect(lambda: self._on_job_cancelled(None))
        QThreadPool.globalInstance().start(job)
    
    def _run_stream(self, label: str, fn, done_callback: callable,
                    append_widget=None, replace=True):
        """스트리밍 작업 실행 (StreamJob)"""
        if self._busy:
            self.error_occurred.emit('이미 작업이 실행 중입니다.')
            return
        
        self._busy = True
        self.status_changed.emit(label)
        
        from novel_studio.jobs.worker import StreamJob
        job = StreamJob(fn)
        job.signals.progress.connect(lambda t, w=None: self._on_stream_token(w, t))
        job.signals.finished.connect(lambda v: self._on_stream_done(None, v))
        job.signals.error.connect(lambda e: self._on_stream_error(e))
        job.signals.cancelled.connect(self._on_stream_cancelled)
        
        if append_widget:
            append_widget.blockSignals(True)
        
        QThreadPool.globalInstance().start(job)
    
    def _on_job_done(self, callback, result):
        self._busy = False
        if callback:
            callback(result)
    
    def _on_job_error(self, callback, error):
        self._busy = False
        self.error_occurred.emit(str(error))
        if callback:
            callback(error)
    
    def _on_job_cancelled(self, callback):
        self._busy = False
        if callback:
            callback()
    
    def _on_stream_token(self, widget, token):
        if widget:
            widget.insertPlainText(token)
    
    def _on_stream_done(self, callback, result):
        self._busy = False
        if callback:
            callback(result)
    
    def _on_stream_error(self, error):
        self._busy = False
        self.error_occurred.emit(str(error))
    
    def _on_stream_cancelled(self):
        self._busy = False
        self.status_changed.emit('작업이 취소되었습니다.')
    
    def stop_current_job(self):
        """현재 작업 취소"""
        if self._current_job:
            self._current_job.cancel()
    
    # ========== 프로젝트 관리 ==========
    
    def new_project(self, path: str) -> bool:
        """새 프로젝트 생성"""
        try:
            # ProjectManager를 통해 새 프로젝트 생성
            return True
        except Exception as e:
            self.error_occurred.emit(f'프로젝트 생성 실패: {e}')
            return False
    
    def open_project(self, path: str) -> bool:
        """기존 프로젝트 열기"""
        try:
            # 프로젝트 열기 로직
            return True
        except Exception as e:
            self.error_occurred.emit(f'프로젝트 열기 실패: {e}')
            return False
    
    def save_project_settings(self, settings: dict) -> bool:
        try:
            self.project_service.save_settings(settings)
            return True
        except Exception as e:
            self.error_occurred.emit(f'설정 저장 실패: {e}')
            return False
    
    # ========== 집필 관련 ==========
    
    def write_chapter(self, chapter: int, stream_callback=None, done_callback=None):
        """챕터 집필 (스트리밍)"""
        def stream_fn():
            # Use the writing service to write the chapter with streaming
            return self.writing_service.write_chapter(chapter, stream_callback)
        
        self._run_stream(f'{chapter}화 AI 집필 중...', stream_fn, done_callback)
    
    def revise_current(self, text: str) -> str:
        return self.writing_service.revise_chapter(text)
    
    def check_consistency(self, chapter: int, text: str):
        def job():
            return self.continuity_service.check_chapter(chapter, text)
        def done(result):
            self.status_changed.emit('연속성 검사 완료')
        self._run_job('연속성 검사 중...', job, lambda r: None)
    
    def revise_text(self, text: str, stream_callback=None, done_callback=None):
        """텍스트 윤문 (스트리밍)"""
        def stream_fn():
            return self.ai_service.generate_stream(
                '사건과 설정을 변경하지 말고 다음 원고를 자연스럽게 윤문하라. 본문만 출력.\n' + text,
                temperature=0.38, max_tokens=14000)
        
        self._run_stream('AI 윤문 중...', stream_fn, done_callback)
    
    # ========== 연속성 검사 ==========
    
    def check_current_chapter(self, chapter: int, text: str, done_callback=None):
        """현재 챕터 연속성 검사"""
        def job():
            return self.continuity_service.check_chapter(chapter, text)
        
        self._run_job('AI 연속성 검사 중...', job, done_callback)
    
    def audit_long_form(self, size: int = 50):
        """장편 연속성 검사 - 진행률 콜백 지원"""
        findings = []
        
        def progress_callback(current, total, range_str, result_text):
            pct = int(current / max(1, total) * 100)
            self.progress_updated.emit(current, total, f'{pct}% ({current}/{total})')
        
        def job():
            # 실제 구현은 ContinuityService에 위임
            pass
        
        def done(result):
            self.status_changed.emit('장편 정밀 검사 완료')
        
        self._run_job('장편 정밀 연속성 검사 중...', job, done)
    
    # ========== 메모리/연속성 ==========
    
    def refresh_memory(self, chapter: int, text: str, previous_state: str):
        def job():
            return self.memory_service.update_memory(chapter, text, previous_state)
        def done(result):
            pass
        self._run_job('기억 업데이트 중...', job, done)
    
    def save_memory_notes(self, notes: str) -> bool:
        return self.memory_service.save_memory_notes(notes)
    
    # ========== 설정 관리 ==========
    
    def get_ai_settings(self) -> dict:
        return self.settings_service.get_ai_settings()
    
    def save_provider_config(self, provider_id: str, config: dict):
        pass
    
    # ========== 내보내기 ==========
    
    def export_manuscript(self) -> str:
        return self.export_service.export_manuscript()
    
    # ========== 유틸리티 ==========
    
    def check_current_chapter(self, chapter: int, text: str):
        """현재 챕터 연속성 검사"""
        return self.check_current_chapter(chapter, text)
    
    def update_ai_status(self):
        """AI 상태 표시 업데이트"""
        try:
            pid = self.settings_service.get_active_provider()
            name = self.settings_service.get_provider_config(pid).get('name', pid)
            model = self.settings_service.get_provider_config(pid).get('model', '')
            self.ai_status_changed.emit(f"AI ● {name} / {model or '모델 미설정'}")
        except Exception as e:
            self.ai_status_changed.emit('AI ● 확인 필요')
    
    def stop_current_job(self):
        """현재 실행 중인 작업 취소"""
        pass