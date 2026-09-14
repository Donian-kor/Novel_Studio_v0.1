from pathlib import Path
import logging
import os
import sys
import subprocess
from PySide6.QtWidgets import (QMainWindow, QMessageBox, QFileDialog, QListWidget,
                                 QStackedWidget, QLabel, QPushButton, QFrame,
                                 QPlainTextEdit, QTextBrowser, QDialog, QComboBox)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QTextCursor, QAction, QKeySequence, QIcon, QPixmap, QPainter, QColor
from novel_studio.ui.loader import load_ui
from novel_studio.ui.views.planning import PlanningView
from novel_studio.ui.views.entities import EntitiesView
from novel_studio.ui.views.ranges import RangesView
from novel_studio.ui.views.plots import PlotsView
from novel_studio.ui.views.manuscript import ManuscriptView
from novel_studio.ui.views.memory import MemoryView
from novel_studio.ui.views.chat import ChatWindow
from novel_studio.core.project import ProjectManager
from novel_studio.core.app_settings import AppSettings
from novel_studio.db.threadsafe_database import ThreadSafeDatabase as Database
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
from novel_studio.ui.dialogs import AISettingsDialog, ProjectSettingsDialog
from novel_studio.jobs.snapshot import AISnapshotStore
from novel_studio.utils.text import count_chars, strip_ai_marks, check_spelling
from novel_studio.controllers.novel_controller import NovelController

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    NAV=['기획','설정 DB','스토리 구간','화별 플롯','원고','기억 / 연속성']
    def __init__(self, project_root):
        super().__init__()
        self.setWindowTitle('Novel Studio v1.4.8')
        self.resize(1700, 1000)
        self.project_root = Path(project_root)
        self.current = 1
        self._busy = False
        self._adjust_attempts = 0
        self._active_manuscript_job = None
        self.ai_snapshots = AISnapshotStore(self.project_root)
        self._init_services()
        self._init_ui()
        self.chat_window = ChatWindow(self)
        # 메인 창이 닫히면 독립 채팅창도 함께 닫아 앱이 정상 종료되게 한다
        try:
            self.destroyed.connect(self.chat_window.close)
        except Exception:
            pass
        self._save_last_project()
        self._load_all()
        self._build_project_menu()
    def _init_services(self):
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
        self.ledger = bundle["ledger"]
        self.master_diff = bundle["master_diff"]
        self.writer = bundle["writer"]
        self.memory = bundle["memory"]
        self.checker = bundle["checker"]

        # 기존 View와 호환되는 보조 객체는 동일 인스턴스를 사용한다.
        self.idea_service = IdeaService(self.db, self.ai, self.pm)
        self.master = MasterPlanner(self.db, self.ai, self.pm)

        self.controller = bundle["controller"]
        self.controller.set_main_window(self)
        self._connect_controller_signals()
        
    def _connect_controller_signals(self):
        """Connect Controller signals to UI updates."""
        self.controller.status_changed.connect(self._on_controller_status)
        self.controller.progress_updated.connect(self._on_progress_update)
        self.controller.chapter_changed.connect(self._on_chapter_changed)
        self.controller.ai_status_changed.connect(self._update_ai_status)
        self.controller.error_occurred.connect(self._error)
    
    def _error(self, error):
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

    def _on_controller_status(self, message: str):
        self.statusBar().showMessage(message)
        if hasattr(self, 'stopBtn') and self.stopBtn is not None:
            self.stopBtn.setEnabled(self.controller.busy or self._busy)

    def _on_progress_update(self, current: int, total: int, message: str):
        """Handle progress updates from controller."""
        pct = int(current / max(1, total) * 100)
        self.statusBar().showMessage(f'{message} ({current}/{total}) {pct}%')
        # Update progress in UI if needed
        
    def _on_chapter_changed(self, chapter: int):
        """Handle chapter change from controller."""
        self.current = chapter
        self.load_chapter(chapter)
    def _init_ui(self):
        self.ui=load_ui('main_window.ui'); self.setCentralWidget(self.ui); self.nav=self.ui.findChild(QListWidget,'navList'); self.stack=self.ui.findChild(QStackedWidget,'pageStack'); self.left=self.ui.findChild(QFrame,'leftPanel'); self.right=self.ui.findChild(QFrame,'rightPanel'); self.left_handle=self.ui.findChild(QFrame,'leftHandle'); self.right_handle=self.ui.findChild(QFrame,'rightHandle'); self.aiStatus=self.ui.findChild(QLabel,'aiStatus')
        self.views=[PlanningView(self),EntitiesView(self),RangesView(self),PlotsView(self),ManuscriptView(self),MemoryView(self)]
        for v in self.views:self.stack.addWidget(v)
        self.nav.addItems(self.NAV); self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.stopBtn = self.ui.findChild(QPushButton, 'stopBtn')
        if self.stopBtn is not None:
            self.stopBtn.clicked.connect(self._stop)
            self.stopBtn.setEnabled(False)
        self.ui.findChild(QPushButton,'leftCollapse').clicked.connect(lambda:self._set_left(False)); self.ui.findChild(QPushButton,'leftExpand').clicked.connect(lambda:self._set_left(True)); self.ui.findChild(QPushButton,'rightCollapse').clicked.connect(lambda:self._set_right(False)); self.ui.findChild(QPushButton,'rightExpand').clicked.connect(lambda:self._set_right(True)); self.ui.findChild(QPushButton,'settingsBtn').clicked.connect(self.open_settings); self._init_conn_test_btn(); self.ui.findChild(QPushButton,'chatBtn').clicked.connect(self.open_ai_chat); self._set_left(True); self._set_right(True); self._build_top_dashboard()
        self.saveAllBtn = self.ui.findChild(QPushButton, 'saveAllBtn')
        if self.saveAllBtn is not None:
            # 스냅샷 생성 중 로딩 표시 후 원래 문구로 복원할 때 사용한다.
            self._save_all_btn_text = self.saveAllBtn.text()
            # clicked(bool)의 불리언을 인자로 넘기지 않도록 람다로 감싼다.
            self.saveAllBtn.clicked.connect(lambda _checked=False: self.save_all())
        ca = self.ui.findChild(QPushButton, 'cleanAllBtn')
        if ca is not None:
            ca.clicked.connect(self.clean_marks_all)
        cbo = self.ui.findChild(QComboBox, 'autoSaveCombo')
        if cbo is not None:
            self.autoSaveCombo = cbo
            for label, mins in (('자동 저장: 안 함', 0), ('자동 저장: 5분', 5), ('자동 저장: 10분', 10)):
                cbo.addItem(label, mins)
            try:
                saved_min = int(self.app.data.get('editor', {}).get('auto_save_interval', 0) or 0)
            except Exception:
                saved_min = 0
            idx = cbo.findData(saved_min)
            cbo.setCurrentIndex(idx if idx >= 0 else 0)
            cbo.currentIndexChanged.connect(self._on_auto_save_changed)
            self._setup_auto_save(saved_min)
        p=self.views[0]; p.masterBtn.clicked.connect(self.generate_master); p.diffMasterBtn.clicked.connect(self.preview_master_diff); p.contractBtn.clicked.connect(self.generate_contract); p.lockBtn.clicked.connect(self.lock_contract); p.masterPlotBtn.clicked.connect(self.generate_master_plot); p.saveMasterBtn.clicked.connect(self.save_master); p.saveContractBtn.clicked.connect(self.save_contract); p.savePlotBtn.clicked.connect(self.save_master_plot); p.generateBtn.clicked.connect(self.generate_idea); p.useBtn.clicked.connect(self.use_idea)
        s = self.views[1]
        # EntitiesView는 __init__ 내부에서 add/save/del/AI 버튼을 자체 배선함
        r=self.views[2]; r.generateBtn.clicked.connect(self.generate_sections); r.snapshotBtn.clicked.connect(self.generate_snapshot); r.saveBtn.clicked.connect(lambda: self._save_view_detail(r, '스토리 구간'))
        pl=self.views[3]; pl.generateBtn.clicked.connect(self.generate_chapter_plans); pl.allBtn.clicked.connect(self.generate_all_chapter_plans); pl.improveBtn.clicked.connect(self.improve_plot); pl.saveBtn.clicked.connect(lambda: self._save_view_detail(pl, '화별 플롯')); pl.hierBtn.clicked.connect(self.generate_hierarchical_plots)
        mem=self.views[5]
        if getattr(mem,'refreshMemoryBtn',None): mem.refreshMemoryBtn.clicked.connect(self._refresh_long_memory)
        if getattr(mem,'auditBtn',None): mem.auditBtn.clicked.connect(self.audit_long_form)
        m=self.views[4]; m.chapterList.currentRowChanged.connect(self._on_chapter_row_changed); m.editor.textChanged.connect(self.update_count); self._wire_manuscript_buttons(m)
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
        root = self.ui.layout()          # main_window.ui 루: top / body / bottom
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
        # top(첫째)와 body(둘째) 사이에 항상 보이는 상단 대시보드 삽입
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
            '<b>Novel Studio</b> v1.4.6<br><br>'
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
        self.views[0].refresh()
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

    def _run_stream(self, label, fn, done, append=None, replace=True,
                    snapshot_kind='ai_stream', snapshot_target=None,
                    error_callback=None, cancelled_callback=None):
        """스트리밍 AI 작업을 UI와 분리된 디스크 스냅샷과 함께 실행한다."""
        stream_started = False
        collected = []
        snapshot_id = self.ai_snapshots.start(snapshot_kind, snapshot_target)
        checkpoint_chars = 0

        def stream_callback(token):
            nonlocal stream_started, checkpoint_chars
            token = str(token or '')
            if not token:
                return
            collected.append(token)
            checkpoint_chars += len(token)
            # 화면을 바꿔도 결과는 이 버퍼에 계속 남는다.
            if checkpoint_chars >= 1200 or len(collected) == 1:
                checkpoint_chars = 0
                self.ai_snapshots.update(snapshot_id, ''.join(collected), target=snapshot_target)
            if append is None:
                return
            if replace and not stream_started:
                try:
                    append.clear()
                except Exception:
                    pass
                stream_started = True
            self._append_token(append, token)

        def on_done(result):
            final_text = str(result if result is not None else ''.join(collected))
            self.ai_snapshots.finish(snapshot_id, 'completed', final_text, target=snapshot_target)
            if done:
                done(result)

        def on_error(error):
            self.ai_snapshots.finish(snapshot_id, 'failed', ''.join(collected), error=str(error), target=snapshot_target)
            if error_callback:
                error_callback(error)

        def on_cancelled():
            partial = ''.join(collected)
            self.ai_snapshots.finish(snapshot_id, 'cancelled', partial, target=snapshot_target)
            if cancelled_callback:
                cancelled_callback()

        ok = self.controller.run_stream(
            label, fn, stream_callback, on_done, on_error, on_cancelled
        )
        if not ok:
            self.ai_snapshots.finish(snapshot_id, 'rejected', ''.join(collected), target=snapshot_target)
        return ok

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
        # save_current(update_memory=True)에 그대로 연결하면 update_memory=False가 되어
        # 스냅샷/기억 갱신이 영원히 실행되지 않으므로 반드시 람다로 감싼다.
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

    def _set_left(self,on): self.left.setVisible(on); self.left_handle.setVisible(not on)
    def _set_right(self,on): self.right.setVisible(on); self.right_handle.setVisible(not on)
    def _run(self, label, fn, done):
        """레거시 호출 호환용 Controller 작업 위임 래퍼."""
        return self.controller.run_task(label, fn, done)
    def _finish_job(self):
        """레거시 호환 메서드. 실제 작업 상태는 Controller가 관리한다."""
        self._busy = False
        self._adjust_attempts = 0

    def _stop(self):
        """⏹ 정지 버튼: Controller의 현재 작업에 취소를 요청한다."""
        if self.controller.stop_current_job():
            logger.info('사용자가 작업 중지를 요청했습니다.')
            self.statusBar().showMessage('작업 취소 요청됨...')
        else:
            self.statusBar().showMessage('실행 중인 작업이 없습니다.')

    def _load_all(self): self.views[0].refresh(); self.views[1].refresh(); self.views[2].refresh(); self.views[3].refresh(); self._load_chapters(); self.load_chapter(1); self._update_ai_status(); self.refresh_dashboard()
    def _load_chapters(self):
        v=self.views[4]
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
                         append=self.views[0].ideaEdit)
    def use_idea(self):
        t = self.views[0].ideaEdit.toPlainText().strip()
        if not t:
            QMessageBox.warning(self, '아이디어 필요', '먼저 아이디어를 입력하거나 [AI 아이디어 생성]을 눌러 생성하세요.')
            return
        self.db.use_idea(t)
        self.db.set_meta('idea', t)
        self.statusBar().showMessage('아이디어 확정 → 아래에서 [AI 마스터 기획 생성]을 눌러 계속하세요.')
        self.views[0].refresh()
    def generate_master(self):
        t=self.views[0].ideaEdit.toPlainText().strip() or self.db.get_meta('idea','')
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
                         append=self.views[0].masterEdit)
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
            self.views[1].refresh()
            self.statusBar().showMessage(f'마스터 기획 저장 완료 · 인물 DB {n}개 자동 동기화')
        except Exception as e:
            logger.warning('마스터→인물 자동 동기화 실패: %s',e)
            self.views[1].refresh()
            self.statusBar().showMessage('마스터 기획 저장 완료 · 인물 자동 동기화 실패')

    def preview_master_diff(self):
        old=self.db.get_plan() or ''
        new=self.views[0].masterEdit.toPlainText()
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
        self.db.save_plan(self.views[0].masterEdit.toPlainText())
        self._run('마스터 기획에서 인물 자동 동기화 중...', self.sync_master_characters, self._after_master_saved)
    def save_contract(self):
        current=self.db.get_contract()
        if current and current['locked']:
            QMessageBox.warning(self,'핵심 기준 잠금','잠긴 핵심 기준은 수정할 수 없습니다.'); return
        self.db.save_contract(self.views[0].contractEdit.toPlainText(),False); self.statusBar().showMessage('핵심 기준 저장 완료')
    def save_master_plot(self): self.db.set_meta('master_plot',self.views[0].masterPlotEdit.toPlainText()); self.statusBar().showMessage('전체 플롯 저장 완료')
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
                         append=self.views[0].contractEdit)
    def lock_contract(self):
        text=self.views[0].contractEdit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self,'핵심 기준 필요','잠글 내용이 없습니다.')
            return
        self.db.save_contract(text,True)
        self.views[0].contractEdit.setReadOnly(True)
        self.views[0].lockBtn.setEnabled(False)
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
                         lambda _: self.views[0].refresh(),
                         append=self.views[0].masterPlotEdit)
    def _previous_section_snapshot(self, start: int) -> str:
        """재생성 대상 바로 앞 구간의 확정 스냅샷을 반환한다."""
        ranges = self.plot.ranges()
        previous = None
        for s, e in ranges:
            if e < start:
                previous = (s, e)
            elif s >= start:
                break
        if not previous:
            return ''
        row = self.db.section(*previous)
        return (row['snapshot'] or '') if row else ''

    def _mark_downstream_sections_stale(self, start: int) -> None:
        """선택 구간 재생성 후 뒤쪽 구간의 기존 기억이 낡았음을 표시한다."""
        for s, e in self.plot.ranges():
            if s <= start:
                continue
            row = self.db.section(s, e)
            if row and (row['content'] or '').strip():
                self.db.save_section(s, e, '기억 갱신 필요', row['content'], row['snapshot'] or '')

    def generate_sections(self, force: bool = False):
        if not self.db.get_meta('master_plot',''): QMessageBox.warning(self,'전체 플롯 필요','먼저 전체 플롯을 생성하세요.'); return
        def work():
            prev=''
            for s,e in self.plot.ranges():
                old=self.db.section(s,e)
                if old and old['status']=='생성완료' and not force:
                    prev=old['snapshot'] or prev
                    continue
                content=self.plot.generate_story_section(s,e,prev)
                snap=self.memory.section_snapshot(s,e,content)
                self.db.save_section(s,e,'생성완료',content,snap)
                prev=snap
            return True
        label = '스토리 구간 전체 다시 생성 중...' if force else '스토리 구간 생성/이어하기 중...'
        return self._run(label,work,lambda _:self.views[2].refresh())

    def regenerate_selected_section(self):
        """선택한 스토리 구간만 다시 생성하고, 이후 구간은 기억 갱신 필요 상태로 표시한다."""
        r=self.views[2].selected()
        if not r:
            QMessageBox.information(self,'구간 선택','먼저 다시 생성할 스토리 구간을 선택하세요.')
            return
        if not self.db.get_meta('master_plot','').strip():
            QMessageBox.warning(self,'전체 플롯 필요','먼저 [기획]에서 전체 플롯을 생성하세요.')
            return
        s,e=int(r['start_chapter']),int(r['end_chapter'])
        if QMessageBox.question(
            self,'선택 구간 재생성',
            f'{s}~{e}화 스토리 구간을 새로 생성합니다.\n\n현재 구간 내용은 새 결과로 교체됩니다. 계속하시겠습니까?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        previous=self._previous_section_snapshot(s)
        def work():
            content=self.plot.generate_story_section(s,e,previous)
            if not (content or '').strip():
                raise ValueError(f'{s}~{e}화 구간 생성 결과가 비어 있습니다.')
            snap=self.memory.section_snapshot(s,e,content)
            self.db.save_section(s,e,'생성완료',content,snap)
            self._mark_downstream_sections_stale(s)
            return True
        return self._run(f'{s}~{e}화 스토리 구간 재생성 중...',work,lambda _:self.views[2].refresh())

    def regenerate_all_sections(self):
        """기존 생성 결과를 무시하고 모든 스토리 구간을 처음부터 다시 생성한다."""
        if not self.db.get_meta('master_plot','').strip():
            QMessageBox.warning(self,'전체 플롯 필요','먼저 [기획]에서 전체 플롯을 생성하세요.')
            return
        answer=QMessageBox.question(
            self,'전체 스토리 구간 다시 생성',
            '현재 생성된 모든 스토리 구간을 처음부터 다시 생성합니다.\n\n기존 구간 내용은 새 결과로 교체됩니다. 계속하시겠습니까?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        return self.generate_sections(force=True)
    def generate_snapshot(self):
        r=self.views[2].selected();
        if not r:return
        self._run('스토리 구간 기억 갱신 중...',lambda:self.memory.section_snapshot(r['start_chapter'],r['end_chapter'],r['content']),lambda t:self.db.save_section(r['start_chapter'],r['end_chapter'],r['status'],r['content'],t) or self.views[2].refresh())
    def _plan_ranges(self,start,end):
        return [(s,min(e,end)) for s,e in self.plot.ranges() if not (e<start or s>end)]
    def _generate_plans_worker(self,start,end):
        saved = 0
        for s,e in self._plan_ranges(start,end):
            if self.controller.cancel_requested:
                break
            out = self.plot.generate_chapter_plans(s,e)
            plans = parse_chapter_plans(out)
            check = validate_chapter_plans(plans, s, e)

            # 누락된 화만 1회 보완 생성하여 모델의 형식 흔들림을 흡수한다.
            if not check['valid'] and check['missing']:
                repair = self.ai.generate(repair_chapter_plans(out, s, e, check['missing']),
                                          temperature=.30, max_tokens=9000)
                plans.extend(parse_chapter_plans(repair))
                # 중복은 최신 보완 결과를 우선한다.
                merged = {}
                for n,title,body in plans:
                    if s <= n <= e:
                        merged[n] = (n,title,body)
                plans = [merged[n] for n in sorted(merged)]
                check = validate_chapter_plans(plans, s, e)

            if not check['valid']:
                missing = ', '.join(f'{n}화' for n in check['missing']) or '없음'
                extra = ', '.join(f'{n}화' for n in check['extra']) or '없음'
                raise ValueError(
                    f'{s}~{e}화 플롯을 완전히 파싱하지 못했습니다.\n'
                    f'누락: {missing} / 범위 밖: {extra}\n\n'
                    f'AI 원문 앞부분:\n{out[:1200]}'
                )

            for n,title,body in plans:
                self.db.save_chapter_plan(n,title,body,'초안')
                saved += 1
        return saved

    def generate_chapter_plans(self):
        s,e=self.views[3].start.value(),self.views[3].end.value()
        total=int(self.pm.settings['target_chapters'])
        if s < 1 or e < s or e > total:
            QMessageBox.warning(self,'화 범위 오류',f'유효한 범위는 1~{total}화입니다.')
            return
        if not self.db.get_meta('master_plot','').strip():
            QMessageBox.warning(self,'전체 플롯 필요','먼저 [기획]에서 AI 전체 플롯을 생성하거나 저장하세요.')
            return
        relevant = [r for r in self.db.sections_overlapping(s, e) if (r['content'] or '').strip()]
        if not relevant:
            QMessageBox.warning(self,'스토리 구간 필요',f'{s}~{e}화에 해당하는 스토리 구간이 없습니다.\n먼저 [스토리 구간]에서 해당 구간을 생성하세요.')
            return
        self._run(f'{s}~{e}화 개별 플롯 생성 중...',
                  lambda:self._generate_plans_worker(s,e),
                  lambda n:(self.views[3].refresh(), self.statusBar().showMessage(f'{n}개 화 플롯 저장 완료')))

    def generate_hierarchical_plots(self):
        total=int(self.pm.settings['target_chapters'])
        if not self.db.get_meta('master_plot','').strip():
            QMessageBox.warning(self,'전체 플롯 필요','먼저 [기획]에서 AI 전체 플롯을 생성하거나 저장하세요.')
            return
        def work():
            return self.plot.generate_hierarchical_plans(25)
        def done(results):
            made=sum(x[2] for x in results)
            self.views[3].refresh()
            QMessageBox.information(self,'구간별 플롯 생성 완료',f'{len(results)}개 구간에서 {made}개 화 플롯을 처리했습니다.')
        self._run(f'1~{total}화 구간별 플롯 생성 중...',work,done)

    def generate_all_chapter_plans(self):
        self.views[3].start.setValue(1)
        self.views[3].end.setValue(int(self.pm.settings['target_chapters']))
        self.generate_chapter_plans()
    def improve_plot(self):
        p=self.views[3].selected();
        if not p:return
        self._run('선택 플롯 개선 중...',lambda:self.ai.generate('기존 설정과 화별 형식을 유지하며 다음 플롯을 개선하라.\n'+p['content'],temperature=.42,max_tokens=9000),lambda t:self.db.save_chapter_plan(p['chapter_number'],p['title'],t,'초안') or self.views[3].refresh())
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
        text = self.views[4].editor.toPlainText()
        title = self.views[4].titleEdit.text().strip() or f'{chapter}화'
        self.pm.save_chapter(chapter, text)
        self.db.set_chapter_meta(
            int(chapter), title, '초안' if text.strip() else '미작성',
            count_chars(text), count_chars(text, True), int(self.pm.settings['chapter_chars'])
        )

    def load_chapter(self,n):
        self.current=int(n); v=self.views[4]
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
        t=self.views[4].editor.toPlainText(); n=count_chars(t); ns=count_chars(t,True); target=int(self.pm.settings['chapter_chars']); self.views[4].countLabel.setText(f'현재 {n:,}자 / 목표 {target:,}자 / 공백 포함 {ns:,}자')
    def _set_save_buttons_busy(self, busy: bool):
        """스냅샷 생성(백그라운드 AI 작업) 동안 저장 버튼을 로딩 상태로 잠근다.

        작업 완료/실패/취소 모든 경로에서 반드시 ``_set_save_buttons_busy(False)``로
        복원해야 한다. 복원하지 않으면 버튼이 영원히 비활성화 상태로 남는다.
        """
        pairs = (
            # (버튼, 원본 문구, 로딩 문구)
            (getattr(self, 'saveAllBtn', None),
             getattr(self, '_save_all_btn_text', '전체 저장'),
             '⏳ 스냅샷 생성 중...'),
            (getattr(self, '_save_btn', None),
             getattr(self, '_save_btn_text', '저장'),
             '⏳ 스냅샷 생성 중...'),
        )
        for btn, default_text, busy_text in pairs:
            if btn is None:
                continue
            btn.setText(busy_text if busy else default_text)
            btn.setEnabled(not busy)

    def save_current(self, update_memory=True):
        """현재 원고를 확정 저장한다. 자동 저장에서는 AI 기억 갱신을 실행하지 않는다."""
        v = self.views[4]
        t = v.editor.toPlainText()
        title = v.titleEdit.text().strip() or f'{self.current}화'
        n = count_chars(t)
        ns = count_chars(t, True)
        target = int(self.pm.settings['chapter_chars'])
        self.pm.save_chapter(self.current, t)
        self.db.set_chapter_meta(
            self.current, title, '작성완료' if t.strip() else '미작성',
            n, ns, target
        )
        self._load_chapters()
        self.statusBar().showMessage(f'{self.current}화 저장 완료')
        if update_memory and t.strip():
            if self.controller.busy:
                # busy면 run_task가 error_occurred → critical 다이얼로그를 띄우므로
                # 여기서 중복 팝업 없이 상태바로만 알린다. 원고는 이미 저장됨.
                self.statusBar().showMessage(
                    f'{self.current}화 저장 완료 · AI 작업 중이라 기억 갱신은 '
                    '작업 종료 후 [저장]을 다시 눌러주세요'
                )
                return
            # 스냅샷/연속성 갱신이 시작되는 순간 저장 버튼을 잠근다.
            # 완료/실패/취소 콜백 모두에서 복원하므로 연타로 작업이 스킵되는 일이 없다.
            self._set_save_buttons_busy(True)

            def _snapshot_done(result):
                try:
                    self.views[5].edit.setPlainText(
                        result[0][0] + '\n\n[연속성]\n' + result[1]
                    )
                    self._update_state()
                finally:
                    self._set_save_buttons_busy(False)

            def _snapshot_error(error):
                self._set_save_buttons_busy(False)

            def _snapshot_cancelled():
                self._set_save_buttons_busy(False)

            ok = self.controller.run_task(
                '확정 원고 기억/연속성 갱신 중...',
                lambda: self._update_memory_and_continuity(self.current, t),
                done_callback=_snapshot_done,
                error_callback=_snapshot_error,
                cancelled_callback=_snapshot_cancelled,
            )
            if not ok:
                # 시작 직전 busy가 된 극히 드문 레이스: 잠근 버튼을 즉시 복원한다.
                self._set_save_buttons_busy(False)
    def save_all(self, silent=False):
        """모든 섹션의 현재 편집 내용을 DB/파일에 일괄 저장한다.

        silent=True(자동 저장/창 닫기/프로젝트 전환)면 팝업 없이 상태 표시줄로만 알린다.
        """
        saved, failed = [], []
        # 1) 기획 (아이디어/마스터 기획/핵심 기준/전체 플롯)
        try:
            p = self.views[0]
            idea = p.ideaEdit.toPlainText().strip()
            if idea:
                self.db.set_meta('idea', idea)
            if p.masterEdit.toPlainText().strip():
                self.db.save_plan(p.masterEdit.toPlainText())
            c = p.contractEdit.toPlainText()
            if c.strip():
                # 잠금 상태는 유지한다 (잠금 해제가 전체 저장으로 풀리지 않게)
                prev = self.db.get_contract()
                locked = bool(prev['locked']) if prev else False
                self.db.save_contract(c, locked)
            if p.masterPlotEdit.toPlainText().strip():
                self.db.set_meta('master_plot', p.masterPlotEdit.toPlainText())
            saved.append('기획')
        except Exception as e:
            failed.append('기획'); logger.warning('전체 저장(기획) 실패: %s', e)
        # 2) 설정 DB (현재 선택/편집 중인 항목)
        try:
            if self.views[1].save_entry(quiet=True):
                saved.append('설정 DB')
        except Exception as e:
            failed.append('설정 DB'); logger.warning('전체 저장(설정 DB) 실패: %s', e)
        # 3) 스토리 구간 (현재 선택 구간 요약/스냅샷)
        try:
            if self.views[2].save_detail():
                saved.append('스토리 구간')
        except Exception as e:
            failed.append('스토리 구간'); logger.warning('전체 저장(스토리 구간) 실패: %s', e)
        # 4) 화별 플롯 (현재 선택 화 플롯)
        try:
            if self.views[3].save_detail():
                saved.append('화별 플롯')
        except Exception as e:
            failed.append('화별 플롯'); logger.warning('전체 저장(화별 플롯) 실패: %s', e)
        # 5) 원고 (현재 화)
        try:
            self.save_current(update_memory=not silent)
            saved.append('원고')
        except Exception as e:
            failed.append('원고'); logger.warning('전체 저장(원고) 실패: %s', e)
        # 6) 기억/연속성 메모
        try:
            if self.views[5].save_detail():
                saved.append('기억/연속성')
        except Exception as e:
            failed.append('기억/연속성'); logger.warning('전체 저장(기억/연속성) 실패: %s', e)
        if failed:
            if silent:
                self.statusBar().showMessage('자동 저장 실패: ' + ', '.join(failed))
            else:
                QMessageBox.warning(self, '전체 저장',
                                    '일부 저장에 실패했습니다.\n\n실패: ' + ', '.join(failed)
                                    + '\n저장됨: ' + (', '.join(saved) or '없음'))
        elif saved:
            if silent:
                self.statusBar().showMessage('자동 저장 완료: ' + ', '.join(saved))
            else:
                self.statusBar().showMessage('전체 저장 완료: ' + ', '.join(saved))
                QMessageBox.information(self, '전체 저장',
                                        '모든 내용을 저장했습니다.\n- ' + '\n- '.join(saved))
        else:
            self.statusBar().showMessage('저장할 내용이 없습니다.')

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
            ('기획-아이디어', getattr(self.views[0], 'ideaEdit', None)),
            ('기획-마스터', getattr(self.views[0], 'masterEdit', None)),
            ('기획-핵심 기준', getattr(self.views[0], 'contractEdit', None)),
            ('기획-전체 플롯', getattr(self.views[0], 'masterPlotEdit', None)),
            ('스토리 구간', getattr(self.views[2], 'detail', None)),
            ('화별 플롯', getattr(self.views[3], 'detail', None)),
            ('원고', getattr(self.views[4], 'editor', None)),
            ('기억/연속성', getattr(self.views[5], 'edit', None)),
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
        """창 닫을 때 현재 내용을 자동 저장한다 (AI 작업 중이면 건너뜀)."""
        try:
            if not self._busy and not self.controller.busy:
                self.save_all(silent=True)
        except Exception:
            pass
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
        super().closeEvent(event)

    def write_current(self):
        """현재 화에 귀속된 AI 집필 작업을 시작한다. 화면 전환과 무관하게 결과를 보존한다."""
        self._adjust_attempts = 0
        if not self._check_write_prereq():
            return

        target_chapter = int(self.current)
        buffer = []
        snapshot_id = self.ai_snapshots.start(
            'manuscript_write', {'chapter': target_chapter}
        )
        self._active_manuscript_job = {
            'chapter': target_chapter,
            'buffer': buffer,
            'snapshot_id': snapshot_id,
        }
        checkpoint_chars = 0

        def stream_callback(token):
            nonlocal checkpoint_chars
            token = str(token or '')
            if not token:
                return
            buffer.append(token)
            checkpoint_chars += len(token)
            if checkpoint_chars >= 1200 or len(buffer) == 1:
                checkpoint_chars = 0
                self.ai_snapshots.update(
                    snapshot_id, ''.join(buffer), target={'chapter': target_chapter}
                )
            # 현재 화면이 대상 화일 때만 UI를 갱신한다. 다른 화를 보고 있어도
            # 작업 버퍼와 스냅샷은 계속 누적되므로 화면 전환이 결과를 잃게 만들지 않는다.
            if self.current == target_chapter:
                try:
                    self.views[4].editor.setPlainText(''.join(buffer))
                    self.views[4].editor.moveCursor(QTextCursor.MoveOperation.End)
                    self.update_count()
                except Exception:
                    logger.exception('원고 스트리밍 UI 반영 실패')

        def done_callback(result):
            text = str(result if result is not None else ''.join(buffer))
            if not text.strip():
                text = ''.join(buffer)
            self._handle_written_result(text, target_chapter, snapshot_id)

        def cancelled_callback():
            partial = ''.join(buffer)
            try:
                if partial.strip():
                    self.pm.save_chapter(target_chapter, partial)
                    self.db.set_chapter_meta(
                        target_chapter, f'{target_chapter}화', '초안',
                        count_chars(partial), count_chars(partial, True),
                        int(self.pm.settings['chapter_chars'])
                    )
                self.ai_snapshots.finish(
                    snapshot_id, 'cancelled', partial,
                    target={'chapter': target_chapter}
                )
            except Exception:
                logger.exception('AI 집필 취소 시 부분 원고 저장 실패')
            self._active_manuscript_job = None

        def error_callback(error):
            self.ai_snapshots.finish(
                snapshot_id, 'failed', ''.join(buffer),
                error=str(error), target={'chapter': target_chapter}
            )
            self._active_manuscript_job = None
            logger.error('AI 집필 실패(%s화): %s', target_chapter, error)

        ok = self.controller.write_chapter(
            target_chapter, stream_callback, done_callback,
            error_callback, cancelled_callback
        )
        if not ok:
            self.ai_snapshots.finish(
                snapshot_id, 'rejected', ''.join(buffer),
                target={'chapter': target_chapter}
            )
            self._active_manuscript_job = None

    def _handle_written_result(self, text, chapter=None, snapshot_id=None):
        """집필 결과를 시작 시 고정한 화에 저장한 뒤 필요하면 분량 보정을 수행한다."""
        chapter = int(chapter or self.current)
        target = int(self.pm.settings['chapter_chars'])
        tol = int(self.pm.settings.get('tolerance', 50))
        n = count_chars(text)

        if not target - tol <= n <= target + tol and self._adjust_attempts < 3:
            self._adjust_attempts += 1
            attempt = self._adjust_attempts
            self._run(
                f'목표 글자 수 보정 중... ({attempt}/3)',
                lambda: self.writer.adjust(text, target, tol),
                lambda adjusted: self._handle_written_result(
                    adjusted, chapter, snapshot_id
                ),
            )
            return

        if not target - tol <= n <= target + tol:
            logger.warning('%s화: 3회 보정 후에도 목표 범위를 벗어남 (%s자)', chapter, n)

        final_text = str(text or '')
        # AI 생성 완료 결과는 화면의 저장 버튼을 기다리지 않고 즉시 파일/DB에 기록한다.
        self.pm.save_chapter(chapter, final_text)
        self.db.set_chapter_meta(
            chapter, f'{chapter}화', '초안' if final_text.strip() else '미작성',
            count_chars(final_text), count_chars(final_text, True), target
        )
        if snapshot_id:
            self.ai_snapshots.finish(
                snapshot_id, 'completed', final_text,
                target={'chapter': chapter}
            )
        active = self._active_manuscript_job
        if active and int(active.get('chapter', -1)) == chapter:
            active['buffer'] = [final_text]

        if self.current == chapter:
            self.views[4].editor.blockSignals(True)
            self.views[4].editor.setPlainText(final_text)
            self.views[4].editor.blockSignals(False)
            self.update_count()
            self.statusBar().showMessage(f'{chapter}화 초안 생성 완료 · 자동 보존됨 · 검토 후 저장하세요.')
        else:
            self.statusBar().showMessage(f'{chapter}화 AI 원고 생성 완료 · 자동 보존됨')

        self._load_chapters()
        self._active_manuscript_job = None

    def _update_memory_and_continuity(self, chapter: int, text: str) -> tuple:
        """확정 원고를 기준으로 장기 기억과 연속성을 갱신한다."""
        prev = self.db.latest_chapter_state(chapter - 1)
        previous_state = prev['state'] if prev else ''
        memory_result = self.controller.memory_service.update_memory(
            chapter, text, previous_state
        )
        continuity_result = self.controller.continuity_service.check_chapter(
            chapter, text
        )
        return memory_result, continuity_result.message


    def revise_current(self):
        text = self.views[4].editor.toPlainText()
        stream_started = False

        def stream_callback(token):
            nonlocal stream_started
            if not stream_started:
                self.views[4].editor.clear()
                stream_started = True
            self.views[4].editor.insertPlainText(token)

        def done_callback(result):
            self.views[4].editor.setPlainText(result)
            self.update_count()

        self.controller.revise_text(text, stream_callback, done_callback)
    def _refresh_long_memory(self):
        path=self.project_root/'chapters'/f'{self.current:03d}.txt'
        if not path.exists(): QMessageBox.information(self,'장기 기억','현재 화 원고가 없습니다.'); return
        try:
            sm,st=self.memory.update(self.current,path.read_text(encoding='utf-8'))
            self.views[5].edit.setPlainText(sm+'\n\n[상태]\n'+st)
        except Exception as e: QMessageBox.critical(self,'장기 기억 오류',str(e))

    def audit_long_form(self):
        """장편 정밀 연속성 검사를 Controller에서 실행한다."""
        mem = self.views[5]

        def on_done(result):
            mem.edit.setPlainText(result or '검사 결과가 없습니다.')
            self.statusBar().showMessage('장편 정밀 검사 완료')

        self.controller.audit_long_form(size=50, done_callback=on_done)

    def check_current(self):
        text = self.views[4].editor.toPlainText()
        def done_callback(result):
            text = getattr(result, 'message', None) or str(result)
            self.views[5].edit.setPlainText(text)
        
        self.controller.check_current_chapter(self.current, text, done_callback)
    def spellcheck_current(self):
        """요청 7-1: 맞춤법 검사. py-hanspell이 있으면 사용, 없으면 AI로 대체한다."""
        t = self.views[4].editor.toPlainText()
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
                self.views[4].editor.setPlainText(corrected)
                self.update_count()
            return
        # py-hanspell 미설치 → AI 맞춤법 검사
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
        self.views[4].editor.setPlainText(out)
        self.update_count()
        QMessageBox.information(self, '맞춤법 검사', 'AI 맞춤법 검사가 완료되어 본문에 반영했습니다.')
    def clean_marks_current(self):
        """요청 7-2: AI 특유 기호(마크다운/장식) 제거."""
        t = self.views[4].editor.toPlainText()
        out = strip_ai_marks(t)
        if out != t:
            self.views[4].editor.setPlainText(out)
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
        s=self.app.data['editor']; v=self.views[4].editor; v.setFont(QFont(str(s['font_family']),int(s['font_size']))); v.setStyleSheet(f"QPlainTextEdit{{color:{s['text_color']};background-color:{s['bg_color']};}}")
    def _update_ai_status(self):
        # NOTE: 여기서 네트워크 I/O(list_models 등)를 하면 안 된다.
        # LM Studio가 꺼져 있으면 UI 스레드가 타임아웃까지 멈추기 때문.
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
        """우측 사이드바의 직전 확정 상태 스냅샷을 가독성 높은 카드 형태로 표시한다.

        현재 작성 중인 화는 아직 확정 전일 수 있으므로, 스냅샷 기준은 항상
        ``현재 화 - 1``을 사용한다. 예: 11화 작성 화면 -> state:10.
        """
        view = self.ui.findChild(QTextBrowser, 'stateText')
        if view is None:
            return

        chapter = int(self.current)
        requested_snapshot_chapter = chapter - 1
        row = (self.db.snapshot(f'state:{requested_snapshot_chapter}')
               if requested_snapshot_chapter > 0 else None)
        if row is None:
            # state:N-1이 없으면 'N-1 이하 최신'으로만 대체한다.
            # (그냥 최신 전체를 가져오면 미확정인 현재 화 스냅샷이 섞일 수 있다.)
            row = self.db.latest_state_snapshot(
                requested_snapshot_chapter if requested_snapshot_chapter > 0 else None
            )
        snapshot_chapter = 0
        if row:
            try:
                snapshot_chapter = int(str(row['scope']).split(':', 1)[1])
            except (ValueError, IndexError, KeyError, TypeError):
                snapshot_chapter = requested_snapshot_chapter if requested_snapshot_chapter > 0 else 0
        title = str(self.pm.settings.get('title', '') or '작품').strip()
        content = (row['content'] or '').strip() if row else ''

        def esc(text: str) -> str:
            from html import escape
            return escape(text).replace('\n', '<br>')

        import re
        blocks = []
        if content:
            pattern = re.compile(r'\[([^\]]+)\]\s*')
            matches = list(pattern.finditer(content))
            if matches:
                for i, m in enumerate(matches):
                    label = m.group(1).strip()
                    start = m.end()
                    end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
                    body = content[start:end].strip()
                    if not body:
                        continue
                    blocks.append((label, body))
            else:
                # AI가 필드 태그 없이 문장을 반환한 경우에도 일반 본문으로 표시한다.
                blocks.append(('상태 요약', content[:5000]))

        parts = [
            '<div class="snapshot-head">'
            '<div class="snapshot-title">현재 상태 스냅샷</div>'
            f'<div class="snapshot-meta">현재 작성 화 <b>{chapter}화</b> · 기준 스냅샷 <b>{snapshot_chapter}화</b></div>'
            f'<div class="snapshot-work">{esc(title)}</div>'
            '</div>'
        ]
        if not row:
            parts.append('<div class="snapshot-empty">아직 직전 확정 화의 상태 스냅샷이 없습니다.</div>')
        else:
            for label, body in blocks:
                parts.append(
                    '<div class="snapshot-card">'
                    f'<div class="snapshot-field">{esc(label)}</div>'
                    f'<div class="snapshot-body">{esc(body)}</div>'
                    '</div>'
                )
        view.setStyleSheet(
            "QTextBrowser { background:#252525; color:#E8E6E3; border:1px solid #5E5B57; border-radius:6px; padding:6px; }"
        )
        view.setHtml(
            '<style>'
            '.snapshot-head{padding:4px 2px 10px 2px;}'
            '.snapshot-title{font-size:16px;font-weight:700;color:#F2F0EC;margin-bottom:4px;}'
            '.snapshot-meta{font-size:12px;color:#B7B3AD;margin-bottom:3px;}'
            '.snapshot-work{font-size:12px;color:#8F8A83;}'
            '.snapshot-card{margin:0 0 9px 0;padding:8px 9px;border:1px solid #4F4C48;border-radius:5px;background:#2D2C2B;}'
            '.snapshot-field{font-size:12px;font-weight:700;color:#D6C6AB;margin-bottom:5px;}'
            '.snapshot-body{font-size:13px;line-height:1.55;color:#E4E1DD;}'
            '.snapshot-empty{margin-top:4px;padding:12px;border:1px dashed #5A5651;border-radius:5px;color:#A7A29B;line-height:1.5;}'
            '</style>' + ''.join(parts)
        )
        view.verticalScrollBar().setValue(0)
