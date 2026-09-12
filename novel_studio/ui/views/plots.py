from ._base import BaseView
from PySide6.QtWidgets import QSpinBox,QListWidget,QPlainTextEdit,QPushButton
class PlotsView(BaseView):
    def __init__(self,w): super().__init__(w); self.mount('plots.ui'); self.w=w; self.start=self.ui.findChild(QSpinBox,'start'); self.end=self.ui.findChild(QSpinBox,'end'); self.list=self.ui.findChild(QListWidget,'list'); self.detail=self.ui.findChild(QPlainTextEdit,'detail'); self.generateBtn=self.ui.findChild(QPushButton,'generateBtn'); self.allBtn=self.ui.findChild(QPushButton,'allBtn'); self.improveBtn=self.ui.findChild(QPushButton,'improveBtn'); self.list.currentRowChanged.connect(self.show_selected)
    def refresh(self): self.list.clear(); [self.list.addItem(f"{p['chapter_number']:03d}화 {p['title']} | {p['status']}") for p in self.w.db.chapter_plans()]
    def selected(self):
        rows=self.w.db.chapter_plans(); i=self.list.currentRow(); return rows[i] if 0<=i<len(rows) else None
    def show_selected(self):
        p=self.selected(); self.detail.setPlainText(p['content'] if p else '')
