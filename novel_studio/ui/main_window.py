from pathlib import Path
import logging
import os
import sys
import subprocess
from PySide6.QtWidgets import (QMainWindow, QMessageBox, QFileDialog, QListWidget,
                                 QStackedWidget, QLabel, QPushButton, QFrame,
                                 QPlainTextEdit, QDialog)
from PySide6.QtCore import QThreadPool
from PySide6.QtGui import QFont, QTextCursor, QAction, QKeySequence
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
from novel_studio.db.database import Database
from novel_studio.ai.provider_manager import ProviderManager
from novel_studio.ai.engine import AIEngine
from novel_studio.ai.context import ContextManager
from novel_studio.ai.prompts import (chat_system, entity_extra, master as master_prompt,
                                     contract as contract_prompt,
                                     master_plot as master_plot_prompt, idea as idea_prompt,
                                     SECTIONS)
from novel_studio.services.idea_service import IdeaService
from novel_studio.planning.master_planner import MasterPlanner
from novel_studio.plot.plot_manager import PlotManager
from novel_studio.plot.parser import parse_chapter_plans
from novel_studio.manuscript.chapter_writer import ChapterWriter
from novel_studio.memory.memory_manager import MemoryManager
from novel_studio.continuity.checker import ContinuityChecker
from novel_studio.jobs.worker import Job, StreamJob
from novel_studio.ui.dialogs import AISettingsDialog, ProjectSettingsDialog
from novel_studio.utils.text import count_chars, strip_ai_marks, check_spelling

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    NAV=['기획','설정 DB','스토리 구간','화별 플롯','원고','기억 / 연속성']
    def __init__(self, project_root):
        super().__init__()
        self.setWindowTitle('Novel Studio v1.0 Final')
        self.resize(1700, 1000)
        self.project_root = Path(project_root)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.current = 1
        self._busy = False
        self._current_job = None
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
        self.pm=ProjectManager(); self.pm.open(self.project_root); self.app=AppSettings(); self.db=Database(self.project_root/'novel.db'); total=int(self.pm.settings.get('target_chapters',500)); target=int(self.pm.settings.get('chapter_chars',5000)); self.db.ensure_chapters(total,target); self.providers=ProviderManager(self.app); self.ai=AIEngine(self.providers,self.app); self.context=ContextManager(self.db,self.pm,self.app); self.idea_service=IdeaService(self.db,self.ai,self.pm); self.master=MasterPlanner(self.db,self.ai,self.pm); self.plot=PlotManager(self.db,self.ai,self.pm); self.writer=ChapterWriter(self.db,self.ai,self.pm,self.context); self.memory=MemoryManager(self.db,self.ai); self.checker=ContinuityChecker(self.db,self.ai,self.context)
    def _init_ui(self):
        self.ui=load_ui('main_window.ui'); self.setCentralWidget(self.ui); self.nav=self.ui.findChild(QListWidget,'navList'); self.stack=self.ui.findChild(QStackedWidget,'pageStack'); self.left=self.ui.findChild(QFrame,'leftPanel'); self.right=self.ui.findChild(QFrame,'rightPanel'); self.left_handle=self.ui.findChild(QFrame,'leftHandle'); self.right_handle=self.ui.findChild(QFrame,'rightHandle'); self.aiStatus=self.ui.findChild(QLabel,'aiStatus')
        self.views=[PlanningView(self),EntitiesView(self),RangesView(self),PlotsView(self),ManuscriptView(self),MemoryView(self)]
        for v in self.views:self.stack.addWidget(v)
        self.nav.addItems(self.NAV); self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.stopBtn = self.ui.findChild(QPushButton, 'stopBtn')
        if self.stopBtn is not None:
            self.stopBtn.clicked.connect(self._stop)
            self.stopBtn.setEnabled(False)
        self.ui.findChild(QPushButton,'leftCollapse').clicked.connect(lambda:self._set_left(False)); self.ui.findChild(QPushButton,'leftExpand').clicked.connect(lambda:self._set_left(True)); self.ui.findChild(QPushButton,'rightCollapse').clicked.connect(lambda:self._set_right(False)); self.ui.findChild(QPushButton,'rightExpand').clicked.connect(lambda:self._set_right(True)); self.ui.findChild(QPushButton,'settingsBtn').clicked.connect(self.open_settings); self.ui.findChild(QPushButton,'chatBtn').clicked.connect(self.open_ai_chat); self._set_left(True); self._set_right(True); self._build_top_dashboard()
        p=self.views[0]; p.masterBtn.clicked.connect(self.generate_master); p.contractBtn.clicked.connect(self.generate_contract); p.lockBtn.clicked.connect(self.lock_contract); p.masterPlotBtn.clicked.connect(self.generate_master_plot); p.saveMasterBtn.clicked.connect(self.save_master); p.saveContractBtn.clicked.connect(self.save_contract); p.savePlotBtn.clicked.connect(self.save_master_plot); p.generateBtn.clicked.connect(self.generate_idea); p.useBtn.clicked.connect(self.use_idea)
        s = self.views[1]
        # EntitiesView는 __init__ 내부에서 add/save/del/AI 버튼을 자체 배선함
        r=self.views[2]; r.generateBtn.clicked.connect(self.generate_sections); r.snapshotBtn.clicked.connect(self.generate_snapshot)
        pl=self.views[3]; pl.generateBtn.clicked.connect(self.generate_chapter_plans); pl.allBtn.clicked.connect(self.generate_all_chapter_plans); pl.improveBtn.clicked.connect(self.improve_plot)
        m=self.views[4]; m.chapterList.currentRowChanged.connect(lambda row:self.load_chapter(row+1)); m.editor.textChanged.connect(self.update_count); self._wire_manuscript_buttons(m)
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
            rows = self.db.chapters()
            done = sum(1 for r in rows if r['status'] in ('작성완료', '확정', '윤문완료'))
            total = int(p.get('target_chapters', 500) or 500)
            chars = sum(r['char_count'] or 0 for r in rows)
            active = len([x for x in self.db.foreshadows() if x['status'] != '회수'])
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
            '<b>Novel Studio</b> v1.0 Final<br><br>'
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
            self._restart_with(dlg.selected_project)

    def open_project(self):
        from novel_studio.ui.startup import StartupDialog
        dlg = StartupDialog()
        if dlg.exec() == dlg.DialogCode.Accepted and dlg.selected_project:
            self._save_last_project(dlg.selected_project)
            self._restart_with(dlg.selected_project)

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
    def _run_stream(self, label, fn, done, append=None):
        """스트리밍 AI 작업 실행. append는 토큰이 실시간으로 채워질 QPlainTextEdit."""
        if self._busy:
            QMessageBox.warning(self, '작업 중',
                                '이미 AI 작업이 실행 중입니다.\n정지하려면 상단의 ⏹ 정지 버튼을 누르세요.')
            return
        self._busy = True
        if hasattr(self, 'stopBtn'):
            self.stopBtn.setEnabled(True)
        self.statusBar().showMessage(label)
        job = StreamJob(fn)
        self._current_job = job
        self._stream_target = None
        if append is not None:
            # 원고 에디터로 스트리밍할 때 잦은 textChanged 갱신으로 UI가 느려지지 않도록 차단
            if append is self.views[4].editor:
                append.blockSignals(True)
                self._stream_target = append
            job.signals.progress.connect(lambda t, w=append: self._append_token(w, t))
        job.signals.finished.connect(lambda v: self._on_done(done, v))
        job.signals.error.connect(self._on_error)
        job.signals.cancelled.connect(self._on_cancelled)
        self.pool.start(job)

    def _append_token(self, widget, t):
        """토큰 조각을 위젯 끝에 실시간으로 입력한다."""
        try:
            cur = widget.textCursor()
            cur.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.MoveAnchor)
            widget.setTextCursor(cur)
            widget.insertPlainText(t)
        except Exception:
            pass
        if widget is getattr(self.views[4], 'editor', None):
            self._stream_tick = getattr(self, '_stream_tick', 0) + 1
            if self._stream_tick % 25 == 0:
                self.update_count()

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
        for b in m.ui.findChildren(QPushButton):
            if b.text().strip() == '저장':
                b.clicked.connect(self.save_current)
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
        if self._busy:
            QMessageBox.warning(self, '작업 중', '이미 AI 작업이 실행 중입니다.\n정지하려면 상단의 ⏹ 정지 버튼을 누르세요.')
            return
        self._busy = True
        if hasattr(self, 'stopBtn'):
            self.stopBtn.setEnabled(True)
        self.statusBar().showMessage(label)
        job = Job(fn)
        self._current_job = job
        job.signals.finished.connect(lambda v: self._on_done(done, v))
        job.signals.error.connect(self._on_error)
        job.signals.cancelled.connect(self._on_cancelled)
        self.pool.start(job)
    def _finish_job(self):
        """공통 정리: 작업 플래그 해제 및 Stop 버튼 비활성화"""
        self._busy = False
        self._current_job = None
        if hasattr(self, 'stopBtn'):
            self.stopBtn.setEnabled(False)
        # 스트리밍 중 블로킹했던 에디터 신호를 복구한다
        target = getattr(self, '_stream_target', None)
        if target is not None:
            try:
                target.blockSignals(False)
            except Exception:
                pass
            self._stream_target = None
    def _stop(self):
        """⏹ 정지 버튼: 실행 중인 AI 작업을 취소한다."""
        if self._current_job is not None and self._busy:
            logger.info('사용자가 작업 중지를 요청했습니다.')
            self._current_job.cancel()
            self.statusBar().showMessage('작업 취소 요청됨...')
        else:
            self.statusBar().showMessage('실행 중인 작업이 없습니다.')
    def _on_done(self, done, result):
        if self._current_job is not None and self._current_job.is_cancelled():
            return
        self._finish_job()
        self._update_ai_status()
        if done:
            done(result)
    def _on_error(self, e):
        if self._current_job is not None and self._current_job.is_cancelled():
            return
        logger.error('AI 작업 오류: %s', e)
        self._finish_job()
        self._update_ai_status()
        self._error(e)
    def _on_cancelled(self):
        """취소된 작업의 최종 정리"""
        logger.info('AI 작업이 취소되었습니다.')
        self._finish_job()
        self._update_ai_status()
        self.statusBar().showMessage('작업이 취소되었습니다.')
    def _error(self,e): self.statusBar().showMessage('오류'); QMessageBox.critical(self,'작업 오류',e)
    def _load_all(self): self.views[0].refresh(); self.views[1].refresh(); self.views[2].refresh(); self.views[3].refresh(); self._load_chapters(); self.load_chapter(1); self._update_ai_status(); self.refresh_dashboard()
    def _load_chapters(self):
        v=self.views[4]; v.chapterList.clear();
        for r in self.db.chapters(): v.chapterList.addItem(f"{r['number']:03d}화 | {r['status']} | {r['char_count']:,}자")
        self.refresh_dashboard()
    def generate_idea(self):
        def stream(on_token):
            previous = '\n'.join(r['content'] for r in self.db.recent_ideas(10))
            collected = []
            for t in self.ai.generate_stream(idea_prompt(self.pm.settings, previous),
                                             temperature=.9, max_tokens=800):
                if self._current_job is not None and self._current_job.is_cancelled():
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
                if self._current_job is not None and self._current_job.is_cancelled():
                    break
                on_token(piece)
                collected.append(piece)
            out = ''.join(collected)
            if out.strip():
                self.db.save_plan(out)
                self.db.set_meta('idea', t)
            return out
        self._run_stream('AI 마스터 기획 생성 중...', stream,
                         lambda _: self.views[0].refresh(),
                         append=self.views[0].masterEdit)
    def save_master(self): self.db.save_plan(self.views[0].masterEdit.toPlainText()); self.statusBar().showMessage('마스터 기획 저장 완료')
    def save_contract(self): self.db.save_contract(self.views[0].contractEdit.toPlainText(),False); self.statusBar().showMessage('핵심 기준 저장 완료')
    def save_master_plot(self): self.db.set_meta('master_plot',self.views[0].masterPlotEdit.toPlainText()); self.statusBar().showMessage('전체 플롯 저장 완료')
    def generate_contract(self):
        if not self.db.get_plan(): return
        txt = '\n\n'.join(f'[{s}]\n{self.db.section_content(s)}' for s in SECTIONS)
        def stream(on_token):
            collected = []
            for piece in self.ai.generate_stream(
                    contract_prompt(self.db.get_plan(), txt, int(self.pm.settings['target_chapters'])),
                    temperature=.22, max_tokens=6000):
                if self._current_job is not None and self._current_job.is_cancelled():
                    break
                on_token(piece)
                collected.append(piece)
            out = ''.join(collected)
            if out.strip():
                self.db.save_contract(out, False)
            return out
        self._run_stream('장편 핵심 기준 추출 중...', stream, lambda _: None,
                         append=self.views[0].contractEdit)
    def lock_contract(self): self.db.save_contract(self.views[0].contractEdit.toPlainText(),True); self.statusBar().showMessage('핵심 기준 잠금 완료')
    def generate_master_plot(self):
        if not self.db.get_contract(): QMessageBox.warning(self,'핵심 기준 필요','먼저 핵심 기준을 추출하세요.'); return
        c = self.db.get_contract()
        def stream(on_token):
            collected = []
            for piece in self.ai.generate_stream(
                    master_plot_prompt(self.db.get_plan(), c['content'] if c else '',
                                       int(self.pm.settings['target_chapters'])),
                    temperature=.62, max_tokens=12000):
                if self._current_job is not None and self._current_job.is_cancelled():
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
    def generate_sections(self):
        if not self.db.get_meta('master_plot',''): QMessageBox.warning(self,'전체 플롯 필요','먼저 전체 플롯을 생성하세요.'); return
        def work():
            prev=''
            for s,e in self.plot.ranges():
                old=self.db.section(s,e)
                if old and old['status']=='생성완료': prev=old['snapshot'] or prev; continue
                content=self.plot.generate_story_section(s,e,prev); snap=self.memory.section_snapshot(s,e,content); self.db.save_section(s,e,'생성완료',content,snap); prev=snap
            return True
        self._run('스토리 구간 생성/이어하기 중...',work,lambda _:self.views[2].refresh())
    def generate_snapshot(self):
        r=self.views[2].selected();
        if not r:return
        self._run('스토리 구간 기억 갱신 중...',lambda:self.memory.section_snapshot(r['start_chapter'],r['end_chapter'],r['content']),lambda t:self.db.save_section(r['start_chapter'],r['end_chapter'],r['status'],r['content'],t) or self.views[2].refresh())
    def _plan_ranges(self,start,end):
        return [(s,min(e,end)) for s,e in self.plot.ranges() if not (e<start or s>end)]
    def _generate_plans_worker(self,start,end):
        for s,e in self._plan_ranges(start,end):
            out=self.plot.generate_chapter_plans(s,e)
            for n,title,body in parse_chapter_plans(out): self.db.save_chapter_plan(n,title,body,'초안')
        return True
    def generate_chapter_plans(self):
        s,e=self.views[3].start.value(),self.views[3].end.value(); self._run(f'{s}~{e}화 개별 플롯 생성 중...',lambda:self._generate_plans_worker(s,e),lambda _:self.views[3].refresh())
    def generate_all_chapter_plans(self): self.views[3].start.setValue(1); self.views[3].end.setValue(int(self.pm.settings['target_chapters'])); self.generate_chapter_plans()
    def improve_plot(self):
        p=self.views[3].selected();
        if not p:return
        self._run('선택 플롯 개선 중...',lambda:self.ai.generate('기존 설정과 화별 형식을 유지하며 다음 플롯을 개선하라.\n'+p['content'],temperature=.42,max_tokens=9000),lambda t:self.db.save_chapter_plan(p['chapter_number'],p['title'],t,'초안') or self.views[3].refresh())
    def load_chapter(self,n):
        self.current=int(n); v=self.views[4]; v.editor.blockSignals(True); v.editor.setPlainText(self.pm.load_chapter(self.current)); v.editor.blockSignals(False); r=self.db.chapter(self.current); v.titleEdit.setText(r['title'] if r else f'{self.current}화'); self.update_count(); self._update_state();
        if hasattr(self,'chat_window'): self.chat_window.refresh(self.db.chat_messages())
    def update_count(self):
        t=self.views[4].editor.toPlainText(); n=count_chars(t); ns=count_chars(t,True); target=int(self.pm.settings['chapter_chars']); self.views[4].countLabel.setText(f'현재 {n:,}자 / 목표 {target:,}자 / 공백 포함 {ns:,}자'); self.ui.findChild(QLabel,'countLabel').setText(f'현재 {n:,}자 / 목표 {target:,}자 / 공백 포함 {ns:,}자')
    def save_current(self):
        v=self.views[4]; t=v.editor.toPlainText(); n=count_chars(t); ns=count_chars(t,True); target=int(self.pm.settings['chapter_chars']); self.pm.save_chapter(self.current,t); self.db.set_chapter_meta(self.current,v.titleEdit.text().strip() or f'{self.current}화','작성완료' if t.strip() else '미작성',n,ns,target); self._load_chapters(); self.statusBar().showMessage(f'{self.current}화 저장 완료')
    def write_current(self):
        """요청 2·4: 기획 확인 후 실시간 스트리밍으로 집필한다."""
        if not self._check_write_prereq():
            return

        def stream(on_token):
            collected = []
            for t in self.writer.write_stream(self.current):
                if self._current_job is not None and self._current_job.is_cancelled():
                    break
                on_token(t)
                collected.append(t)
            return ''.join(collected)

        self._run_stream(f'{self.current}화 AI 집필 중...', stream, self._after_write,
                         append=self.views[4].editor)
    def _after_write(self,t):
        if self._current_job is not None and self._current_job.is_cancelled():
            return
        target=int(self.pm.settings['chapter_chars']); tol=int(self.pm.settings['tolerance']); n=count_chars(t)
        if not target-tol<=n<=target+tol:
            self._run('목표 글자 수 보정 중...',lambda:self.writer.adjust(t,target,tol),self._after_write); return
        self.views[4].editor.setPlainText(t); self.update_count();
        def memory_job(): return self.memory.update(self.current,t),self.checker.check(self.current,t)
        self._run('기억/연속성 자동 갱신 중...',memory_job,lambda result:self.views[5].edit.setPlainText(result[0][0]+'\n\n[연속성]\n'+result[1]))
    def revise_current(self): self._run('AI 윤문 중...',lambda:self.ai.generate('사건과 설정을 변경하지 말고 다음 원고를 자연스럽게 윤문하라. 본문만 출력.\n'+self.views[4].editor.toPlainText(),temperature=.38,max_tokens=14000),self._apply_text)
    def _apply_text(self,t): self.views[4].editor.setPlainText(t); self.update_count()
    def check_current(self): self._run('AI 연속성 검사 중...',lambda:self.checker.check(self.current,self.views[4].editor.toPlainText()),lambda t:self.views[5].edit.setPlainText(t))
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
        msg=self.chat_window.input.toPlainText().strip();
        if not msg:return
        self.chat_window.input.clear(); self.db.add_chat('user',msg,self.current); hits=self.db.search(msg,40); evidence='\n'.join(f'[{l}] {r}' for l,r in hits); ctx=self.context.build(self.current,msg)+'\n\n[DB SEARCH EVIDENCE]\n'+evidence
        def stream(on_token):
            on_token('\nAI: ')
            collected = []
            for t in self.ai.generate_stream([{'role':'system','content':chat_system(ctx)},
                                              {'role':'user','content':msg}],
                                             temperature=.55, max_tokens=10000):
                if self._current_job is not None and self._current_job.is_cancelled():
                    break
                on_token(t)
                collected.append(t)
            return ''.join(collected)
        self._run_stream('AI 작품 비서 응답 중...', stream,
                         lambda t:(self.db.add_chat('assistant',t,self.current),
                                   self.chat_window.refresh(self.db.chat_messages())),
                         append=self.chat_window.log)
    def open_ai_chat(self): self.chat_window.show(); self.chat_window.raise_(); self.chat_window.activateWindow()
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
    def _update_state(self): self.ui.findChild(QPlainTextEdit,'stateText').setPlainText(f"현재 화: {self.current}화\n작품: {self.pm.settings.get('title','')}\n\n"+(self.db.snapshot(f'state:{self.current-1}')['content'][:3000] if self.current>1 and self.db.snapshot(f'state:{self.current-1}') else '현재 상태 스냅샷이 없습니다.'))
