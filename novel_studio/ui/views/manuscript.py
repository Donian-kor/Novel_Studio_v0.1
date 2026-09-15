from ._base import BaseView
from PySide6.QtWidgets import QLineEdit,QPushButton,QListWidget,QPlainTextEdit,QLabel,QSplitter
from PySide6.QtCore import QSettings
class ManuscriptView(BaseView):
    def __init__(self,w):
        super().__init__(w); self.mount('manuscript.ui'); self.w=w
        self.titleEdit=self.ui.findChild(QLineEdit,'titleEdit'); self.writeBtn=self.ui.findChild(QPushButton,'writeBtn'); self.chatBtn=self.ui.findChild(QPushButton,'chatBtn'); self.reviseBtn=self.ui.findChild(QPushButton,'reviseBtn'); self.checkBtn=self.ui.findChild(QPushButton,'checkBtn'); self.saveBtn=self.ui.findChild(QPushButton,'saveBtn'); self.chapterList=self.ui.findChild(QListWidget,'chapterList'); self.editor=self.ui.findChild(QPlainTextEdit,'editor'); self.countLabel=self.ui.findChild(QLabel,'countLabel')
        self.splitter=self.ui.findChild(QSplitter,'manuscriptSplitter')
        if self.splitter:self.splitter.setChildrenCollapsible(False); self.splitter.setHandleWidth(7); self.splitter.setSizes([380,1020])

    def refresh(self) -> None:
        """현재 선택된 화의 원고 본문과 제목을 DB 기준으로 다시 채운다."""
        w=self.w
        self.editor.blockSignals(True)
        active=getattr(w,'_active_manuscript_job',None)
        if active and int(active.get('chapter',-1))==int(w.current):
            self.editor.setPlainText(''.join(active.get('buffer',[])))
        else:
            self.editor.setPlainText(w.pm.load_chapter(int(w.current)))
        self.editor.blockSignals(False)
        r=w.db.chapter(int(w.current))
        self.titleEdit.setText(r['title'] if r else f'{int(w.current)}화')
        w.update_count()
