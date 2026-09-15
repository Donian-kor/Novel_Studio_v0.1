from pathlib import Path
import logging
import os
import sys
import subprocess
from PySide6.QtWidgets import (QMainWindow, QMessageBox, QFileDialog, QListWidget,
                                 QStackedWidget, QLabel, QPushButton, QFrame,
                                 QPlainTextEdit, QTextBrowser, QDialog, QComboBox)
from PySide6.QtCore import QTimer, Qt, QByteArray
from PySide6.QtGui import QFont, QTextCursor, QAction, QKeySequence, QIcon, QPixmap, QPainter, QColor
from novel_studio.ui.loader import load_ui
from novel_studio.ui.views.planning import PlanningView
from novel_studio.ui.views.entities import EntitiesView
from novel_studio.ui.views.story import StoryView
from novel_studio.ui.views.manuscript import ManuscriptView
from novel_studio.ui.views.end_state import EndStateView
from novel_studio.ui.views.chat import ChatWindow
from novel_studio.core.project import ProjectManager
from novel_studio.core.app_settings import AppSettings
from novel_studio.ai.provider_manager import ProviderManager
from novel_studio.ai.engine import AIEngine
from novel_studio.ai.context import ContextManager
from novel_studio.ai.prompts import (chat_system, entity_extra, master as master_prompt,
                                     contract as contract_prompt,
                                     master_plot as master_plot_prompt, idea as idea_prompt,
                                     SECTIONS)
