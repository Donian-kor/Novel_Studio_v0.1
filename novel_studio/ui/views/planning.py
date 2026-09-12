from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPlainTextEdit,QPushButton
class PlanningView(QWidget):
    def __init__(self,callbacks,parent=None):
        super().__init__(parent); l=QVBoxLayout(self)
        r=QHBoxLayout(); self.idea=QPlainTextEdit(); self.idea.setPlaceholderText('아이디어 3줄'); self.idea.setMaximumHeight(110); r.addWidget(self.idea,1)
        for txt,key in [('AI 아이디어 생성','idea'),('이 아이디어 사용','use')]: b=QPushButton(txt); b.clicked.connect(callbacks[key]); r.addWidget(b)
        l.addLayout(r); self.master=QPlainTextEdit(); l.addWidget(self.master,2)
        r=QHBoxLayout()
        for txt,key in [('AI 마스터 기획','master'),('AI Contract 추출','contract'),('저장','save')]: b=QPushButton(txt); b.clicked.connect(callbacks[key]); r.addWidget(b)
        l.addLayout(r)
