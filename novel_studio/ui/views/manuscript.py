from ._base import BaseView
from PySide6.QtWidgets import QLineEdit,QPushButton,QListWidget,QPlainTextEdit,QLabel,QSplitter
from PySide6.QtCore import QSettings
class ManuscriptView(BaseView):
    def __init__(self,w):
        super().__init__(w); self.mount('manuscript.ui'); self.w=w
        self.titleEdit=self.ui.findChild(QLineEdit,'titleEdit'); self.writeBtn=self.ui.findChild(QPushButton,'writeBtn'); self.chatBtn=self.ui.findChild(QPushButton,'chatBtn'); self.reviseBtn=self.ui.findChild(QPushButton,'reviseBtn'); self.checkBtn=self.ui.findChild(QPushButton,'checkBtn'); self.saveBtn=self.ui.findChild(QPushButton,'saveBtn'); self.chapterList=self.ui.findChild(QListWidget,'chapterList'); self.editor=self.ui.findChild(QPlainTextEdit,'editor'); self.countLabel=self.ui.findChild(QLabel,'countLabel')
        self.splitter=self.ui.findChild(QSplitter,'manuscriptSplitter')
        if self.splitter:self.splitter.setChildrenCollapsible(False); self.splitter.setHandleWidth(7); self.splitter.setSizes([380,1020])
