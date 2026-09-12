from PySide6.QtWidgets import QWidget,QVBoxLayout,QPlainTextEdit,QPushButton,QTabWidget
SECTIONS=['세계관','인물','세력','장소','수련체계','시간축','복선','핵심 사건']
class SectionsView(QWidget):
    def __init__(self,callbacks,parent=None):
        super().__init__(parent); l=QVBoxLayout(self); self.tabs=QTabWidget(); self.edits={}
        for sec in SECTIONS:
            p=QWidget(); pl=QVBoxLayout(p); e=QPlainTextEdit(); self.edits[sec]=e; pl.addWidget(e)
            b=QPushButton(f'AI {sec} 생성'); b.clicked.connect(lambda _,s=sec: callbacks['generate'](s)); pl.addWidget(b)
            b=QPushButton(f'AI {sec} 개선'); b.clicked.connect(lambda _,s=sec: callbacks['improve'](s)); pl.addWidget(b); self.tabs.addTab(p,sec)
        l.addWidget(self.tabs)
