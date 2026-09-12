from ._base import BaseView
from PySide6.QtWidgets import QListWidget,QPlainTextEdit,QPushButton
class RangesView(BaseView):
    def __init__(self,w): super().__init__(w); self.mount('ranges.ui'); self.w=w; self.list=self.ui.findChild(QListWidget,'list'); self.detail=self.ui.findChild(QPlainTextEdit,'detail'); self.generateBtn=self.ui.findChild(QPushButton,'generateBtn'); self.snapshotBtn=self.ui.findChild(QPushButton,'snapshotBtn'); self.list.currentRowChanged.connect(self.show_selected)
    def refresh(self): self.list.clear(); [self.list.addItem(f"스토리 구간 {r['start_chapter']:03d}~{r['end_chapter']:03d}화 | {r['status']}") for r in self.w.db.sections()]
    def selected(self):
        rows=self.w.db.sections(); i=self.list.currentRow(); return rows[i] if 0<=i<len(rows) else None
    def show_selected(self):
        r=self.selected(); self.detail.setPlainText((r['content'] if r else '')+'\n\n[상태 스냅샷]\n'+(r['snapshot'] if r else ''))
    def save_detail(self):
        """편집된 구간 요약/상태 스냅샷을 DB에 저장. 저장했으면 True."""
        r=self.selected()
        if not r: return False
        text=self.detail.toPlainText()
        marker='\n\n[상태 스냅샷]\n'
        if marker in text:
            content,snap=text.split(marker,1)
        else:
            content,snap=text,(r['snapshot'] or '')
        self.w.db.save_section(r['start_chapter'],r['end_chapter'],r['status'],content,snap)
        return True
