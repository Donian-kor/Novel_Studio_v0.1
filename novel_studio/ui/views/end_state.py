from __future__ import annotations

from ._base import BaseView
from PySide6.QtWidgets import QListWidget, QPlainTextEdit, QPushButton, QSplitter


class EndStateView(BaseView):
    """연속성 기록을 확인하고 필요할 때만 AI로 생성한다."""
    def __init__(self, w):
        super().__init__(w)
        self.mount('end_state.ui')
        self.w = w
        self.chapterList = self.ui.findChild(QListWidget, 'chapterList')
        self.edit = self.ui.findChild(QPlainTextEdit, 'edit')
        self.generateBtn = self.ui.findChild(QPushButton, 'generateBtn')
        self.auditBtn = self.ui.findChild(QPushButton, 'auditBtn')
        self.saveBtn = self.ui.findChild(QPushButton, 'saveBtn')
        self.stateSplitter = self.ui.findChild(QSplitter, 'stateSplitter')
        if self.stateSplitter:
            self.stateSplitter.setSizes([280, 1100])
        self.chapterList.currentRowChanged.connect(self.show_selected)
        self.saveBtn.clicked.connect(self.save_selected)
        self._rows = []
        self._loading = False
        self._status_rows = {}

    def refresh(self):
        keep = self.chapterList.currentRow()
        self._rows = self.w.db.chapter_states(limit=None)
        by_chapter = {int(r['chapter_number']): r for r in self._rows}
        chapters = self.w.db.chapters()
        self.chapterList.blockSignals(True); self.chapterList.clear()
        for c in chapters:
            n = int(c['number']); row = by_chapter.get(n)
            status = (row['status'] if row else '미생성') or '미생성'
            self.chapterList.addItem(f"{n:03d}화 | {status}")
        if self.chapterList.count():
            self.chapterList.setCurrentRow(max(0, min(keep if keep >= 0 else 0, self.chapterList.count()-1)))
        self.chapterList.blockSignals(False)
        self.show_selected()

    def selected_chapter(self):
        i = self.chapterList.currentRow()
        return i + 1 if i >= 0 else None

    def show_selected(self):
        n = self.selected_chapter()
        self._loading = True
        self.edit.blockSignals(True)
        row = self.w.db.chapter_state(n) if n else None
        self.edit.setPlainText((row['state'] if row else '') or '')
        self.edit.blockSignals(False)
        self._loading = False
        self.saveBtn.setEnabled(row is not None)

    def save_selected(self):
        n = self.selected_chapter()
        if not n: return False
        row = self.w.db.chapter_state(n)
        if not row: return False
        text = self.edit.toPlainText().strip()
        self.w.db.save_chapter_state(n, '', text, row['source_hash'] or '', row['status'] or '완료')
        self.refresh()
        return True
