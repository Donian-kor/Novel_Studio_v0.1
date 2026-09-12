from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import QMainWindow, QWidget, QListWidget, QStackedWidget, QMessageBox, QFileDialog, QApplication
from novel_studio.ui.loader import load_ui
from novel_studio.ui.dialogs import NewProjectDialog, AISettingsDialog
from novel_studio.ui.views.dashboard import DashboardView
from novel_studio.ui.views.idea import IdeaView
from novel_studio.ui.views.planning import PlanningView
from novel_studio.ui.views.sections import SectionsView, SECTIONS
from novel_studio.ui.views.ranges import RangesView
from novel_studio.ui.views.plots import PlotsView
from novel_studio.ui.views.manuscript import ManuscriptView
from novel_studio.ui.views.chat import ChatView
from novel_studio.ui.views.memory import MemoryView
from novel_studio.core.project import ProjectManager
from novel_studio.core.helpers import count_chars
from novel_studio.db.database import Database
from novel_studio.ai.lmstudio import LMStudioClient
from novel_studio.ai.engine import AIEngine, AIConfig
from novel_studio.ai.context import ContextManager
from novel_studio.services.project_service import ProjectService
from novel_studio.services.idea_service import IdeaService
from novel_studio.services.chat_service import ChatService
from novel_studio.services.backup_service import BackupService
from novel_studio.planning.master_planner import MasterPlanner
from novel_studio.plot.plot_manager import PlotManager
from novel_studio.manuscript.chapter_writer import ChapterWriter
from novel_studio.memory.memory_manager import MemoryManager
from novel_studio.continuity.checker import ContinuityChecker
from novel_studio.jobs.worker import Job

