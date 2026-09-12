from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QSpinBox,QLineEdit,QLabel,QPlainTextEdit,QPushButton
class ManuscriptView(QWidget):
    def __init__(self,callbacks,parent=None):
        super().__init__(parent); l=QVBoxLayout(self); r=QHBoxLayout(); self.chapter=QSpinBox(); self.chapter.setRange(1,5000); self.chapter.valueChanged.connect(callbacks['load']); self.title=QLineEdit(); r.addWidget(QLabel('화')); r.addWidget(self.chapter); r.addWidget(self.title,1); l.addLayout(r); self.editor=QPlainTextEdit(); self.editor.textChanged.connect(callbacks['count']); l.addWidget(self.editor,1); self.count=QLabel(); l.addWidget(self.count); r=QHBoxLayout()
        for txt,key in [('저장','save'),('AI 집필','write'),('AI 윤문','revise'),('연속성 검사','check')]: b=QPushButton(txt); b.clicked.connect(callbacks[key]); r.addWidget(b)
        l.addLayout(r)