from novel_studio.plot.plot_manager import PlotManager
from novel_studio.manuscript.chapter_writer import ChapterWriter
from novel_studio.continuity.checker import ContinuityChecker
from novel_studio.intelligence.diff import MasterDiffService
from novel_studio.ui.dialogs import AISettingsDialog, ProjectSettingsDialog
from novel_studio.utils.text import count_chars, strip_ai_marks, check_spelling
from novel_studio.controllers.novel_controller import NovelController
from novel_studio.utils.story_parser import parse_chapter_stories

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    NAV=['기획','설정 DB','스토리','원고','화 종료 상태']
    def __init__(self, project_root):
        super().__init__()
        self.setWindowTitle('Novel Studio v1.5.3')
        self.resize(1700, 1000)
        self.project_root = Path(project_root)
        self.current = 1
        self._busy = False
        self._adjust_attempts = 0
        self._active_manuscript_job = None
        self._init_services()
        self._init_ui()
        self._restore_ui_state()
        self.chat_window = ChatWindow(self)
        # 메인 창이 닫히면 독립 채팅창도 함께 닫아 앱이 정상 종료되게 한다
        try:
            self.destroyed.connect(self.chat_window.close)
        except Exception:
            pass
        self._save_last_project()
        self._load_all()
        self._build_project_menu()
    def _init_services(self) -> None:
        """프로젝트 구성요소를 ServiceFactory에서 한 번만 생성한다."""
        from novel_studio.factories import ServiceFactory

        bundle = ServiceFactory.create_all(self.project_root)
        self.pm = bundle["pm"]
        self.app = bundle["app"]
        self.db = bundle["db"]
        self.providers = bundle["providers"]
        self.ai = bundle["ai_engine"]
        self.context = bundle["context_mgr"]
        self.plot = bundle["plot_mgr"]
        self.master_diff = bundle["master_diff"]
        self.end_state = bundle["end_state"]
        self.writer = bundle["writer"]
        self.checker = bundle["checker"]

        # 기존 View와 호환되는 보조 객체는 동일 인스턴스를 사용한다.
        self.idea_service = bundle["idea_service"]

        self.controller = bundle["controller"]
        self.controller.set_main_window(self)
        self._connect_controller_signals()
        
    def _connect_controller_signals(self) -> None:
        """Controller 신호를 UI 갱신 함수에 연결한다."""
        self.controller.status_changed.connect(self._on_controller_status)
        self.controller.progress_updated.connect(self._on_progress_update)
        self.controller.chapter_changed.connect(self._on_chapter_changed)
        self.controller.ai_status_changed.connect(self._update_ai_status)
        self.controller.error_occurred.connect(self._error)
    
    def _error(self, error: object) -> None:
        """Controller에서 전달된 작업 오류를 UI에 표시한다.

        Controller의 error_occurred 시그널은 예외 객체 또는 문자열을
        전달할 수 있으므로 둘 다 안전하게 처리한다.
        """
        try:
            message = str(error) if error is not None else '알 수 없는 오류가 발생했습니다.'
        except Exception:
            message = '알 수 없는 오류가 발생했습니다.'
        logger.error('Controller error: %s', message)
        self.statusBar().showMessage(message)
        QMessageBox.critical(self, '작업 오류', message)

    def _on_controller_status(self, message: str) -> None:
        self.statusBar().showMessage(message)
        if hasattr(self, 'stopBtn') and self.stopBtn is not None:
            self.stopBtn.setEnabled(self.controller.busy or self._busy)

    def _on_progress_update(self, current: int, total: int, message: str) -> None:
        """Controller의 진행 상황을 상태 표시줄에 반영한다."""
        pct = int(current / max(1, total) * 100)
        self.statusBar().showMessage(f'{message} ({current}/{total}) {pct}%')
        # 필요한 경우 여기에서 세부 진행률 UI를 갱신한다.
        
    def _on_chapter_changed(self, chapter: int) -> None:
        """Controller가 알려준 현재 화 변경을 화면에 반영한다."""
        self.current = chapter
        self.load_chapter(chapter)
    def _init_ui(self) -> None:
        """주요 UI 구성요소를 생성하고 이벤트를 연결한다."""
        self._create_ui_base()
        self._create_views()
        self._connect_common_ui()
        self._connect_planning_ui()
        self._connect_story_ui()
        self._connect_manuscript_ui()
        self._connect_end_state_ui()
        self._setup_auto_save_controls()
        self._build_top_dashboard()

    def _create_ui_base(self) -> None:
        """기본 UI 위젯을 찾고 중앙 위젯에 연결한다."""
        self.ui = load_ui('main_window.ui')
        self.setCentralWidget(self.ui)
        self.nav = self.ui.findChild(QListWidget, 'navList')
        self.stack = self.ui.findChild(QStackedWidget, 'pageStack')
        self.left = self.ui.findChild(QFrame, 'leftPanel')
        self.right = self.ui.findChild(QFrame, 'rightPanel')
        self.left_handle = self.ui.findChild(QFrame, 'leftHandle')
        self.right_handle = self.ui.findChild(QFrame, 'rightHandle')
        self.leftCollapse = self.ui.findChild(QPushButton, 'leftCollapse')
        self.leftExpand = self.ui.findChild(QPushButton, 'leftExpand')
        self.rightCollapse = self.ui.findChild(QPushButton, 'rightCollapse')
        self.rightExpand = self.ui.findChild(QPushButton, 'rightExpand')
        self.aiStatus = self.ui.findChild(QLabel, 'aiStatus')
        self.stopBtn = self.ui.findChild(QPushButton, 'stopBtn')

    def _create_views(self) -> None:
        """화면별 View를 생성하고 Stack에 등록한다."""
        self.views = [
            PlanningView(self),
            EntitiesView(self),
            StoryView(self),
            ManuscriptView(self),
            EndStateView(self),
        ]
        (
            self.planning_view,
            self.entities_view,
            self.story_view,
            self.manuscript_view,
            self.end_state_view,
        ) = self.views
        for view in self.views:
            self.stack.addWidget(view)

    def _connect_common_ui(self) -> None:
        """공통 탐색, 패널, 설정, 채팅, 정지 기능을 연결한다."""
        self.nav.addItems(self.NAV)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        if self.stopBtn is not None:
            self.stopBtn.clicked.connect(self._stop)
            self.stopBtn.setEnabled(False)
        self.ui.findChild(QPushButton, 'leftCollapse').clicked.connect(lambda: self._set_left(False))
        self.ui.findChild(QPushButton, 'leftExpand').clicked.connect(lambda: self._set_left(True))
        self.ui.findChild(QPushButton, 'rightCollapse').clicked.connect(lambda: self._set_right(False))
        self.ui.findChild(QPushButton, 'rightExpand').clicked.connect(lambda: self._set_right(True))
        self.ui.findChild(QPushButton, 'settingsBtn').clicked.connect(self.open_settings)
        self._init_conn_test_btn()
        self.ui.findChild(QPushButton, 'chatBtn').clicked.connect(self.open_ai_chat)
        self.saveAllBtn = self.ui.findChild(QPushButton, 'saveAllBtn')
        if self.saveAllBtn is not None:
            self._save_all_btn_text = self.saveAllBtn.text()
            self.saveAllBtn.clicked.connect(lambda _checked=False: self.save_all())
        clean_all = self.ui.findChild(QPushButton, 'cleanAllBtn')
        if clean_all is not None:
            clean_all.clicked.connect(self.clean_marks_all)

    def _setup_auto_save_controls(self) -> None:
        """자동 저장 선택값을 설정하고 변경 신호를 연결한다."""
        combo = self.ui.findChild(QComboBox, 'autoSaveCombo')
        if combo is None:
            return
        self.autoSaveCombo = combo
        for label, minutes in (('자동 저장: 안 함', 0), ('자동 저장: 5분', 5), ('자동 저장: 10분', 10)):
            combo.addItem(label, minutes)
        try:
            saved_minutes = int(self.app.data.get('editor', {}).get('auto_save_interval', 0) or 0)
        except Exception:
            saved_minutes = 0
        index = combo.findData(saved_minutes)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.currentIndexChanged.connect(self._on_auto_save_changed)
        self._setup_auto_save(saved_minutes)

    def _connect_planning_ui(self) -> None:
        """기획 View의 버튼 신호를 연결한다."""
        view = self.planning_view
        view.masterBtn.clicked.connect(self.generate_master)
        view.diffMasterBtn.clicked.connect(self.preview_master_diff)
        view.contractBtn.clicked.connect(self.generate_contract)
        view.lockBtn.clicked.connect(self.lock_contract)
        view.masterPlotBtn.clicked.connect(self.generate_master_plot)
        view.saveMasterBtn.clicked.connect(self.save_master)
        view.saveContractBtn.clicked.connect(self.save_contract)
        view.savePlotBtn.clicked.connect(self.save_master_plot)
        view.generateBtn.clicked.connect(self.generate_idea)
        view.useBtn.clicked.connect(self.use_idea)

    def _connect_story_ui(self) -> None:
        """스토리 View의 생성 및 재생성 버튼을 연결한다."""
        view = self.story_view
        view.generateBtn.clicked.connect(self.generate_sections)
        view.regenerateSelectedBtn.clicked.connect(self.regenerate_selected_section)
        view.regenerateAllBtn.clicked.connect(self.regenerate_all_sections)
        view.generateChapterBtn.clicked.connect(self.generate_chapter_stories)
        view.regenerateChapterBtn.clicked.connect(self.regenerate_selected_chapter_story)

    def _connect_manuscript_ui(self) -> None:
        """원고 View의 화 선택, 편집, 버튼 이벤트를 연결한다."""
        view = self.manuscript_view
        view.chapterList.currentRowChanged.connect(self._on_chapter_row_changed)
        view.editor.textChanged.connect(self.update_count)
        self._wire_manuscript_buttons(view)

    def _connect_end_state_ui(self) -> None:
        """화 종료 상태 View의 생성 및 검증 버튼을 연결한다."""
        view = self.end_state_view
        view.generateBtn.clicked.connect(self.generate_end_state_selected)
        view.auditBtn.clicked.connect(self.audit_long_form)

    def _restore_ui_state(self) -> None:
        """저장된 창 크기, 창 상태, 패널 상태, 선택 메뉴를 복원한다."""
        try:
            geometry = self.app.get_ui_state('geometry', '')
            window_state = self.app.get_ui_state('window_state', '')
            if geometry:
                self.restoreGeometry(QByteArray.fromBase64(geometry.encode('ascii')))
            if window_state:
                self.restoreState(QByteArray.fromBase64(window_state.encode('ascii')))
            self._set_left(bool(self.app.get_ui_state('left_panel_visible', True)))
            self._set_right(bool(self.app.get_ui_state('right_panel_visible', True)))
            selected = int(self.app.get_ui_state('selected_nav', 0) or 0)
            if self.nav.count() and 0 <= selected < self.nav.count():
                self.nav.setCurrentRow(selected)
        except Exception:
            logger.exception('UI 상태 복원 실패')

    def _save_ui_state(self) -> None:
        """현재 UI 상태를 AppSettings에 저장한다."""
        try:
            self.app.set_ui_state(
                geometry=bytes(self.saveGeometry().toBase64()).decode('ascii'),
                window_state=bytes(self.saveState().toBase64()).decode('ascii'),
                left_panel_visible=self.left.isVisible(),
                right_panel_visible=self.right.isVisible(),
                selected_nav=self.nav.currentRow(),
            )
            self.app.save()
        except Exception:
            logger.exception('UI 상태 저장 실패')

    def _save_view_detail(self, view, label):
        try:
            ok = view.save_detail()
        except Exception as e:
            logger.exception('%s 저장 실패', label)
            QMessageBox.critical(self, f'{label} 저장 실패', str(e))
            return
        if ok:
            view.refresh()
            QMessageBox.information(self, '저장 완료', f'{label}이(가) 저장되었습니다.')
        else:
            QMessageBox.information(self, '저장할 항목 없음', f'저장할 {label} 항목을 먼저 선택하세요.')

    def _build_top_dashboard(self):
        """요청 1: 대시보드를 상단 고정 바로 교체. 사이드바에서 제거하고 항상 보이게."""
        from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
        root = self.ui.layout()          # main_window.ui의 최상위 레이아웃은 top / body / bottom 구조다.
        bar = QFrame(self.ui)
        bar.setObjectName('dashBar')
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(8, 4, 8, 4)
        self.dashTitle = QLabel('작품', bar); self.dashTitle.setObjectName('dashTitle')
        self.dashProgress = QLabel('0/0화', bar); self.dashProgress.setObjectName('dashProgress')
        self.dashChars = QLabel('총 0자', bar); self.dashChars.setObjectName('dashChars')
        self.dashForeshadow = QLabel('활성 복선 0', bar); self.dashForeshadow.setObjectName('dashForeshadow')
        for w in (self.dashTitle, self.dashProgress, self.dashChars, self.dashForeshadow):
            hl.addWidget(w)
        hl.addStretch(1)
        # top(첫째)과 body(둘째) 사이에 항상 보이는 상단 대시보드를 삽입한다.
        root.insertWidget(1, bar)

    def refresh_dashboard(self):
        try:
            p = self.pm.settings
            stats = self.db.chapter_stats()
            done = int(stats.get('done') or 0)
            total = int(p.get('target_chapters', 500) or 500)
            chars = int(stats.get('total_chars') or 0)
            active = self.db.active_foreshadow_count()
            self.dashTitle.setText(f"작품: {p.get('title','')}")
            self.dashProgress.setText(f'{self.current}/{total}화 | 완료 {done}화 ({done/max(1,total)*100:.1f}%)')
            self.dashChars.setText(f'총 {chars:,}자 / 화당 {int(p.get("chapter_chars",5000)):,}자')
            self.dashForeshadow.setText(f'활성 복선 {active}')
        except Exception as e:
            logger.warning('대시보드 갱신 실패: %s', e)

    # ---------- 요청 1: 메인 화면 프로젝트 관리 ----------
    def _build_project_menu(self):
        """상단 메뉴바에 [프로젝트] 메뉴 추가 (새로 만들기/열기/설정)."""
        try:
            mb = self.menuBar()
            if mb is None:
                return
            mnu = mb.addMenu('프로젝트')
            a1 = QAction('새 프로젝트', self); a1.triggered.connect(self.new_project); mnu.addAction(a1)
            a2 = QAction('프로젝트 열기', self); a2.triggered.connect(self.open_project); mnu.addAction(a2)
            mnu.addSeparator()
            a3 = QAction('프로젝트 설정', self); a3.triggered.connect(self.edit_project_settings); mnu.addAction(a3)
            mnu.addSeparator()
            a4 = QAction('전체 원고 내보내기', self); a4.triggered.connect(self.export_manuscript); mnu.addAction(a4)
            # ---------- 도움말 메뉴 ----------
            hlp = mb.addMenu('도움말')
            h1 = QAction('사용법', self); h1.setShortcut(QKeySequence('F1')); h1.triggered.connect(self.open_help); hlp.addAction(h1)
            h2 = QAction('단축키', self); h2.triggered.connect(lambda: self.open_help('sec-shortcuts')); hlp.addAction(h2)
            hlp.addSeparator()
            h3 = QAction('Novel Studio 정보', self); h3.triggered.connect(self.show_about); hlp.addAction(h3)
        except Exception as e:
            logger.warning('프로젝트 메뉴 생성 실패: %s', e)

    # ---------- 도움말 (내장 사용법) ----------
    def open_help(self, anchor=None):
        """내장 도움말 대화상자를 연다. anchor가 있으면 해당 섹션으로 이동."""
        try:
            from novel_studio.ui.help import HelpDialog
            dlg = HelpDialog(self, anchor=anchor)
            dlg.exec()
        except Exception as e:
            logger.error('도움말 열기 실패: %s', e)
            QMessageBox.critical(self, '도움말 오류', f'도움말을 여는 중 오류가 발생했습니다.\n{e}')

    def show_about(self):
        QMessageBox.about(
            self, 'Novel Studio 정보',
            '<b>Novel Studio</b> v1.5.2<br><br>'
            '아이디어부터 장편 연재 원고까지 AI와 함께 완성하는 작품 집필 도구입니다.<br><br>'
            '사용법은 메뉴바 [도움말] → [사용법] (F1)에서 확인할 수 있습니다.')

    def _save_last_project(self, root=None):
        """요청: 다음 실행 때 자동으로 열기 위해 마지막 프로젝트 경로를 저장한다."""
        try:
            self.app.data['last_project'] = str(root or self.project_root)
            self.app.save()
        except Exception as e:
            logger.warning('마지막 프로젝트 저장 실패: %s', e)

    def _restart_with(self, root):
        """프로젝트 전환: 새 프로세스로 재시작해 해당 프로젝트를 연다."""
        # 전환 전 현재 내용을 저장해 데이터 유실을 막는다
        try:
            self.save_all(silent=True)
        except Exception:
            pass
        try:
            script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'main.py'))
            subprocess.Popen([sys.executable, script, str(root)])
        except Exception as e:
            logger.error('프로젝트 전환 실패: %s', e)
        os._exit(0)

    def new_project(self):
        from novel_studio.ui.startup import StartupDialog
        dlg = StartupDialog()
        if dlg.exec() == dlg.DialogCode.Accepted and dlg.selected_project:
            self._save_last_project(dlg.selected_project)
            if self.controller.new_project(str(dlg.selected_project)):
                self._restart_with(dlg.selected_project)
            else:
                QMessageBox.warning(self, '오류', '새 프로젝트를 만드는 데 실패했습니다.')

    def open_project(self):
        from novel_studio.ui.startup import StartupDialog
        dlg = StartupDialog()
        if dlg.exec() == dlg.DialogCode.Accepted and dlg.selected_project:
            self._save_last_project(dlg.selected_project)
            if self.controller.open_project(str(dlg.selected_project)):
                self._restart_with(dlg.selected_project)
            else:
                QMessageBox.warning(self, '오류', '프로젝트를 여는 데 실패했습니다.')

    def edit_project_settings(self):
        d = ProjectSettingsDialog(self.pm, self)
        if d.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            total = int(self.pm.settings['target_chapters'])
            target = int(self.pm.settings['chapter_chars'])
            self.db.ensure_chapters(total, target)
        except Exception:
            pass
        self._save_last_project()
        self._update_state()
        self._load_chapters()
        self.refresh_dashboard()
        self.planning_view.refresh()
        QMessageBox.information(self, '저장 완료', '프로젝트 설정이 저장되었습니다.')

    # ---------- 요청 4: 실시간 스트리밍 ----------
    def _append_token(self, widget, token):
        """스트리밍 토큰을 텍스트 편집 위젯에 안전하게 추가한다.

        QPlainTextEdit/QTextEdit 모두 지원하며, 토큰마다 전체 텍스트를 다시
        설정하지 않아 커서 위치와 입력 상태를 불필요하게 초기화하지 않는다.
        """
        if widget is None or not token:
            return
        try:
            from PySide6.QtGui import QTextCursor
            cursor = widget.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(str(token))
            widget.setTextCursor(cursor)
            widget.ensureCursorVisible()
        except Exception:
            # 위젯 구현 차이가 있는 경우 Qt의 기본 삽입 API로 한 번 더 시도한다.
            try:
                if hasattr(widget, 'insertPlainText'):
                    widget.moveCursor(widget.textCursor().MoveOperation.End)
                    widget.insertPlainText(str(token))
                elif hasattr(widget, 'insertHtml'):
                    widget.insertHtml(str(token))
            except Exception:
                logger.exception('스트리밍 토큰 UI 반영 실패')

    def _run_stream(self, label, fn, done, append=None, replace=True, error_callback=None, cancelled_callback=None):
        """AI 스트리밍을 Controller에 연결한다. 진행 결과는 메모리 버퍼에만 유지하고 저장은 명시적 단계에서 수행한다."""
        stream_started = False
        collected = []
        def stream_callback(token):
            nonlocal stream_started
            token = str(token or '')
            if not token: return
            collected.append(token)
            if append is not None:
                if replace and not stream_started:
                    try: append.clear()
                    except Exception: pass
                    stream_started = True
                self._append_token(append, token)
        def on_done(result):
            if done: done(result if result is not None else ''.join(collected))
        def on_error(error):
            if error_callback: error_callback(error)
        def on_cancelled():
            if cancelled_callback: cancelled_callback()
        return self.controller.run_stream(label, fn, stream_callback, on_done, on_error, on_cancelled)

    def _check_write_prereq(self):
        """요청 2: 기획/설정 없이 원고를 쓰지 못하도록 차단."""
        if not self.db.get_plan() and not self.db.get_meta('master_plot', ''):
            QMessageBox.information(
                self, '기획 필요',
                '아직 작품 기획이 없습니다.\n\n'
                '[기획] 탭에서 아래 순서를 먼저 진행하세요.\n'
                '1) AI 아이디어 생성 → 이 아이디어 사용\n'
                '2) AI 마스터 기획 생성\n'
                '3) AI 핵심 기준 추출\n'
                '4) AI 전체 플롯 생성')
            return False
        if not self.db.get_meta('master_plot', ''):
            QMessageBox.information(
                self, '전체 플롯 필요',
                '마스터 기획은 있지만 전체 플롯이 없습니다.\n\n'
                '[기획] 탭에서 [AI 전체 플롯 생성]을 먼저 실행하세요.')
            return False
        return True

    def _wire_manuscript_buttons(self, m):
        """하단바 버튼 제거 대신 원고 뷰 내부 버튼을 찾아 연결 (라벨 변경 포함)."""
        mapping = {}
        for b in m.ui.findChildren(QPushButton):
            t = b.text()
            if '집필' in t: mapping['write'] = b
            elif '윤문' in t or '다듬' in t: mapping['revise'] = b; b.setText('AI 문장 다듬기')
            elif '검증' in t or '충돌' in t: mapping['check'] = b; b.setText('설정 충돌 검사')
        if 'write' in mapping: mapping['write'].clicked.connect(self.write_current)
        if 'revise' in mapping: mapping['revise'].clicked.connect(self.revise_current)
        if 'check' in mapping: mapping['check'].clicked.connect(self.check_current)
        # 저장 버튼 (원고 뷰 내부)
        # 주의: QPushButton.clicked(bool)는 첫 슬롯 인자에 False를 주입한다.
        # save_current(update_end_state=True)에 그대로 연결하면 update_end_state=False가 되어
        # 저장 옵션이 잘못 전달되지 않도록 반드시 람다로 감싼다.
        for b in m.ui.findChildren(QPushButton):
            if b.text().strip() == '저장':
                self._save_btn_text = b.text()
                b.clicked.connect(lambda _checked=False: self.save_current())
                self._save_btn = b
        # 요청 7: manuscript.ui에 이미 존재하는 맞춤법/기호삭제 버튼 배선
        sp = m.ui.findChild(QPushButton, 'spellBtn')
        if sp is not None:
            sp.clicked.connect(self.spellcheck_current)
        cl = m.ui.findChild(QPushButton, 'cleanBtn')
        if cl is not None:
            cl.clicked.connect(self.clean_marks_current)
        cb = m.ui.findChild(QPushButton, 'chatBtn')
        if cb is not None:
            cb.clicked.connect(self.open_ai_chat)

    def _set_left(self, on: bool) -> None: self.left.setVisible(on); self.left_handle.setVisible(not on)
    def _set_right(self, on: bool) -> None: self.right.setVisible(on); self.right_handle.setVisible(not on)
    def _run(self, label, fn, done, error_callback=None, cancelled_callback=None):
        """레거시 호출 호환용 Controller 작업 위임 래퍼.

        Controller가 busy면 ``run_task``가 False를 반환하는데, 기존 호출부는
        이 값을 무시해 "설정 충돌 검사 버튼이 먹통"처럼 보였다. busy 거부는
        상태바로 알려주고 False를 그대로 돌려준다.
        """
        ok = self.controller.run_task(
            label, fn, done,
            error_callback=error_callback,
            cancelled_callback=cancelled_callback,
        )
        if not ok:
            self.statusBar().showMessage('AI 작업 실행 중입니다. 잠시 후 다시 눌러주세요.')
        return ok
    def _finish_job(self):
        """레거시 호환 메서드. 실제 작업 상태는 Controller가 관리한다."""
        self._busy = False
        self._adjust_attempts = 0

    def _stop(self):
        """⏹ 정지 버튼: 현재 작업에 취소를 요청하고 진행 중인 AI I/O를 중단한다."""
        if self.controller.stop_current_job():
            logger.info('사용자가 작업 중지를 요청했습니다.')
            self.statusBar().showMessage('작업 취소 요청됨...')
        else:
            self.statusBar().showMessage('실행 중인 작업이 없습니다.')

    def _load_all(self) -> None: self.planning_view.refresh(); self.entities_view.refresh(); self.story_view.refresh(); self._load_chapters(); self.manuscript_view.refresh(); self.load_chapter(1); self._update_ai_status(); self.refresh_dashboard()
    def _load_chapters(self) -> None:
        v=self.manuscript_view
        v.chapterList.blockSignals(True)
        try:
            v.chapterList.clear()
            rows=self.db.chapters()
            v.chapterList.insertItems(0,[f"{r['number']:03d}화 | {r['status']} | {r['char_count']:,}자" for r in rows])
        finally:
            v.chapterList.blockSignals(False)
        self.refresh_dashboard()
    def export_manuscript(self):
        """작성된 전체 원고를 Controller의 ExportService를 통해 내보낸다."""
        try:
            path = self.controller.export_manuscript()
            self.statusBar().showMessage(f'원고 내보내기 완료: {path}')
            QMessageBox.information(self, '내보내기 완료', f'전체 원고를 내보냈습니다.\n{path}')
        except Exception as e:
            logger.warning('원고 내보내기 실패: %s', e)
            QMessageBox.critical(self, '내보내기 실패', f'원고 내보내기 중 오류가 발생했습니다.\n{e}')
    def generate_idea(self):
        def stream(on_token):
            previous = '\n'.join(r['content'] for r in self.db.recent_ideas(10))
            collected = []
            for t in self.ai.generate_stream(idea_prompt(self.pm.settings, previous),
                                             temperature=.9, max_tokens=800):
                if self.controller.cancel_requested:
                    break
                on_token(t)
                collected.append(t)
            out = ''.join(collected)
            if out.strip():
                self.db.add_idea(out)
            return out
        self._run_stream('AI 아이디어 생성 중...', stream, lambda t: None,
                         append=self.planning_view.ideaEdit)
    def use_idea(self):
        t = self.planning_view.ideaEdit.toPlainText().strip()
        if not t:
            QMessageBox.warning(self, '아이디어 필요', '먼저 아이디어를 입력하거나 [AI 아이디어 생성]을 눌러 생성하세요.')
            return
        self.db.use_idea(t)
        self.db.set_meta('idea', t)
        self.statusBar().showMessage('아이디어 확정 → 아래에서 [AI 마스터 기획 생성]을 눌러 계속하세요.')
        self.planning_view.refresh()
    def generate_master(self):
        t=self.planning_view.ideaEdit.toPlainText().strip() or self.db.get_meta('idea','')
        if not t: QMessageBox.warning(self,'아이디어 필요','아이디어를 먼저 입력하거나 AI로 생성하세요.'); return
        def stream(on_token):
            collected = []
            for piece in self.ai.generate_stream(
                    [{'role': 'system', 'content': '장편 웹소설 마스터 기획자'},
                     {'role': 'user', 'content': master_prompt(t, self.pm.settings)}],
                    temperature=.72, max_tokens=12000):
                if self.controller.cancel_requested:
                    break
                on_token(piece)
                collected.append(piece)
            out = ''.join(collected)
            if out.strip():
                self.db.save_plan(out)
                self.db.set_meta('idea', t)
            return out
        self._run_stream('AI 마스터 기획 생성 중...', stream,
                         lambda _: self._after_master_saved(),
                         append=self.planning_view.masterEdit)
    def sync_master_characters(self):
        """마스터 기획에서 남주/여주/조연 인물을 자동 추출해 설정 DB에 upsert한다."""
        from novel_studio.ai.prompts import entity_catalog_prompt
        from novel_studio.utils.entity_parser import parse_entity_catalog
        master=self.db.get_plan().strip()
        if not master:return 0
        text=self.ai.generate(entity_catalog_prompt('인물',master,int(self.pm.settings['target_chapters'])),temperature=.28,max_tokens=8000)
        items=parse_entity_catalog(text); count=0
        for x in items:
            name=(x.get('name') or '').strip()
            if not name:continue
            self.db.save_character({'name':name,'role':x.get('role') or '조연','profile':x.get('profile',''),'personality':x.get('personality',''),'speech_style':x.get('speech_style',''),'goal':x.get('goal',''),'secret':x.get('secret',''),'arc':x.get('arc','')})
            count+=1
        return count

    def _after_master_saved(self, _=None):
        try:
            n=self.sync_master_characters()
            self.entities_view.refresh()
            self.statusBar().showMessage(f'마스터 기획 저장 완료 · 인물 DB {n}개 자동 동기화')
        except Exception as e:
            logger.warning('마스터→인물 자동 동기화 실패: %s',e)
            self.entities_view.refresh()
            self.statusBar().showMessage('마스터 기획 저장 완료 · 인물 자동 동기화 실패')

    def preview_master_diff(self):
        old=self.db.get_plan() or ''
        new=self.planning_view.masterEdit.toPlainText()
        if not old:
            QMessageBox.information(self,'변경점 검사','기존 마스터 기획이 없습니다. 먼저 저장된 마스터 기획을 만들어 주세요.')
            return
        if old == new:
            QMessageBox.information(self,'변경점 검사','변경된 내용이 없습니다.')
            return
        try:
            payload=self.master_diff.propose(old,new)
            text=payload.get('summary','변경점 검사 완료')
            changes=payload.get('changes') or []
            if changes: text += '\n\n' + '\n'.join(f"- {c.get('type','modify')}: {c.get('path','')}\n  기존: {c.get('before','')}\n  변경: {c.get('after','')}" for c in changes[:30])
            QMessageBox.information(self,'마스터 변경 제안',text)
        except Exception as e:
            QMessageBox.critical(self,'변경점 검사 실패',str(e))

    def save_master(self):
        self.db.save_plan(self.planning_view.masterEdit.toPlainText())
        self._run('마스터 기획에서 인물 자동 동기화 중...', self.sync_master_characters, self._after_master_saved)
    def save_contract(self):
        current=self.db.get_contract()
        if current and current['locked']:
            QMessageBox.warning(self,'핵심 기준 잠금','잠긴 핵심 기준은 수정할 수 없습니다.'); return
        self.db.save_contract(self.planning_view.contractEdit.toPlainText(),False); self.statusBar().showMessage('핵심 기준 저장 완료')
    def save_master_plot(self): self.db.set_meta('master_plot',self.planning_view.masterPlotEdit.toPlainText()); self.statusBar().showMessage('전체 플롯 저장 완료')
    def generate_contract(self):
        if not self.db.get_plan(): return
        txt = '\n\n'.join(f'[{s}]\n{self.db.section_content(s)}' for s in SECTIONS)
        def stream(on_token):
            collected = []
            for piece in self.ai.generate_stream(
                    contract_prompt(self.db.get_plan(), txt, int(self.pm.settings['target_chapters'])),
                    temperature=.22, max_tokens=6000):
                if self.controller.cancel_requested:
                    break
                on_token(piece)
                collected.append(piece)
            out = ''.join(collected)
            if out.strip():
                self.db.save_contract(out, False)
            return out
        self._run_stream('장편 핵심 기준 추출 중...', stream, lambda _: None,
                         append=self.planning_view.contractEdit)
    def lock_contract(self):
        text=self.planning_view.contractEdit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self,'핵심 기준 필요','잠글 내용이 없습니다.')
            return
        self.db.save_contract(text,True)
        self.planning_view.contractEdit.setReadOnly(True)
        self.planning_view.lockBtn.setEnabled(False)
        self.statusBar().showMessage('핵심 기준 잠금 완료')
    def generate_master_plot(self):
        if not self.db.get_contract(): QMessageBox.warning(self,'핵심 기준 필요','먼저 핵심 기준을 추출하세요.'); return
        c = self.db.get_contract()
        def stream(on_token):
            collected = []
            for piece in self.ai.generate_stream(
                    master_plot_prompt(self.db.get_plan(), c['content'] if c else '',
                                       int(self.pm.settings['target_chapters'])),
                    temperature=.62, max_tokens=12000):
                if self.controller.cancel_requested:
                    break
                on_token(piece)
                collected.append(piece)
            out = ''.join(collected)
            if out.strip():
                self.db.set_meta('master_plot', out)
            return out
        self._run_stream('AI 전체 플롯 생성 중...', stream,
                         lambda _: self.planning_view.refresh(),
                         append=self.planning_view.masterPlotEdit)
    def _mark_downstream_sections_stale(self, start: int) -> None:
        """선택 장기 구간 재생성 뒤의 구간을 갱신 필요 상태로 표시한다."""
        for s, e in self.plot.long_ranges():
            if s <= int(start):
                continue
            row = self.db.section(s, e)
            if row and (row['content'] or '').strip():
                self.db.save_section(s, e, '갱신 필요', row['content'])

    def _generate_subsections(self, start: int, end: int, parent_content: str) -> int:
        made = 0
        previous = ''
        for ss, ee in self.plot.sub_ranges(start, end):
            if self.controller.cancel_requested:
                break
            text = self.plot.generate_substory_section(ss, ee, parent_content, previous)
            if not (text or '').strip():
                raise ValueError(f'{ss}~{ee}화 세부 스토리 생성 결과가 비어 있습니다.')
            self.db.save_story_subsection(start, end, ss, ee, f'{ss}~{ee}화 세부 스토리', text, '생성완료')
            previous = text
            made += 1
        return made

    def generate_sections(self, force: bool = False):
        if not self.db.get_meta('master_plot','').strip():
            QMessageBox.warning(self,'전체 플롯 필요','먼저 전체 플롯을 생성하세요.')
            return
        def work():
            previous = ''
            made = 0
            for s, e in self.plot.long_ranges():
                if self.controller.cancel_requested:
                    break
                old = self.db.section(s, e)
                if old and old['status'] == '생성완료' and not force:
                    previous = old['content'] or previous
                    continue
                content = self.plot.generate_story_section(s, e, previous)
                if not (content or '').strip():
                    raise ValueError(f'{s}~{e}화 스토리 생성 결과가 비어 있습니다.')
                self.db.save_section(s, e, '생성완료', content, '')
                made += self._generate_subsections(s, e, content)
                previous = content
            return made
        label = '스토리 전체 다시 생성 중...' if force else '스토리 생성/이어하기 중...'
        return self._run(label, work, lambda n: (self.story_view.refresh(), self.statusBar().showMessage(f'세부 스토리 {n}개 생성 완료')))

    def regenerate_selected_section(self):
        kind, row = self.story_view.selected()
        if not row:
            QMessageBox.information(self,'구간 선택','먼저 재생성할 스토리 구간을 선택하세요.')
            return
        if not self.db.get_meta('master_plot','').strip():
            QMessageBox.warning(self,'전체 플롯 필요','먼저 [기획]에서 전체 플롯을 생성하세요.')
            return
        if QMessageBox.question(self,'선택 구간 재생성','선택한 스토리 구간을 새로 생성하여 기존 내용을 교체합니다. 계속하시겠습니까?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        if kind == 'long':
            s,e = int(row['start_chapter']), int(row['end_chapter'])
            def work():
                content = self.plot.generate_story_section(s, e, '')
                if not content.strip(): raise ValueError('스토리 생성 결과가 비어 있습니다.')
                self.db.save_section(s,e,'생성완료',content)
                return self._generate_subsections(s,e,content)
        else:
            s,e = int(row['start_chapter']), int(row['end_chapter'])
            parent = self.db.section(int(row['parent_start']), int(row['parent_end']))
            parent_content = (parent['content'] if parent else '') or ''
            def work():
                content = self.plot.generate_substory_section(s,e,parent_content)
                if not content.strip(): raise ValueError('세부 스토리 생성 결과가 비어 있습니다.')
                self.db.save_story_subsection(int(row['parent_start']),int(row['parent_end']),s,e,row['title'] or f'{s}~{e}화 세부 스토리',content,'생성완료')
                return 1
        return self._run('선택 스토리 구간 재생성 중...', work, lambda _: self.story_view.refresh())

    def regenerate_all_sections(self):
        if not self.db.get_meta('master_plot','').strip():
            QMessageBox.warning(self,'전체 플롯 필요','먼저 전체 플롯을 생성하세요.')
            return
        if QMessageBox.question(self,'전체 스토리 다시 생성','현재 스토리 구간을 전부 새로 생성합니다. 계속하시겠습니까?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        return self.generate_sections(force=True)

    def _on_chapter_row_changed(self, row):
        if row < 0:
            return
        target = row + 1
        if target == self.current:
            return
        # 화면 전환으로 현재 원고가 교체되기 전에 현재 화의 화면 내용을 먼저 보존한다.
        try:
            self._save_editor_draft(self.current)
        except Exception:
            logger.exception('화 전환 전 원고 임시 저장 실패')
        self.load_chapter(target)

    def _save_editor_draft(self, chapter: int) -> None:
        text = self.manuscript_view.editor.toPlainText()
        title = self.manuscript_view.titleEdit.text().strip() or f'{chapter}화'
        self.pm.save_chapter(chapter, text)
        self.db.set_chapter_meta(
            int(chapter), title, '초안' if text.strip() else '미작성',
            count_chars(text), count_chars(text, True), int(self.pm.settings['chapter_chars'])
        )

    def load_chapter(self,n):
        self.current=int(n); v=self.manuscript_view
        v.editor.blockSignals(True)
        active = self._active_manuscript_job
        if active and int(active.get('chapter', -1)) == self.current:
            v.editor.setPlainText(''.join(active.get('buffer', [])))
        else:
            v.editor.setPlainText(self.pm.load_chapter(self.current))
        v.editor.blockSignals(False)
        r=self.db.chapter(self.current); v.titleEdit.setText(r['title'] if r else f'{self.current}화'); self.update_count(); self._update_state()
        if hasattr(self,'chat_window'): self.chat_window.refresh(self.db.chat_messages(limit=200))
    def update_count(self):
        t=self.manuscript_view.editor.toPlainText(); n=count_chars(t); ns=count_chars(t,True); target=int(self.pm.settings['chapter_chars']); self.manuscript_view.countLabel.setText(f'현재 {n:,}자 / 목표 {target:,}자 / 공백 포함 {ns:,}자')
    def _set_save_buttons_busy(self, busy: bool):
        """종료 상태 작업 동안 저장 버튼을 로딩 상태로 잠근다.

        작업 완료/실패/취소 모든 경로에서 반드시 ``_set_save_buttons_busy(False)``로
        복원해야 한다. 복원하지 않으면 버튼이 영원히 비활성화 상태로 남는다.
        """
        pairs = (
            # (버튼, 원본 문구, 로딩 문구)
            (getattr(self, 'saveAllBtn', None),
             getattr(self, '_save_all_btn_text', '전체 저장'),
             '⏳ 종료 상태 작업 중...'),
            (getattr(self, '_save_btn', None),
             getattr(self, '_save_btn_text', '저장'),
             '⏳ 종료 상태 작업 중...'),
        )
        for btn, default_text, busy_text in pairs:
            if btn is None:
                continue
            btn.setText(busy_text if busy else default_text)
            btn.setEnabled(not busy)

    def _generate_end_state_for_chapter(self, chapter: int, text: str):
        return self.end_state.generate(int(chapter), text)

    def save_current(self, update_end_state=None):
        """원고는 항상 즉시 저장한다. 종료 상태 AI 생성은 별도 옵션으로 실행한다."""
        v = self.manuscript_view
        t = v.editor.toPlainText()
        title = v.titleEdit.text().strip() or f'{self.current}화'
        n = count_chars(t); ns = count_chars(t, True); target = int(self.pm.settings['chapter_chars'])
        self.pm.save_chapter(self.current, t)
        self.db.set_chapter_meta(self.current, title, '작성완료' if t.strip() else '미작성', n, ns, target)
        self._load_chapters()
        self.statusBar().showMessage(f'{self.current}화 저장 완료')
        if update_end_state is None:
            update_end_state = bool(self.app.data.get('editor', {}).get('auto_generate_end_state', False))
        if update_end_state and t.strip():
            chapter = int(self.current); text = t
            def done(result):
                self.end_state_view.refresh(); self._update_state(); self.statusBar().showMessage(f'{chapter}화 저장 완료 · 종료 상태 생성 완료')
            def err(error):
                self.statusBar().showMessage(f'{chapter}화 저장 완료 · 종료 상태 생성 실패: {error}')
            self.controller.generate_end_state(chapter, text, done_callback=done, error_callback=err)

    def save_all(self, silent=False):
        """현재 화면 내용을 저장한다. 자동 저장도 AI를 호출하지 않는다."""
        saved, failed = [], []
        try:
            p=self.planning_view; idea=p.ideaEdit.toPlainText().strip()
            if idea: self.db.set_meta('idea',idea)
            if p.masterEdit.toPlainText().strip(): self.db.save_plan(p.masterEdit.toPlainText())
            c=p.contractEdit.toPlainText()
            if c.strip():
                prev=self.db.get_contract(); self.db.save_contract(c, bool(prev['locked']) if prev else False)
            if p.masterPlotEdit.toPlainText().strip(): self.db.set_meta('master_plot',p.masterPlotEdit.toPlainText())
            saved.append('기획')
        except Exception as e:
            failed.append('기획'); logger.exception('전체 저장(기획) 실패: %s',e)
        try:
            if self.entities_view.save_entry(quiet=True): saved.append('설정 DB')
        except Exception as e:
            failed.append('설정 DB'); logger.exception('전체 저장(설정 DB) 실패: %s',e)
        try:
            if self.story_view.save_detail(): saved.append('스토리')
        except Exception as e:
            failed.append('스토리'); logger.exception('전체 저장(스토리) 실패: %s',e)
        try:
            self.save_current(update_end_state=False); saved.append('원고')
        except Exception as e:
            failed.append('원고'); logger.exception('전체 저장(원고) 실패: %s',e)
        try:
            if self.end_state_view.save_selected(): saved.append('화 종료 상태')
        except Exception as e:
            failed.append('화 종료 상태'); logger.exception('전체 저장(종료 상태) 실패: %s',e)
        if failed:
            msg='자동 저장 실패: ' if silent else '일부 저장에 실패했습니다: '; self.statusBar().showMessage(msg+', '.join(failed))
            if not silent: QMessageBox.warning(self,'전체 저장',msg+' / '.join(failed))
        elif saved:
            self.statusBar().showMessage(('자동 저장 완료: ' if silent else '전체 저장 완료: ')+', '.join(saved))
            if not silent: QMessageBox.information(self,'전체 저장','저장했습니다.\n- '+'\n- '.join(saved))

    # ---------- 자동 저장 ----------
    def _setup_auto_save(self, minutes):
        """자동 저장 타이머를 minutes 간격(분)으로 설정. 0이면 끔."""
        if not hasattr(self, 'auto_timer'):
            self.auto_timer = QTimer(self)
            self.auto_timer.timeout.connect(self._auto_save_tick)
        self.auto_timer.stop()
        if minutes and minutes > 0:
            self.auto_timer.start(int(minutes) * 60 * 1000)

    def _on_auto_save_changed(self, idx):
        try:
            mins = int(self.autoSaveCombo.itemData(idx) or 0)
        except Exception:
            mins = 0
        try:
            self.app.data.setdefault('editor', {})['auto_save_interval'] = mins
            self.app.save()
        except Exception as e:
            logger.warning('자동 저장 설정 저장 실패: %s', e)
        self._setup_auto_save(mins)
        self.statusBar().showMessage(f'자동 저장: {mins}분 간격' if mins else '자동 저장: 끔')

    def _auto_save_tick(self):
        """타이머 만료: 모든 섹션을 조용히 저장한다."""
        if self._busy or self.controller.busy:
            self.statusBar().showMessage('AI 작업 실행 중 - 자동 저장을 건너뛰었습니다.')
            return
        try:
            self.save_all(silent=True)
        except Exception as e:
            logger.warning('자동 저장 실패: %s', e)

    # ---------- 전체 섹션 AI 기호 삭제 ----------
    def clean_marks_all(self):
        """모든 섹션의 편집 칸에서 AI 특유 기호(마크다운/장식)를 제거하고 저장한다.

        설정 DB(EntitiesView)는 단일 텍스트칸이 아닌 항목별 입력폼 구조라 이 대상에서
        제외한다. 위젯명이 없는 경우(getattr 실패)는 해당 탭만 건너뛰고 계속 진행한다.
        """
        targets = [
            ('기획-아이디어', getattr(self.planning_view, 'ideaEdit', None)),
            ('기획-마스터', getattr(self.planning_view, 'masterEdit', None)),
            ('기획-핵심 기준', getattr(self.planning_view, 'contractEdit', None)),
            ('기획-전체 플롯', getattr(self.planning_view, 'masterPlotEdit', None)),
            ('스토리', getattr(self.story_view, 'detail', None)),
            ('원고', getattr(self.manuscript_view, 'editor', None)),
            ('화 종료 상태', getattr(self.end_state_view, 'edit', None)),
        ]
        changed = []
        for name, w in targets:
            if w is None:
                logger.warning('AI 기호 삭제(%s) 건너뜀: 위젯이 없습니다.', name)
                continue
            try:
                t = w.toPlainText()
                out = strip_ai_marks(t)
                if out != t:
                    w.setPlainText(out)
                    changed.append(name)
            except Exception as e:
                logger.warning('AI 기호 삭제(%s) 실패: %s', name, e)
        if changed:
            # 정리된 내용을 바로 저장해 유실을 막는다
            self.save_all(silent=True)
            msg = 'AI 특유 기호를 제거했습니다.\n- ' + '\n- '.join(changed)
            self.statusBar().showMessage(f'AI 기호 삭제: {len(changed)}곳 정리 완료')
        else:
            msg = '제거할 기호가 없습니다.'
            self.statusBar().showMessage('AI 기호 삭제: 제거할 기호 없음')
        QMessageBox.information(self, 'AI 기호 삭제', msg)

    def closeEvent(self, event):
        self._save_ui_state()
        """창 닫을 때 현재 편집 내용과 AI 집필 중 부분 결과를 먼저 보존한다."""
        try:
            active=self._active_manuscript_job
            if active and active.get('buffer'):
                chapter=int(active['chapter']); partial=''.join(active.get('buffer', []))
                if partial.strip():
                    self.pm.save_chapter(chapter, partial)
                    self.db.set_chapter_meta(chapter, f'{chapter}화', '초안', count_chars(partial), count_chars(partial, True), int(self.pm.settings['chapter_chars']))
            elif not self._busy and not self.controller.busy:
                self.save_all(silent=True)
        except Exception:
            logger.exception('종료 전 원고 저장 실패')
        # 독립 채팅창도 함께 닫기
        try:
            if hasattr(self, 'chat_window') and self.chat_window is not None:
                self.chat_window.close()
        except Exception:
            pass
        # 스레드 풀이 완료될 때까지 대기 (QThreadStorage 경고 방지)
        try:
            if hasattr(self.controller, 'pool'):
                self.controller.pool.waitForDone(3000)  # 최대 3초 대기
        except Exception:
            pass
        # Qt 작업 스레드가 종료된 뒤 프로젝트의 모든 SQLite 연결을 닫는다.
        try:
            if getattr(self, 'db', None) is not None:
                self.db.close()
        except Exception:
            logger.exception('프로젝트 DB 종료 실패')
        super().closeEvent(event)

    def write_current(self):
        """현재 화에 고정된 AI 집필. 화면을 이동해도 작업 대상 화의 결과를 계속 보존한다."""
        self._adjust_attempts = 0
        if not self._check_write_prereq(): return
        target_chapter = int(self.current)
        buffer = []
        self._active_manuscript_job = {'chapter': target_chapter, 'buffer': buffer}

        def stream_callback(token):
            token = str(token or '')
            if not token: return
            buffer.append(token)
            if self.current == target_chapter:
                try:
                    self.manuscript_view.editor.setPlainText(''.join(buffer))
                    self.manuscript_view.editor.moveCursor(QTextCursor.MoveOperation.End)
                    self.update_count()
                except Exception:
                    logger.exception('원고 스트리밍 UI 반영 실패')

        def done_callback(result):
            text = str(result if result is not None else ''.join(buffer)) or ''.join(buffer)
            self._handle_written_result(text, target_chapter)

        def cancelled_callback():
            partial=''.join(buffer)
            try:
                if partial.strip():
                    self.pm.save_chapter(target_chapter, partial)
                    self.db.set_chapter_meta(target_chapter, f'{target_chapter}화', '초안', count_chars(partial), count_chars(partial, True), int(self.pm.settings['chapter_chars']))
            finally:
                self._active_manuscript_job=None

        def error_callback(error):
            self._active_manuscript_job=None
            logger.error('AI 집필 실패(%s화): %s', target_chapter, error)

        return self.controller.write_chapter(target_chapter, stream_callback, done_callback, error_callback, cancelled_callback)

    # AI가 원고 대신 안내/거부 메시지를 반환할 때 쓰는 전형적 표현.
    # 이런 응답을 원고 파일에 저장하면 다음 집필·윤문·연속성 검사가 전부 오염된다.
    _AI_REFUSAL_MARKERS = (
        '원고를 제공하지', '원고를 공유해', '원고를 보내주시', '원고를 입력해',
        '원고가 비어', '원고가 없어', '본문을 제공해', '텍스트를 제공해',
        '내용을 제공해', '죄송합니다만', '죄송하지만', '제공해 주시면',
        '공유해 주시면', '알려주시면', '확인할 수 없습니다', '조정할 수 없습니다',
        '작성할 수 없습니다', '도와드릴 수 없',
    )

    @classmethod
    def _looks_like_ai_refusal(cls, text: str) -> bool:
        """AI 응답이 본문이 아니라 안내/거부 메시지인지 판정한다.

        거부 메시지는 대체로 짧고 안내 문구를 포함하므로, 패턴 일치 + 길이
        상한을 함께 본다. 길이 상한은 정상 원고 안에 우연히 비슷한 대사가
        들어가는 오탐을 줄이기 위한 것이다.
        """
        t = (text or '').strip()
        if not t:
            return False  # 빈 응답은 별도 분기로 처리한다
        if len(t) > 800:
            return False
        return any(m in t for m in cls._AI_REFUSAL_MARKERS)

    def _handle_written_result(self, text, chapter=None):
        """집필 결과를 시작 시 고정한 화에 저장한 뒤 필요하면 분량 보정을 수행한다.

        AI 응답이 빈 문자열이거나 "원고를 제공하라"는 안내/거부 메시지면
        절대 파일에 저장하지 않는다. 저장되면 다음 집필·윤문·기억 갱신이
        오염되어 같은 거부 응답이 반복되는 악순환이 생긴다.
        """
        chapter = int(chapter or self.current)
        target = int(self.pm.settings['chapter_chars'])
        tol = int(self.pm.settings.get('tolerance', 50))
        final_text = str(text or '')

        if not final_text.strip():
            logger.warning('%s화: AI 집필 결과가 비어 있어 저장하지 않습니다.', chapter)
            self._active_manuscript_job = None
            self.statusBar().showMessage(
                f'{chapter}화: AI가 빈 응답을 반환했습니다. 저장하지 않았습니다. 다시 집필해 주세요.'
            )
            return

        if self._looks_like_ai_refusal(final_text):
            logger.warning(
                '%s화: AI가 본문 대신 안내/거부 메시지를 반환해 저장하지 않습니다: %s',
                chapter, final_text[:120]
            )
            self._active_manuscript_job = None
            self.statusBar().showMessage(
                f'{chapter}화: AI가 원고 대신 안내 메시지를 반환했습니다. 저장하지 않았습니다. '
                '기획/직전 화 종료 상태를 확인 후 다시 집필해 주세요.'
            )
            return

        n = count_chars(final_text)

        if not target - tol <= n <= target + tol and self._adjust_attempts < 3:
            self._adjust_attempts += 1
            attempt = self._adjust_attempts
            self._run(
                f'목표 글자 수 보정 중... ({attempt}/3)',
                lambda: self.writer.adjust(final_text, target, tol),
                lambda adjusted: self._handle_written_result(
                    adjusted, chapter
                ),
            )
            return

        if not target - tol <= n <= target + tol:
            logger.warning('%s화: 3회 보정 후에도 목표 범위를 벗어남 (%s자)', chapter, n)

        # AI 생성 완료 결과는 화면의 저장 버튼을 기다리지 않고 즉시 파일/DB에 기록한다.
        self.pm.save_chapter(chapter, final_text)
        self.db.set_chapter_meta(
            chapter, f'{chapter}화', '초안' if final_text.strip() else '미작성',
            count_chars(final_text), count_chars(final_text, True), target
        )
        active = self._active_manuscript_job
        if active and int(active.get('chapter', -1)) == chapter:
            active['buffer'] = [final_text]

        if self.current == chapter:
            self.manuscript_view.editor.blockSignals(True)
            self.manuscript_view.editor.setPlainText(final_text)
            self.manuscript_view.editor.blockSignals(False)
            self.update_count()
            self.statusBar().showMessage(f'{chapter}화 초안 생성 완료 · 자동 보존됨 · 검토 후 저장하세요.')
        else:
            self.statusBar().showMessage(f'{chapter}화 AI 원고 생성 완료 · 자동 보존됨')

        self._load_chapters()
        self._active_manuscript_job = None

    def revise_current(self):
        original = self.manuscript_view.editor.toPlainText()
        text = original
        stream_started = False

        def stream_callback(token):
            nonlocal stream_started
            if not stream_started:
                self.manuscript_view.editor.clear()
                stream_started = True
            self.manuscript_view.editor.insertPlainText(token)

        def done_callback(result):
            result_text = str(result or '')
            # AI가 윤문 대신 안내/거부 메시지를 반환하면 편집창에 두면 안 된다.
            # 그대로 두면 5분 자동 저장이 그 메시지를 원고 파일에 기록해버린다.
            if not result_text.strip() or self._looks_like_ai_refusal(result_text):
                self.manuscript_view.editor.setPlainText(original)
                self.update_count()
                self.statusBar().showMessage(
                    '윤문 중단: AI가 본문 대신 안내 메시지를 반환했습니다. 원본을 복원했습니다.'
                )
                return
            self.manuscript_view.editor.setPlainText(result_text)
            self.update_count()

        if not text.strip():
            self.statusBar().showMessage('윤문할 원고가 없습니다. 먼저 본문을 작성해 주세요.')
            return
        self.controller.revise_text(text, stream_callback, done_callback)
    def generate_chapter_stories(self):
        kind,row=self.story_view.selected()
        if kind not in ('sub','long') or not row:
            QMessageBox.information(self,'세부 스토리 선택','먼저 장기 또는 세부 스토리 구간을 선택하세요.')
            return
        start=int(row['start_chapter']); end=int(row['end_chapter'])
        sub_content=(row['content'] or '')
        def work():
            raw=self.plot.generate_chapter_stories(start,end,sub_content)
            parsed=parse_chapter_stories(raw,start,end)
            if not parsed:
                raise ValueError('화별 스토리 응답을 화 번호 형식으로 파싱하지 못했습니다.')
            for n,title,content in parsed:
                sub=self.db.story_subsection_for_chapter(n); long=self.db.section_for_chapter(n)
                self.db.save_chapter_story(n,int(long['start_chapter']) if long else 0,int(long['end_chapter']) if long else 0,int(sub['start_chapter']) if sub else 0,int(sub['end_chapter']) if sub else 0,title or f'{n}화',content,'생성완료')
            return len(parsed)
        self._run('AI 화별 스토리 생성 중...',work,lambda n:(self.story_view.refresh(),self.statusBar().showMessage(f'화별 스토리 {n}개 생성 완료')))

    def regenerate_selected_chapter_story(self):
        kind,row=self.story_view.selected()
        if kind!='chapter' or not row:
            QMessageBox.information(self,'화 선택','먼저 재생성할 화별 스토리를 선택하세요.')
            return
        n=int(row['chapter_number'])
        sub=self.db.story_subsection_for_chapter(n); long=self.db.section_for_chapter(n)
        context=(sub['content'] if sub else '') or (long['content'] if long else '') or ''
        def work():
            raw=self.plot.generate_chapter_stories(n,n,context,'')
            parsed=parse_chapter_stories(raw,n,n)
            if not parsed: raise ValueError(f'{n}화 스토리 파싱에 실패했습니다.')
            _,title,content=parsed[0]
            self.db.save_chapter_story(n,int(long['start_chapter']) if long else 0,int(long['end_chapter']) if long else 0,int(sub['start_chapter']) if sub else 0,int(sub['end_chapter']) if sub else 0,title or f'{n}화',content,'생성완료')
            return 1
        self._run(f'{n}화 스토리 재생성 중...',work,lambda _:self.story_view.refresh())

    def generate_end_state_selected(self):
        n = self.end_state_view.selected_chapter()
        if not n:
            return
        text = self.pm.load_chapter(n)
        if not text.strip():
            QMessageBox.information(self,'화 종료 상태','선택한 화의 원고가 없습니다.')
            return
        def done(result):
            self.end_state_view.refresh(); self._update_state(); self.statusBar().showMessage(f'{n}화 종료 상태 생성 완료')
        self.controller.generate_end_state(n, text, done_callback=done, error_callback=lambda e:self.statusBar().showMessage(f'종료 상태 생성 실패: {e}'), cancelled_callback=lambda:self.statusBar().showMessage('화 종료 상태 생성이 취소되었습니다.'))

    def audit_long_form(self):
        view=self.end_state_view
        def on_done(result):
            view.edit.setPlainText(result or '검사 결과가 없습니다.'); self.statusBar().showMessage('장편 정밀 검사 완료')
        self._run('장편 정밀 연속성 검사 중...', lambda: self.controller.continuity_service.audit_long_form(size=50, progress_callback=lambda c,t,r,o: self.controller.progress_updated.emit(c,t,f'장편 정밀 검사 {r}'), cancelled_check=self.controller.cancelled_check()), on_done, error_callback=lambda e:self.statusBar().showMessage(f'검사 실패: {e}'), cancelled_callback=lambda:self.statusBar().showMessage('장편 정밀 검사가 취소되었습니다.'))

    def check_current(self):
        text = self.manuscript_view.editor.toPlainText()

        def done_callback(result):
            text = getattr(result, 'message', None) or str(result)
            self.end_state_view.edit.setPlainText(text)
            self.statusBar().showMessage('설정 충돌 검사 완료')

        def on_error(error):
            message = str(error).strip() if error is not None else ''
            self.statusBar().showMessage(
                f'설정 충돌 검사 실패: {message or "알 수 없는 오류"}')

        def on_cancelled():
            self.statusBar().showMessage('설정 충돌 검사가 취소되었습니다.')

        self._run('AI 연속성 검사 중...', lambda: self.controller.continuity_service.check_chapter(self.current, text),
                  lambda result: done_callback(result),
                  error_callback=on_error, cancelled_callback=on_cancelled)
        # Controller가 busy 상태로 작업을 거부하면 _run이 상태바로 알린다.
    def spellcheck_current(self):
        """요청 7-1: 맞춤법 검사. py-hanspell이 있으면 사용, 없으면 AI로 대체한다."""
        t = self.manuscript_view.editor.toPlainText()
        if not t.strip():
            return

        corrected, nerr, _ = check_spelling(t)
        if corrected is not None:
            if nerr == 0:
                QMessageBox.information(self, '맞춤법 검사', '맞춤법 오류가 없습니다.')
                return
            ret = QMessageBox.question(self, '맞춤법 검사',
                                       f'{nerr}개의 맞춤법 오류를 수정했습니다.\n수정 내용을 반영할까요?')
            if ret == QMessageBox.StandardButton.Yes:
                self.manuscript_view.editor.setPlainText(corrected)
                self.update_count()
            return
        # py-hanspell이 설치되어 있지 않으면 AI 맞춤법 검사를 사용한다.
        self._run('AI 맞춤법 검사 중...',
                  lambda: self.ai.generate('다음 원고의 맞춤법·띄어쓰기·문법 오류만 수정하라. '
                                            '내용과 문체는 절대 바꾸지 말고 수정된 원고 전체만 출력하라.\n' + t,
                                            temperature=0, max_tokens=16000),
                  lambda out: self._spell_apply(out))
    def _spell_apply(self, out):
        out = (out or '').strip()
        if not out:
            QMessageBox.information(self, '맞춤법 검사', '결과가 비어 있습니다.')
            return
        self.manuscript_view.editor.setPlainText(out)
        self.update_count()
        QMessageBox.information(self, '맞춤법 검사', 'AI 맞춤법 검사가 완료되어 본문에 반영했습니다.')
    def clean_marks_current(self):
        """요청 7-2: AI 특유 기호(마크다운/장식) 제거."""
        t = self.manuscript_view.editor.toPlainText()
        out = strip_ai_marks(t)
        if out != t:
            self.manuscript_view.editor.setPlainText(out)
            self.update_count()
            QMessageBox.information(self, 'AI 기호 삭제', 'AI 특유 기호를 제거했습니다.')
        else:
            QMessageBox.information(self, 'AI 기호 삭제', '제거할 기호가 없습니다.')
    def search_chat(self):
        msg=self.chat_window.input.toPlainText().strip(); hits=self.db.search(msg,30); self.chat_window.log.appendPlainText('\n[DB 검색]\n'+('\n'.join(f'{label}: {row}' for label,row in hits) if hits else '일치하는 DB 기록이 없습니다.')+'\n')
    def send_chat(self):
        msg=self.chat_window.input.toPlainText().strip()
        if not msg:return
        self.chat_window.input.clear()
        self.db.add_chat('user',msg,self.current)
        history=list(reversed(self.db.chat_messages(limit=20)))
        ctx=self.context.build(self.current,msg)
        messages=[{'role':'system','content':chat_system(ctx)}]
        for row in history[:-1]:
            role=row['role'] if row['role'] in ('user','assistant') else 'user'
            messages.append({'role':role,'content':row['content']})
        messages.append({'role':'user','content':msg})
        def stream(on_token):
            on_token('\nAI: ')
            collected = []
            for token in self.ai.generate_stream(
                messages, temperature=.55, max_tokens=10000
            ):
                on_token(token)
                collected.append(token)
            return ''.join(collected)

        def done(result):
            self.db.add_chat('assistant', result or '', self.current)
            self.chat_window.refresh(self.db.chat_messages(limit=200))

        self.controller.run_stream(
            'AI 작품 비서 응답 중...', stream, self.chat_window.log.appendPlainText, done
        )
    def open_ai_chat(self): self.chat_window.show(); self.chat_window.raise_(); self.chat_window.activateWindow()
    def _init_conn_test_btn(self):
        """상단 연결 테스트 버튼(●)을 초기화한다. 초기 상태는 빨강(미연결)."""
        btn = self.ui.findChild(QPushButton, 'testConnBtn')
        if btn is None:
            return
        btn.setText('')
        btn.setToolTip('AI 연결 테스트: 클릭하면 현재 활성 프로바이더로 연결을 확인합니다.')
        self._set_conn_state(False, '미연결 - 클릭하면 연결을 테스트합니다.')
        btn.clicked.connect(self.run_connection_test)

    def _conn_icon(self, color):
        """연결 상태를 표시하는 원형 색상 아이콘을 만든다."""
        pm = QPixmap(16, 16)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(color))
        p.setPen(QColor('#4B5563'))
        p.drawEllipse(2, 2, 11, 11)
        p.end()
        return QIcon(pm)

    def _set_conn_state(self, ok, message=''):
        """연결 상태 아이콘 갱신. ok: True(초록/연결됨), False(빨강/미연결), None(회색/테스트 중)"""
        btn = self.ui.findChild(QPushButton, 'testConnBtn')
        if btn is None:
            return
        color = {True: '#22C55E', False: '#EF4444', None: '#9CA3AF'}.get(ok)
        btn.setIcon(self._conn_icon(color))
        btn.setToolTip(message or 'AI 연결 테스트')

    def run_connection_test(self):
        """현재 활성 프로바이더의 저장된 설정으로 연결 테스트만 수행한다(설정 저장 없음)."""
        if self._busy or self.controller.busy:
            return  # 이미 작업 중이면 연결 테스트를 시작하지 않는다
        try:
            pid = self.app.data['active_provider']
        except Exception:
            pid = 'lmstudio'
        name = self.providers.IDS.get(pid, pid)
        cfg = self.providers.config(pid)
        base_url = str(cfg.get('base_url', '') or '')
        model = str(cfg.get('model', '') or '')
        api_key = str(cfg.get('api_key', '') or '')

        def do_test():
            try:
                tmp = self.providers.build_unsaved(pid, base_url, model, api_key)
                tester = getattr(tmp, 'quick_test', None)
                res = tester() if callable(tester) else tmp.test()
                return True, (str(res) if res else '')
            except Exception as e:
                return False, str(e)

        self._set_conn_state(None, f'{name} 연결 테스트 중...')
        self._run(f'{name} 연결 테스트 중...', do_test, self._on_conn_result)

    def _on_conn_result(self, result):
        """연결 테스트 결과를 아이콘 색상과 메시지로 표시한다."""
        ok, msg = result
        try:
            pid = self.app.data['active_provider']
        except Exception:
            pid = ''
        name = self.providers.IDS.get(pid, pid or 'AI')
        if ok:
            self._set_conn_state(True, f'{name} 연결 성공')
            self.statusBar().showMessage(f'{name} 연결 성공')
            QMessageBox.information(self, '연결 테스트', f'{name} 연결 성공\n\n{msg}')
        else:
            self._set_conn_state(False, f'{name} 연결 실패')
            self.statusBar().showMessage(f'{name} 연결 실패')
            QMessageBox.critical(self, '연결 테스트 실패', f'{name} 연결 실패\n\n{msg}')

    def open_settings(self):
        d=AISettingsDialog(self.providers,self.app,self)
        if d.exec()==QDialog.DialogCode.Accepted:self._update_ai_status(); self.apply_editor_style()
    def apply_editor_style(self):
        s=self.app.data['editor']; v=self.manuscript_view.editor; v.setFont(QFont(str(s['font_family']),int(s['font_size']))); v.setStyleSheet(f"QPlainTextEdit{{color:{s['text_color']};background-color:{s['bg_color']};}}")
    def _update_ai_status(self):
        # 여기에서 네트워크 I/O(list_models 등)를 수행하면 안 된다.
        # LM Studio가 꺼져 있으면 UI 스레드가 타임아웃까지 멈추기 때문이다.
        # 모델 자동 감지는 [설정 → 연결 테스트]에서만 수행하고, 여기서는 저장된 값만 표시한다.
        try:
            pid = self.app.data['active_provider']
            name = self.providers.IDS.get(pid, pid)
            model = (self.providers.config(pid).get('model') or '').strip()
            self.aiStatus.setText(f"AI ● {name} / {model or '모델 미설정'}")
        except Exception as e:
            logger.warning('AI 상태 갱신 실패: %s', e)
            self.aiStatus.setText('AI ● 확인 필요')
    def _update_state(self):
        """현재 집필 화 직전의 화 종료 상태만 오른쪽 사이드바에 표시한다."""
        view=self.ui.findChild(QTextBrowser,'stateText')
        if view is None: return
        chapter=int(self.current); previous=chapter-1
        row=self.db.chapter_state(previous) if previous>0 else None
        title=str(self.pm.settings.get('title','') or '작품').strip()
        content=(row['state'] if row else '') or ''
        from html import escape
        head=f'<div class="state-head"><div class="state-title">직전 화 종료 상태</div><div class="state-meta">현재 작성 화 <b>{chapter}화</b> · 기준 <b>{previous}화</b></div><div class="state-work">{escape(title)}</div></div>'
        body='' 
        if not row:
            body='<div class="state-empty">직전 화의 종료 상태가 아직 없습니다.</div>'
        else:
            blocks=[]
            import re
            matches=list(re.finditer(r'\[([^\]]+)\]\s*', content))
            if matches:
                for i,m in enumerate(matches):
                    label=m.group(1).strip(); text=content[m.end():(matches[i+1].start() if i+1<len(matches) else len(content))].strip()
                    if text: blocks.append(f'<div class="state-card"><div class="state-field">{escape(label)}</div><div class="state-body">{escape(text).replace(chr(10),"<br>")}</div></div>')
            else:
                blocks=[f'<div class="state-card"><div class="state-field">종료 상태</div><div class="state-body">{escape(content).replace(chr(10),"<br>")}</div></div>']
            body=''.join(blocks)
        view.setHtml('<style>.state-head{padding:4px 2px 10px}.state-title{font-size:16px;font-weight:700}.state-meta,.state-work{font-size:12px;color:#B7B3AD}.state-card{margin:0 0 9px;padding:8px;border:1px solid #4F4C48;border-radius:5px;background:#2D2C2B}.state-field{font-size:12px;font-weight:700;color:#D6C6AB;margin-bottom:5px}.state-body{font-size:13px;line-height:1.55}.state-empty{padding:12px;color:#A7A29B}</style>'+head+body)
        view.verticalScrollBar().setValue(0)
