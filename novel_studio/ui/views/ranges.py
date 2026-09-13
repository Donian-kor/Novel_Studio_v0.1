from ._base import BaseView
from PySide6.QtWidgets import QListWidget,QPlainTextEdit,QPushButton
class RangesView(BaseView):
    def __init__(self,w): super().__init__(w); self.mount('ranges.ui'); self.w=w; self.list=self.ui.findChild(QListWidget,'list'); self.detail=self.ui.findChild(QPlainTextEdit,'detail'); self.generateBtn=self.ui.findChild(QPushButton,'generateBtn'); self.snapshotBtn=self.ui.findChild(QPushButton,'snapshotBtn'); self.saveBtn=self.ui.findChild(QPushButton,'saveBtn'); self.list.currentRowChanged.connect(self.show_selected); self.saveBtn.setEnabled(False) if self.saveBtn else None; self.detail.textChanged.connect(self._on_edited)
    def refresh(self):
        current = self.list.currentRow() if self.list else -1
        self.list.blockSignals(True)
        self._rows_cache = self.w.db.sections()
        self.list.clear()
        self.list.insertItems(0, [f"스토리 구간 {r['start_chapter']:03d}~{r['end_chapter']:03d}화 | {r['status']}" for r in self._rows_cache])
        if self.list.count(): self.list.setCurrentRow(min(max(current,0), self.list.count()-1))
        else: self.detail.clear()
        self.list.blockSignals(False)
        if self.saveBtn: self.saveBtn.setEnabled(self.selected() is not None)
    def selected(self):
        cache = getattr(self, '_rows_cache', None)
        if not cache: return None
        i=self.list.currentRow(); return cache[i] if 0<=i<len(cache) else None
    def show_selected(self):
        r=self.selected(); self.detail.setPlainText((r['content'] if r else '')+'\n\n[상태 스냅샷]\n'+(r['snapshot'] if r else ''))
        if self.saveBtn: self.saveBtn.setEnabled(r is not None)

    def _on_edited(self):
        if self.saveBtn: self.saveBtn.setEnabled(self.selected() is not None)
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