class MainWindow(QMainWindow):
    NAV=['대시보드','아이디어','마스터 기획','설정 자동 생성','스토리 구간','화별 플롯','원고','AI 채팅','기억 / 연속성']
    def __init__(self):
        super().__init__();self.setWindowTitle('Novel Studio v1.1');self.resize(1600,980)
        self.pool=QThreadPool(self);self.pool.setMaxThreadCount(1);self.busy=False;self.current=1
        self.pm=ProjectManager();self.ps=ProjectService(self.pm);self.db=None
        self.client=self.ai=self.context=self.master=self.plot=self.writer=self.memory=self.continuity=self.chat_service=self.idea_service=None
        self.owner=load_ui('main_window.ui');self.setCentralWidget(self.owner.centralWidget());self.setMenuBar(self.owner.menuBar());self.setStatusBar(self.owner.statusBar())
        self._find();self._pages();self._wire();self.nav.addItems(self.NAV);self._toggle_left(True);self._toggle_right(True)
        self.nav.setCurrentRow(0);self.statusBar().showMessage('새 작품을 만들거나 기존 작품을 열어주세요.')
    def _find(self):
        # main_window.ui is loaded into a temporary QMainWindow and its central widget
        # is then re-parented to this MainWindow. After re-parenting, widgets must be
        # searched from self (not the temporary owner), otherwise pageStack is None.
        f=self.findChild
        self.project_label=f(QWidget,'projectLabel');self.ai_status=f(QWidget,'aiStatusLabel');self.nav=f(QListWidget,'navigationList');self.stack=f(QStackedWidget,'pageStack')
        if self.stack is None or self.nav is None:
            raise RuntimeError('main_window.ui 위젯을 찾을 수 없습니다: pageStack/navigationList objectName을 확인하세요.')
        self.left=f(QWidget,'leftPanel');self.lh=f(QWidget,'leftHandle');self.right=f(QWidget,'rightPanel');self.rh=f(QWidget,'rightHandle')
        self.lc=f(QWidget,'leftCollapseButton');self.le=f(QWidget,'leftExpandButton');self.rc=f(QWidget,'rightCollapseButton');self.re=f(QWidget,'rightExpandButton')
        self.ai_btn=f(QWidget,'aiSettingsButton');self.save_btn=f(QWidget,'saveButton');self.write_btn=f(QWidget,'writeButton');self.revise_btn=f(QWidget,'reviseButton');self.check_btn=f(QWidget,'checkButton');self.count_label=f(QWidget,'charCountLabel')
        self.state_ch=f(QWidget,'stateChapterValue');self.state_time=f(QWidget,'stateTimeValue');self.state_loc=f(QWidget,'stateLocationValue');self.state_pro=f(QWidget,'stateProtagonistValue');self.state_cult=f(QWidget,'stateCultivationValue');self.state_mem=f(QWidget,'memoryPanel')
    def _pages(self):
        self.dashboard=DashboardView();self.idea=IdeaView({'generate':self.generate_idea,'use':self.use_idea});self.plan=PlanningView({'idea':self.generate_idea,'use':self.use_idea,'master':self.generate_master,'all_sections':self.generate_all_sections,'contract':self.generate_contract,'lock':self.lock_contract,'master_plot':self.generate_master_plot,'save_master':self.save_master,'save_plot':self.save_master_plot});self.sections=SectionsView({'generate':self.generate_section,'improve':self.improve_section,'load':self.load_section});self.ranges=RangesView({'generate':self.generate_ranges,'snapshot':self.generate_snapshot,'select':self.select_range});self.plots=PlotsView({'generate':self.generate_chapter_plans,'improve':self.improve_plot,'select':self.select_plot});self.manuscript=ManuscriptView({'load':self.load_chapter,'count':self.update_count,'save':self.save_current,'write':self.write_current,'revise':self.revise_current,'check':self.check_current,'chat':self.go_chat});self.chat=ChatView({'send':self.send_chat});self.memory_view=MemoryView({'summary':self.summarize_current,'check':self.check_current})
        self.views=[self.dashboard,self.idea,self.plan,self.sections,self.ranges,self.plots,self.manuscript,self.chat,self.memory_view]
        for v in self.views:self.stack.addWidget(v)
    def _wire(self):
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex);self.lc.clicked.connect(lambda:self._toggle_left(False));self.le.clicked.connect(lambda:self._toggle_left(True));self.rc.clicked.connect(lambda:self._toggle_right(False));self.re.clicked.connect(lambda:self._toggle_right(True));self.ai_btn.clicked.connect(self.open_ai_settings);self.save_btn.clicked.connect(self.save_current);self.write_btn.clicked.connect(self.write_current);self.revise_btn.clicked.connect(self.revise_current);self.check_btn.clicked.connect(self.check_current)
        acts={a.objectName():a for a in self.findChildren(QAction)}
        if 'actionNew' in acts:acts['actionNew'].triggered.connect(self.create_project)
        if 'actionOpen' in acts:acts['actionOpen'].triggered.connect(self.open_project)
        if 'actionBackup' in acts:acts['actionBackup'].triggered.connect(self.backup)
        if 'actionAISettings' in acts:acts['actionAISettings'].triggered.connect(self.open_ai_settings)
    def _toggle_left(self,v):self.left.setVisible(v);self.lh.setVisible(not v)
    def _toggle_right(self,v):self.right.setVisible(v);self.rh.setVisible(not v)
    def require_project(self):
        if not self.pm.active or not self.db:QMessageBox.warning(self,'프로젝트 없음','먼저 새 작품을 만들거나 열어주세요.');return False
        return True
    def _setup_ai(self):
        if not self.pm.active:return
        s=self.pm.settings;self.client=LMStudioClient(s.get('lmstudio_url','http://localhost:1234'),s.get('model',''));self.ai=AIEngine(self.client,AIConfig(float(s.get('temperature','0.72')),float(s.get('top_p','0.90')),int(s.get('max_tokens','9000'))));self.context=ContextManager(self.db,self.pm);self.master=MasterPlanner(self.db,self.ai,self.pm);self.plot=PlotManager(self.db,self.ai);self.writer=ChapterWriter(self.db,self.ai,self.context,self.pm);self.memory=MemoryManager(self.db,self.ai,self.context);self.continuity=ContinuityChecker(self.db,self.ai,self.context);self.chat_service=ChatService(self.db,self.ai,self.context);self.idea_service=IdeaService(self.db,self.ai,self.pm)
    def create_project(self):
        d=NewProjectDialog(self)
        if d.exec()!=d.DialogCode.Accepted:return
        root=Path(d.folder.text().strip())/d.title.text().strip()
        try:self.ps.create(root,d.title.text().strip(),d.genre.text().strip(),d.mood.text().strip(),d.total.value(),d.chars.value(),d.tol.value());self._opened();self.statusBar().showMessage('새 작품이 생성되었습니다.')
        except Exception as e:QMessageBox.critical(self,'생성 실패',str(e))
    def open_project(self):
        p=QFileDialog.getExistingDirectory(self,'Novel Studio 프로젝트 선택')
        if not p:return
        try:self.ps.open(p);self._opened();self.statusBar().showMessage('프로젝트를 열었습니다.')
        except Exception as e:QMessageBox.critical(self,'열기 실패',str(e))
    def _opened(self):
        self.db=self.ps.db;self._setup_ai();self.project_label.setText(self.pm.settings.get('title','프로젝트'));self._load_views();self.ai_status.setText('AI ● 연결 테스트 필요');self.load_chapter(1);self.apply_editor_style()
    def _load_views(self):
        idea=self.db.get_meta('idea','');self.idea.idea.setPlainText(idea);self.plan.ideaEdit.setPlainText(idea);self.plan.masterEdit.setPlainText(self.db.get_meta('master_plan',''));c=self.db.contract();self.plan.contractEdit.setPlainText(c['content'] if c else '');self.plan.masterPlotEdit.setPlainText(self.db.get_meta('master_plot',''));self.refresh_sections();self.refresh_ranges();self.refresh_plots();self.refresh_dashboard();self.refresh_state()
    def run_job(self,title,fn,on_result,on_error=None):
        if self.busy:return
        if not self.require_project():return
        self.busy=True;self.statusBar().showMessage(title);job=Job(title,fn);job.signals.result.connect(on_result);job.signals.error.connect(lambda e:self._job_error(e,on_error));job.signals.finished.connect(self._job_finished);self.pool.start(job)
    def _job_error(self,e,cb):QMessageBox.critical(self,'AI 작업 오류',e);cb and cb(e)
    def _job_finished(self):self.busy=False;self.statusBar().showMessage('준비 완료')
    def generate_idea(self):
        self._setup_ai();self.run_job('AI 아이디어 생성 중...',self.idea_service.generate,self._show_idea)
    def _show_idea(self,t):self.idea.idea.setPlainText(t);self.plan.ideaEdit.setPlainText(t)
    def use_idea(self):
        if not self.require_project():return
        t=self.idea.idea.toPlainText().strip();self.db.set_meta('idea',t);self.db.add_idea(t);self.db.use_idea(t);self.plan.ideaEdit.setPlainText(t);self.nav.setCurrentRow(2)
    def generate_master(self):
        idea=self.plan.ideaEdit.toPlainText().strip()
        if not idea:QMessageBox.warning(self,'아이디어 필요','아이디어를 입력하거나 AI로 생성하세요.');return
        self._setup_ai();self.run_job('AI 마스터 기획 생성 중...',lambda:self.master.create_master(idea),lambda t:self.plan.masterEdit.setPlainText(t))
    def save_master(self):
        if self.require_project():self.db.set_meta('master_plan',self.plan.masterEdit.toPlainText());self.db.set_meta('idea',self.plan.ideaEdit.toPlainText());self.statusBar().showMessage('마스터 기획 저장 완료')
    def generate_all_sections(self):
        master=self.plan.masterEdit.toPlainText().strip()
        if not master:QMessageBox.warning(self,'마스터 기획 필요','먼저 마스터 기획을 생성하세요.');return
        def work():
            for s in SECTIONS:self.master.generate_section(s,master,self.db.get_meta('section_'+s,''))
            return True
        self._setup_ai();self.run_job('전체 설정을 순서대로 생성 중...',work,lambda _:self.refresh_sections())
    def generate_section(self,s):
        if not self.plan.masterEdit.toPlainText().strip():QMessageBox.warning(self,'마스터 기획 필요','마스터 기획을 먼저 생성하세요.');return
        self._setup_ai();master=self.plan.masterEdit.toPlainText();existing=self.sections.edits[s].toPlainText();self.run_job(f'{s} AI 생성 중...',lambda:self.master.generate_section(s,master,existing),lambda t:self._set_section(s,t))
    def improve_section(self,s):self.generate_section(s)
    def _set_section(self,s,t):self.sections.edits[s].setPlainText(t);self.db.set_meta('section_'+s,t)
    def load_section(self,s):self.sections.edits[s].setPlainText(self.db.get_meta('section_'+s,'')) if self.db else None
    def refresh_sections(self):
        if self.db:
            for s in SECTIONS:self.sections.edits[s].setPlainText(self.db.get_meta('section_'+s,''))
    def generate_contract(self):
        self._setup_ai();master=self.plan.masterEdit.toPlainText();sections='\n\n'.join(f'[{s}]\n{self.db.get_meta("section_"+s,"")}' for s in SECTIONS);self.run_job('AI Contract 추출 중...',lambda:self.master.extract_contract(master,sections),lambda t:self.plan.contractEdit.setPlainText(t))
    def lock_contract(self):
        if self.require_project():self.db.save_contract(self.plan.contractEdit.toPlainText(),True);self.statusBar().showMessage('Plan Contract 승인/잠금 완료')
    def generate_master_plot(self):
        c=self.db.contract() if self.db else None
        if not c:QMessageBox.warning(self,'Contract 필요','Plan Contract를 먼저 생성하세요.');return
        self._setup_ai();target=int(self.pm.settings.get('target_chapters','500'));self.run_job('AI 전체 플롯 생성 중...',lambda:self.plot.generate_master_plot(self.plan.masterEdit.toPlainText(),c['content'],target),lambda t:self.plan.masterPlotEdit.setPlainText(t))
    def save_master_plot(self):
        if self.require_project():self.db.set_meta('master_plot',self.plan.masterPlotEdit.toPlainText());self.statusBar().showMessage('전체 플롯 저장 완료')
    def generate_ranges(self):
        if not self.require_project():return
        mp=self.db.get_meta('master_plot','');c=self.db.contract();
        if not mp or not c:QMessageBox.warning(self,'기획 부족','마스터 플롯과 Contract가 필요합니다.');return
        total=int(self.pm.settings.get('target_chapters','500'));size=self.ranges.size.value();self._setup_ai()
        def work():
            prev=''
            for s,e in self.plot.ranges(total,size):
                old=self.db.section(s,e)
                if old and old['status']=='생성완료':prev=old['snapshot'] or prev;continue
                text=self.plot.generate_story_section(mp,c['content'],s,e,prev);snap=self.memory.section_snapshot(s,e,text);old=self.db.section(s,e);self.db.upsert_section(s,e,'생성완료',old['objective'] if old else '',text,snap);prev=snap
            return True
        self.run_job('스토리 구간 생성 중...',work,lambda _:self.refresh_ranges())
    def refresh_ranges(self):
        self.ranges.list.clear()
        if self.db:
            for r in self.db.sections():self.ranges.list.addItem(f"{r['start_chapter']:03d}~{r['end_chapter']:03d}화  {r['status']}")
    def select_range(self,row):
        if not self.db or row<0:return
        r=self.db.sections()[row];self.ranges.detail.setPlainText((r['content'] or '')+'\n\n[상태 스냅샷]\n'+(r['snapshot'] or '없음'))
    def generate_snapshot(self):
        if not self.db:return
        row=self.ranges.list.currentRow();
        if row<0:return
        r=self.db.sections()[row];self._setup_ai();self.run_job('선택 구간 상태 생성 중...',lambda:self.memory.section_snapshot(r['start_chapter'],r['end_chapter'],r['content']),lambda t:self.db.upsert_section(r['start_chapter'],r['end_chapter'],r['status'],r['objective'],r['content'],t) or self.refresh_ranges())
    def generate_chapter_plans(self):
        if not self.require_project():return
        s,e=self.plots.start.value(),self.plots.end.value();sections=[r for r in self.db.sections() if r['start_chapter']<=e and r['end_chapter']>=s]
        if not sections:QMessageBox.warning(self,'스토리 구간 필요','먼저 해당 스토리 구간을 생성하세요.');return
        self._setup_ai();c=self.db.contract()['content'] if self.db.contract() else '';section_text='\n\n'.join(r['content'] for r in sections);ctx='\n'.join(r['snapshot'] for r in sections);self.run_job(f'{s}~{e}화 플롯 생성 중...',lambda:self.plot.generate_chapter_plans(section_text,c,ctx,s,e),lambda _:self.refresh_plots())
    def refresh_plots(self):
        self.plots.list.clear()
        if self.db:
            for p in self.db.chapter_plans():self.plots.list.addItem(f"{p['chapter_number']:03d}화  {p['title']}")
    def select_plot(self,row):
        if self.db and row>=0:self.plots.detail.setPlainText(self.db.chapter_plans()[row]['content'])
    def improve_plot(self):
        row=self.plots.list.currentRow();
        if row<0 or not self.db:return
        num=self.db.chapter_plans()[row]['chapter_number'];old=self.db.chapter_plan(num);self._setup_ai();prompt=f"다음 {num}화 플롯을 사건/설정/인물 일관성을 유지하며 개선하라. 동일 형식을 유지하라.\n{old['content']}";self.run_job(f'{num}화 플롯 개선 중...',lambda:self.ai.generate(prompt,temperature=.45,max_tokens=9000),lambda t:self.db.set_chapter_plan(num,old['title'],t,'초안') or self.refresh_plots())
    def load_chapter(self,n):
        if not self.db:return
        self.current=int(n);self.manuscript.editor.blockSignals(True);self.manuscript.editor.setPlainText(self.pm.load_chapter(self.current));self.manuscript.editor.blockSignals(False);c=self.db.chapter(self.current);self.manuscript.title.setText(c['title'] if c else f'{self.current}화');self.update_count();self.refresh_state();self.load_chat()
    def update_count(self):
        text=self.manuscript.editor.toPlainText();n=count_chars(text);ns=count_chars(text,True);target=int(self.pm.settings.get('chapter_chars','5000'));self.count_label.setText(f'현재 {n:,}자 / 목표 {target:,}자 / 공백 포함 {ns:,}자');self.manuscript.count.setText(f'{n:,}자 / 목표 {target:,}자')
    def save_current(self):
        if not self.require_project():return
        text=self.manuscript.editor.toPlainText();self.pm.save_chapter(self.current,text);self.db.set_chapter_meta(self.current,self.manuscript.title.text().strip() or f'{self.current}화','작성완료' if text.strip() else '미작성',count_chars(text),count_chars(text,True),int(self.pm.settings.get('chapter_chars','5000')));self.statusBar().showMessage(f'{self.current}화 저장 완료');self.refresh_dashboard()
    def write_current(self):
        if not self.require_project():return
        self._setup_ai();self.run_job(f'{self.current}화 AI 집필 중...',lambda:self.writer.write(self.current),self._apply_generated)
    def _apply_generated(self,text):
        target=int(self.pm.settings.get('chapter_chars','5000'));tol=int(self.pm.settings.get('tolerance','300'))
        if not(target-tol<=count_chars(text)<=target+tol):
            self.run_job('목표 글자 수에 맞춰 조정 중...',lambda:self.writer.adjust_length(text,target,tol),self._apply_to_editor);return
        self._apply_to_editor(text)
    def _apply_to_editor(self,text):self.manuscript.editor.setPlainText(text);self.update_count();self.nav.setCurrentRow(6)
    def revise_current(self):
        if not self.require_project():return
        text=self.manuscript.editor.toPlainText();self._setup_ai();self.run_job('AI 윤문 중...',lambda:self.ai.generate('다음 원고를 사건/설정은 유지한 채 한국 웹소설 문장으로 자연스럽게 윤문하라. 본문만 출력하라.\n\n'+text,temperature=.38,max_tokens=9000),self._apply_to_editor)
    def check_current(self):
        if not self.require_project():return
        text=self.manuscript.editor.toPlainText();self._setup_ai();self.run_job('AI 연속성 검증 중...',lambda:self.continuity.check(self.current,text),lambda t:self.memory_view.edit.setPlainText(t) or self.refresh_state())
    def summarize_current(self):
        if not self.require_project():return
        text=self.manuscript.editor.toPlainText();self._setup_ai();self.run_job('AI 기억 생성 중...',lambda:self.memory.summarize(self.current,text),lambda t:self.memory_view.edit.setPlainText(t) or self.refresh_state())
    def go_chat(self):self.nav.setCurrentRow(7);self.chat.input.setFocus();self.load_chat()
    def load_chat(self):
        if not self.db:return
        self.chat.log.clear()
        for r in self.db.chat_messages(self.current):self.chat.log.appendPlainText(("사용자: " if r['role']=='user' else "AI: ")+r['content']+"\n")
    def send_chat(self):
        msg=self.chat.input.toPlainText().strip()
        if not msg:return
        self.chat.input.clear();self._setup_ai();self.run_job('AI 응답 생성 중...',lambda:self.chat_service.send(self.current,msg),lambda t:self.load_chat())
    def backup(self):
        if not self.require_project():return
        try:p=BackupService(self.pm).backup();QMessageBox.information(self,'백업 완료',f'백업 위치:\n{p}')
        except Exception as e:QMessageBox.critical(self,'백업 실패',str(e))
    def open_ai_settings(self):
        if not self.pm.active:QMessageBox.information(self,'AI 설정','먼저 작품을 하나 만든 뒤 AI 설정을 열어주세요.');return
        d=AISettingsDialog(self.pm,self)
        if d.exec()==d.DialogCode.Accepted:self._setup_ai();self.apply_editor_style();self.ai_status.setText('AI ● 설정 저장됨')
    def apply_editor_style(self):
        if not self.pm.active:return
        s=self.pm.settings;font=QFont(s.get('editor_font_family','Malgun Gothic'),int(s.get('editor_font_size','18')));self.manuscript.editor.setFont(font);self.manuscript.editor.setStyleSheet(f"QPlainTextEdit {{ color: {s.get('editor_text_color','#222222')}; background-color: {s.get('editor_bg_color','#FFFDF5')}; }}")
    def refresh_dashboard(self):
        if not self.db:return
        rows=self.db.chapters();done=sum(1 for r in rows if r['status'] in ('작성완료','확정','윤문완료'));chars=sum(r['char_count'] for r in rows);total=int(self.pm.settings.get('target_chapters','500'));active=len([r for r in self.db.foreshadows() if r['status']!='회수']);issues=len(self.db.continuity())
        self.dashboard.set_text(f"작품: {self.pm.settings.get('title','')}\n\n현재 화: {self.current} / {total}\n진행률: {done}/{total} ({(done/total*100 if total else 0):.1f}%)\n총 글자수: {chars:,}자\n목표 화당: {int(self.pm.settings.get('chapter_chars','5000')):,}자\n활성 복선: {active}\n검증 기록: {issues}")
    def refresh_state(self):
        if not self.db:return
        self.state_ch.setText(str(self.current));tl=self.db.timelines();self.state_time.setText(tl[-1]['story_date'] if tl else '-');self.state_loc.setText(tl[-1]['location'] if tl else '-');
        chars=self.db.characters();self.state_pro.setText(chars[0]['name'] if chars else '-');self.state_cult.setText('-')
        snap=self.db.snapshot(f'state:{self.current-1}') or self.db.snapshot(f'chapter:{self.current-1}');self.state_mem.setPlainText(snap['content'][:4000] if snap else '현재 상태 정보가 아직 없습니다.')
