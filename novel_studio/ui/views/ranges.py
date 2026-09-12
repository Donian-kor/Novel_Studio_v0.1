from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QSpinBox,QPushButton,QLabel,QListWidget,QPlainTextEdit,QSplitter
class RangesView(QWidget):
    def __init__(self,callbacks,parent=None):
        super().__init__(parent); l=QVBoxLayout(self); r=QHBoxLayout(); self.size=QSpinBox(); self.size.setRange(1,50); self.size.setValue(5); r.addWidget(QLabel('스토리 구간 크기')); r.addWidget(self.size); b=QPushButton('전체 구간 생성'); b.clicked.connect(callbacks['generate']); r.addWidget(b); l.addLayout(r)
        self.list=QListWidget(); self.list.currentRowChanged.connect(callbacks['select']); self.detail=QPlainTextEdit(); self.detail.setReadOnly(True); s=QSplitter(); s.addWidget(self.list); s.addWidget(self.detail); l.addWidget(s)
