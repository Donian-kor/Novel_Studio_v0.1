from PySide6.QtWidgets import QWidget,QVBoxLayout,QPlainTextEdit,QPushButton
class ChatView(QWidget):
    def __init__(self,callbacks,parent=None):
        super().__init__(parent); l=QVBoxLayout(self); self.log=QPlainTextEdit(); self.log.setReadOnly(True); self.input=QPlainTextEdit(); self.input.setPlaceholderText('예: 1화 써줘.'); self.input.setMaximumHeight(110); b=QPushButton('전송'); b.clicked.connect(callbacks['send']); l.addWidget(self.log,1); l.addWidget(self.input); l.addWidget(b)
