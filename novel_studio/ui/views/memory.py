from PySide6.QtWidgets import QWidget,QVBoxLayout,QPlainTextEdit,QPushButton
class MemoryView(QWidget):
    def __init__(self,callbacks,parent=None):
        super().__init__(parent); l=QVBoxLayout(self); self.edit=QPlainTextEdit(); self.edit.setReadOnly(True); l.addWidget(self.edit); b=QPushButton('현재 화 기억/연속성 검사'); b.clicked.connect(callbacks['check']); l.addWidget(b)
