from __future__ import annotations
from pathlib import Path
from PySide6.QtWidgets import QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QTabWidget,QMessageBox,QFileDialog,QDialog
from novel_studio.core.project import ProjectManager
from novel_studio.core.helpers import count_chars
from novel_studio.db.database import Database
from novel_studio.ai.lmstudio import LMStudioClient
from novel_studio.ai.engine import AIEngine
from novel_studio.ai.context import ContextManager
from novel_studio.ai.prompts import idea_prompt,chat_system
from novel_studio.services.section_service import SectionService
from novel_studio.services.plot_service import PlotService
from novel_studio.services.chapter_service import ChapterService
from novel_studio.services.memory_service import MemoryService
from novel_studio.services.continuity_service import ContinuityService
from novel_studio.services.backup_service import BackupService
from novel_studio.ui.dialogs import NewProjectDialog,AISettingsDialog
from novel_studio.ui.views.planning import PlanningView
from novel_studio.ui.views.sections import SectionsView,SECTIONS
from novel_studio.ui.views.ranges import RangesView
from novel_studio.ui.views.plots import PlotsView
from novel_studio.ui.views.manuscript import ManuscriptView
from novel_studio.ui.views.chat import ChatView
from novel_studio.ui.views.memory import MemoryView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle('Novel Studio v0.4'); self.resize(1500,950)
        self.pm=ProjectManager(); self.db=None; self.engine=None; self.context=None; self.current=1
        self._build_menu(); self.setCentralWidget(self._build_ui()); self.statusBar().showMessage('프로젝트를 열어주세요.')
    def _build_menu(self):
        menu=self.menuBar().addMenu('프로젝트'); menu.addAction('새 작품',self.create_project); menu.addAction('작품 열기',self.open_project); menu.addAction('프로젝트 백업',self.backup)
    def _build_ui(self):
        root=QWidget(); l=QVBoxLayout(root); top=QHBoxLayout(); self.project_label=QLabel('작품: 없음'); self.ai_label=QLabel('AI ● 미설정'); s=QPushButton('AI 설정'); s.clicked.connect(self.open_ai_settings); top.addWidget(self.project_label); top.addStretch(); top.addWidget(self.ai_label); top.addWidget(s); l.addLayout(top)
        cb={'idea':self.generate_idea,'use':self.use_idea,'master':self.generate_master,'contract':self.generate_contract,'save':self.save_master}; self.planning=PlanningView(cb); self.sections_view=SectionsView({'generate':self.generate_section,'improve':self.improve_section}); self.ranges_view=RangesView({'generate':self.generate_all_ranges,'select':self.range_selected}); self.plots_view=PlotsView({'generate':self.generate_chapter_plans,'select':self.plot_selected}); self.manuscript=ManuscriptView({'load':self.load_chapter,'count':self.update_count,'save':self.save_current,'write':self.write_current,'revise':self.revise_current,'check':self.check_current}); self.chat_view=ChatView({'send':self.send_chat}); self.memory_view=MemoryView({'check':self.check_current})
        self.tabs=QTabWidget(); self.tabs.addTab(self.build_dashboard(),'대시보드'); self.tabs.addTab(self.planning,'AI 기획'); self.tabs.addTab(self.sections_view,'설정'); self.tabs.addTab(self.ranges_view,'스토리 구간'); self.tabs.addTab(self.plots_view,'화별 플롯'); self.tabs.addTab(self.manuscript,'원고'); self.tabs.addTab(self.chat_view,'AI 채팅'); self.tabs.addTab(self.memory_view,'기억/연속성'); l.addWidget(self.tabs,1); return root
    def build_dashboard(self): self.dashboard=QLabel('프로젝트를 열어주세요.'); self.dashboard.setAlignment(Qt.AlignTop|Qt.AlignLeft) if False else None; w=QWidget(); ll=QVBoxLayout(w); ll.addWidget(self.dashboard); return w
    def require_project(self):
        if not self.pm.active or not self.db: QMessageBox.warning(self,'프로젝트 없음','먼저 프로젝트를 열거나 새로 만들어주세요.'); return False
        if not self.engine: self.build_ai()
        return True
    def create_project(self):
        d=NewProjectDialog(self); 
        if d.exec()!=QDialog.Accepted:return
        self.pm.create(Path(d.folder.text()),d.title.text(),d.genre.text(),d.total.value(),d.chars.value(),d.tol.value()); self.db=Database(self.pm.paths.db); self.refresh_project()
    def open_project(self):
        p=QFileDialog.getExistingDirectory(self,'프로젝트 폴더');
        if not p:return
        try:self.pm.open(Path(p)); self.db=Database(self.pm.paths.db); self.refresh_project()
        except Exception as e:QMessageBox.critical(self,'오류',str(e))
    def refresh_project(self):
        self.project_label.setText('작품: '+self.pm.settings.get('title',self.pm.paths.root.name)); self.build_ai(); self.planning.idea.setPlainText(self.db.get_meta('idea','')); self.planning.master.setPlainText(self.db.get_meta('master_plan','')); self.refresh_ranges(); self.refresh_plots(); self.load_chapter(1); self.refresh_dashboard()
    def build_ai(self):
        client=LMStudioClient(self.pm.settings.get('lmstudio_url','http://localhost:1234'),self.pm.settings.get('model','')); self.engine=AIEngine(client); self.context=ContextManager(self.db,self.pm); self.sections=SectionService(self.db,self.engine,self.pm); self.plots=PlotService(self.db,self.engine,self.context); self.chapters=ChapterService(self.db,self.engine,self.context,self.pm); self.memory_service=MemoryService(self.db,self.engine,self.context); self.continuity=ContinuityService(self.db,self.engine,self.context,self.pm); self.backups=BackupService(self.pm); self.ai_label.setText('AI ● '+(self.pm.settings.get('model') or '모델 미지정'))
    def open_ai_settings(self):
        settings=self.pm.settings if self.pm.active else {'lmstudio_url':'http://localhost:1234','model':''}; d=AISettingsDialog(settings,self)
        if d.exec()!=QDialog.Accepted:return
        if self.pm.active: self.pm.settings.update(d.values()); self.pm.save_settings(); self.build_ai()
    def generate_idea(self):
        if not self.require_project():return
        recent='\n'.join(r['content'] for r in self.db.recent_ideas()); out=self.engine.generate(idea_prompt(f"장르={self.pm.settings.get('genre','')}",recent),temperature=0.95,max_tokens=300); self.planning.idea.setPlainText(out); self.db.add_idea(out); self.db.set_meta('idea',out)
    def use_idea(self):
        if self.require_project(): self.db.set_meta('idea',self.planning.idea.toPlainText())
    def generate_master(self):
        if not self.require_project():return
        meta={'target_chapters':int(self.pm.settings.get('target_chapters',500)),'chapter_chars':int(self.pm.settings.get('chapter_chars',5000)),'genre':self.pm.settings.get('genre','')}; out=self.sections.master_plan(self.planning.idea.toPlainText(),meta); self.planning.master.setPlainText(out)
    def save_master(self):
        if self.require_project(): self.db.set_meta('master_plan',self.planning.master.toPlainText())
    def generate_contract(self):
        if not self.require_project():return
        ctx={s:self.sections_view.edits[s].toPlainText() for s in SECTIONS}; out=self.sections.make_contract(self.planning.master.toPlainText(),ctx,int(self.pm.settings.get('target_chapters',500))); self.chat_view.log.appendPlainText('[AI Contract]\n'+out)
    def generate_section(self,sec):
        if not self.require_project():return
        out=self.sections.generate_section(sec,self.planning.master.toPlainText()); self.sections_view.edits[sec].setPlainText(out)
    def improve_section(self,sec):
        if not self.require_project():return
        out=self.sections.generate_section(sec,self.planning.master.toPlainText()+'\n현재 설정:\n'+self.sections_view.edits[sec].toPlainText()); self.sections_view.edits[sec].setPlainText(out)
    def generate_all_ranges(self):
        if not self.require_project():return
        total=int(self.pm.settings.get('target_chapters',500)); size=self.ranges_view.size.value(); master=self.planning.master.toPlainText(); contract=self.db.contract()['content'] if self.db.contract() else ''
        for s,e in self.plots.split_ranges(total,size): self.plots.make_story_section(master,contract,s,e)
        self.refresh_ranges()
    def refresh_ranges(self):
        self.ranges_view.list.clear();
        if self.db:
            for r in self.db.sections(): self.ranges_view.list.addItem(f"{r['start_chapter']:03d}~{r['end_chapter']:03d}  {r['status']}")
    def range_selected(self,row):
        if row<0 or not self.db:return
        r=self.db.sections()[row]; self.ranges_view.detail.setPlainText(r['content']+'\n\n[스냅샷]\n'+(r['snapshot'] or ''))
    def generate_chapter_plans(self):
        if not self.require_project():return
        s,e=self.plots_view.start.value(),self.plots_view.end.value(); sec='\n'.join(r['content'] for r in self.db.sections() if int(r['start_chapter'])<=e and int(r['end_chapter'])>=s); ctx=self.planning.master.toPlainText()+'\n'+sec+'\n'+(self.db.contract()['content'] if self.db.contract() else ''); self.plots.make_chapter_plans(s,e,ctx); self.refresh_plots()
    def refresh_plots(self):
        self.plots_view.list.clear();
        if self.db:
            for n in range(1,int(self.pm.settings.get('target_chapters',500))+1):
                p=self.db.chapter_plan(n)
                if p:self.plots_view.list.addItem(f"{n:03d}  {p['title']}")
    def plot_selected(self,row):
        if row<0 or not self.db:return
        n=int(self.plots_view.list.item(row).text().split()[0]); p=self.db.chapter_plan(n); self.plots_view.detail.setPlainText(p['content'])
    def load_chapter(self,n):
        if not self.pm.active:return
        self.current=int(n); self.manuscript.chapter.blockSignals(True); self.manuscript.chapter.setValue(self.current); self.manuscript.chapter.blockSignals(False); self.manuscript.editor.blockSignals(True); self.manuscript.editor.setPlainText(self.pm.load_chapter(self.current)); self.manuscript.editor.blockSignals(False); ch=self.db.chapter(self.current) if self.db else None; self.manuscript.title.setText(ch['title'] if ch else ''); self.update_count(); self.refresh_memory()
    def save_current(self):
        if not self.require_project():return
        text=self.manuscript.editor.toPlainText(); target=int(self.pm.settings.get('chapter_chars',5000)); self.pm.save_chapter(self.current,text); self.db.set_chapter_meta(self.current,self.manuscript.title.text() or f'{self.current}화','집필완료',count_chars(text),target); self.refresh_dashboard()
    def update_count(self):
        n=count_chars(self.manuscript.editor.toPlainText()); target=int(self.pm.settings.get('chapter_chars',5000)) if self.pm.active else 0; self.manuscript.count.setText(f'현재 {n:,}자 / 목표 {target:,}자 / 차이 {n-target:+,}자')
    def write_current(self):
        if not self.require_project():return
        out=self.chapters.write(self.current,int(self.pm.settings.get('chapter_chars',5000))); self.manuscript.editor.setPlainText(out); self.chat_view.log.appendPlainText(f'[AI 집필 {self.current}화]\n{out}')
    def revise_current(self):
        if not self.require_project():return
        out=self.engine.generate(f'''설정과 플롯을 유지하면서 다음 원고를 자연스럽게 윤문하라. 목표 분량은 {self.pm.settings.get('chapter_chars',5000)}자다.\n\n{self.manuscript.editor.toPlainText()}''',system='한국 웹소설 전문 편집자다.',temperature=0.4,max_tokens=9000); self.manuscript.editor.setPlainText(out)
    def check_current(self):
        if not self.require_project():return
        out=self.continuity.check(self.current,self.manuscript.editor.toPlainText()); self.memory_view.edit.setPlainText(out); self.chat_view.log.appendPlainText('[연속성 검사]\n'+out)
    def send_chat(self):
        if not self.require_project():return
        user=self.chat_view.input.toPlainText().strip();
        if not user:return
        ctx=self.context.build(self.current); out=self.engine.generate(user,system=chat_system(ctx),temperature=float(self.pm.settings.get('temperature',0.72)),max_tokens=int(self.pm.settings.get('max_tokens',7000))); self.chat_view.log.appendPlainText('사용자:\n'+user+'\n\nAI:\n'+out+'\n'); self.chat_view.input.clear()
    def refresh_memory(self):
        if not self.db:return
        s=self.db.snapshot(f'chapter:{max(1,self.current-1)}'); self.memory_view.edit.setPlainText(s['content'] if s else '현재 화 관련 기억이 없습니다.')
    def refresh_dashboard(self):
        if not self.db:return
        rows=self.db.chapters(); done=sum(1 for r in rows if r['status']=='집필완료'); total=int(self.pm.settings.get('target_chapters',500)); chars=sum(int(r['word_count']) for r in rows); self.dashboard.setText(f"작품: {self.pm.settings.get('title','')}\n목표: {total}화\n집필 완료: {done}화\n총 글자수: {chars:,}자\n화당 목표: {int(self.pm.settings.get('chapter_chars',5000)):,}자")
    def backup(self):
        if not self.require_project():return
        try: dest=self.backups.backup(); QMessageBox.information(self,'백업 완료',str(dest))
        except Exception as e: QMessageBox.critical(self,'백업 실패',str(e))
