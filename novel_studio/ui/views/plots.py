from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QSpinBox,QPushButton,QLabel,QListWidget,QPlainTextEdit,QSplitter
class PlotsView(QWidget):
    def __init__(self,callbacks,parent=None):
        super().__init__(parent); l=QVBoxLayout(self); r=QHBoxLayout(); self.start=QSpinBox(); self.start.setRange(1,5000); self.end=QSpinBox(); self.end.setRange(1,5000); self.start.setValue(1); self.end.setValue(5); r.addWidget(QLabel('화')); r.addWidget(self.start); r.addWidget(QLabel('~')); r.addWidget(self.end); b=QPushButton('AI 화별 플롯 생성'); b.clicked.connect(callbacks['generate']); r.addWidget(b); l.addLayout(r)
        self.list=QListWidget(); self.list.currentRowChanged.connect(callbacks['select']); self.detail=QPlainTextEdit(); self.detail.setReadOnly(True); s=QSplitter(); s.addWidget(self.list); s.addWidget(self.detail); l.addWidget(s)
