from PySide6.QtWidgets import QListWidget, QPlainTextEdit, QPushButton
from ._base import BaseView


class RangesView(BaseView):
    def __init__(self, w):
        super().__init__(w)
        self.mount('ranges.ui')
        self.w = w
        self.list = self.ui.findChild(QListWidget, 'list')
        self.detail = self.ui.findChild(QPlainTextEdit, 'detail')
        self.generateBtn = self.ui.findChild(QPushButton, 'generateBtn')
        self.regenerateSelectedBtn = self.ui.findChild(QPushButton, 'regenerateSelectedBtn')
        self.regenerateAllBtn = self.ui.findChild(QPushButton, 'regenerateAllBtn')
        self.snapshotBtn = self.ui.findChild(QPushButton, 'snapshotBtn')
        self.saveBtn = self.ui.findChild(QPushButton, 'saveBtn')

        if self.list:
            self.list.currentRowChanged.connect(self.show_selected)
        if self.regenerateSelectedBtn:
            self.regenerateSelectedBtn.clicked.connect(self.w.regenerate_selected_section)
        if self.regenerateAllBtn:
            self.regenerateAllBtn.clicked.connect(self.w.regenerate_all_sections)
        if self.saveBtn:
            self.saveBtn.setEnabled(False)
        if self.detail:
            self.detail.textChanged.connect(self._on_edited)

    def refresh(self):
        if not self.list:
            return
        current = self.list.currentRow()
        self.list.blockSignals(True)
        self._rows_cache = self.w.db.sections()
        self.list.clear()
        self.list.insertItems(
            0,
            [
                f"스토리 구간 {r['start_chapter']:03d}~{r['end_chapter']:03d}화 | {r['status']}"
                for r in self._rows_cache
            ],
        )
        if self.list.count():
            self.list.setCurrentRow(min(max(current, 0), self.list.count() - 1))
        elif self.detail:
            self.detail.clear()
        self.list.blockSignals(False)
        self.show_selected()

    def selected(self):
        cache = getattr(self, '_rows_cache', None)
        if not cache or not self.list:
            return None
        i = self.list.currentRow()
        return cache[i] if 0 <= i < len(cache) else None

    def show_selected(self, *_args):
        r = self.selected()
        if self.detail:
            self.detail.blockSignals(True)
            self.detail.setPlainText(
                (r['content'] if r else '')
                + '\n\n[상태 스냅샷]\n'
                + (r['snapshot'] if r else '')
            )
            self.detail.blockSignals(False)
        if self.saveBtn:
            self.saveBtn.setEnabled(r is not None)

    def _on_edited(self):
        if self.saveBtn:
            self.saveBtn.setEnabled(self.selected() is not None)

    def save_detail(self):
        """편집된 구간 요약/상태 스냅샷을 DB에 저장. 저장했으면 True."""
        r = self.selected()
        if not r or not self.detail:
            return False
        text = self.detail.toPlainText()
        marker = '\n\n[상태 스냅샷]\n'
        if marker in text:
            content, snap = text.split(marker, 1)
        else:
            content, snap = text, (r['snapshot'] or '')
        self.w.db.save_section(
            r['start_chapter'], r['end_chapter'], r['status'], content, snap
        )
        self.refresh()
        return True
