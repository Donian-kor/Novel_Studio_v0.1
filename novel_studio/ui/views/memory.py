from ._base import BaseView
from PySide6.QtWidgets import QPlainTextEdit,QPushButton
class MemoryView(BaseView):
    def __init__(self,w):
        super().__init__(w); self.mount('memory.ui'); self.w=w; self.edit=self.ui.findChild(QPlainTextEdit,'edit'); self.refreshMemoryBtn=self.ui.findChild(QPushButton,'refreshMemoryBtn'); self.auditBtn=self.ui.findChild(QPushButton,'auditBtn')
        # 이전에 저장한 기억/연속성 메모 복원
        try: self.edit.setPlainText(self.w.db.get_meta('memory_notes',''))
        except Exception: pass
    def save_detail(self):
        """편집된 기억/연속성 메모를 DB(meta)에 저장. 저장했으면 True."""
        t=self.edit.toPlainText()
        if not t.strip(): return False
        self.w.db.set_meta('memory_notes',t)
        return True
