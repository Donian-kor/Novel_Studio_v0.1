from ._base import BaseView
from PySide6.QtWidgets import QPlainTextEdit
class MemoryView(BaseView):
    def __init__(self,w): super().__init__(w); self.mount('memory.ui'); self.w=w; self.edit=self.ui.findChild(QPlainTextEdit,'edit')
