from ._base import BaseView
from PySide6.QtWidgets import QPlainTextEdit,QPushButton
class IdeaView(BaseView):
    def __init__(self,w): super().__init__(w); self.mount('idea.ui'); self.w=w; self.ideaEdit=self.ui.findChild(QPlainTextEdit,'ideaEdit'); self.generateBtn=self.ui.findChild(QPushButton,'generateBtn'); self.useBtn=self.ui.findChild(QPushButton,'useBtn')
    def load(self): self.ideaEdit.setPlainText(self.w.db.get_meta('idea',''))
