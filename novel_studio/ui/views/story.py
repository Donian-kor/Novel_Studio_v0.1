from __future__ import annotations
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QListWidget, QPlainTextEdit, QPushButton
from ._base import BaseView


class StoryView(BaseView):
    """전체 줄거리 → 구간별 상세 → 화별 스토리의 3단계 작업 화면."""
    changed = Signal()

    def __init__(self, w):
        super().__init__(w)
        self.mount('story.ui')
        self.w = w
        self.detailList = self.ui.findChild(QListWidget, 'detailList')
        self.chapterCombo = self.ui.findChild(QListWidget, 'chapterCombo')
        self.chapterLabel = self.ui.findChild(QLabel, 'chapterLabel')
        self.selectedRangeLabel = self.ui.findChild(QLabel, 'selectedRangeLabel')
        self.detailCountLabel = self.ui.findChild(QLabel, 'detailCountLabel')
        self.masterPlotPreview = self.ui.findChild(QPlainTextEdit, 'masterPlotPreview')
        self.generateChapterBtn = self.ui.findChild(QPushButton, 'generateChapterBtn')
        self.regenerateChapterBtn = self.ui.findChild(QPushButton, 'regenerateChapterBtn')
        self.generateBtn = self.ui.findChild(QPushButton, 'generateBtn')
        self.regenerateSelectedBtn = self.ui.findChild(QPushButton, 'regenerateSelectedBtn')
        self.regenerateAllBtn = self.ui.findChild(QPushButton, 'regenerateAllBtn')
        self.saveBtn = self.ui.findChild(QPushButton, 'saveBtn')
        self.detail = self.ui.findChild(QPlainTextEdit, 'detail')

        for widget in (self.detailList, self.chapterCombo):
            if widget:
                widget.setUniformItemSizes(True)
        self.detailList.currentRowChanged.connect(self._detail_changed)
        self.chapterCombo.currentRowChanged.connect(self._chapter_changed)
        self.detail.textChanged.connect(lambda: self.saveBtn.setEnabled(True))
        self.saveBtn.clicked.connect(self.save_detail)
        self._detail_rows = []
        self._chapter_rows = []
        self._selected_kind = 'detail'
        self._loading = False
        self.saveBtn.setEnabled(False)

    @staticmethod
    def _range_label(row):
        return f"{int(row['start_chapter']):03d}~{int(row['end_chapter']):03d}화 | {row['status'] or '미작성'}"

    def refresh(self):
        master = (self.w.db.get_meta('master_plot', '') or '').strip()
        self.masterPlotPreview.setPlainText(master)
        ranges = self.w.plot.detail_ranges()
        current = self.detailList.currentRow()
        self._detail_rows = []
        by_key = {(int(r['start_chapter']), int(r['end_chapter'])): r for r in self.w.db.sections()}
        for s, e in ranges:
            row = by_key.get((s, e))
            if row is None:
                row = {
                    'start_chapter': s, 'end_chapter': e, 'status': '미작성',
                    'content': '', 'updated_at': None,
                }
            self._detail_rows.append(row)
        self.detailList.blockSignals(True)
        self.detailList.clear()
        self.detailList.addItems([self._range_label(r) for r in self._detail_rows])
        if self._detail_rows:
            self.detailList.setCurrentRow(max(0, min(current if current >= 0 else 0, len(self._detail_rows) - 1)))
        else:
            self.detailList.setCurrentRow(-1)
        self.detailList.blockSignals(False)
        self.detailCountLabel.setText(f'구간 수: {len(self._detail_rows)}')
        self._load_chapter_rows()
        self._show_selected()
        self.saveBtn.setEnabled(False)

    def _selected_detail(self):
        i = self.detailList.currentRow()
        return self._detail_rows[i] if 0 <= i < len(self._detail_rows) else None

    def _load_chapter_rows(self):
        detail = self._selected_detail()
        if detail:
            start, end = int(detail['start_chapter']), int(detail['end_chapter'])
            self._chapter_rows = self.w.db.chapter_stories_in_range(start, end)
            self.selectedRangeLabel.setText(f'선택 구간: {start}~{end}화')
        else:
            self._chapter_rows = []
            self.selectedRangeLabel.setText('선택 구간: -')
        self.chapterCombo.blockSignals(True)
        self.chapterCombo.clear()
        self.chapterCombo.addItems([
            f"{int(x['chapter_number']):03d}화 | {x['status'] or '초안'} | {x['title'] or ''}"
            for x in self._chapter_rows
        ])
        if self._chapter_rows:
            self.chapterCombo.setCurrentRow(0)
        else:
            self.chapterCombo.setCurrentRow(-1)
        self.chapterCombo.blockSignals(False)

    def _selected_chapter(self):
        i = self.chapterCombo.currentRow()
        return self._chapter_rows[i] if 0 <= i < len(self._chapter_rows) else None

    def _detail_changed(self, _):
        self._selected_kind = 'detail'
        self._load_chapter_rows()
        self._show_selected()

    def _chapter_changed(self, _):
        self._selected_kind = 'chapter'
        self._show_selected()

    def _show_selected(self):
        row = self._selected_chapter() if self._selected_kind == 'chapter' else self._selected_detail()
        self._loading = True
        self.detail.blockSignals(True)
        self.detail.setPlainText((row['content'] if row else '') or '')
        self.detail.blockSignals(False)
        self._loading = False
        self.saveBtn.setEnabled(row is not None)

    def selected(self):
        if self._selected_kind == 'chapter' and self._selected_chapter():
            return 'chapter', self._selected_chapter()
        row = self._selected_detail()
        return ('detail', row) if row else (None, None)

    def save_detail(self):
        kind, row = self.selected()
        if not row:
            return False
        content = self.detail.toPlainText()
        if kind == 'chapter':
            self.w.db.save_chapter_story(
                row['chapter_number'], row['long_start'], row['long_end'],
                row['sub_start'], row['sub_end'], row['title'], content,
                row['status'] or '초안'
            )
        else:
            self.w.db.save_section(
                row['start_chapter'], row['end_chapter'], row['status'] or '초안', content
            )
        self.refresh()
        self.saveBtn.setEnabled(False)
        return True
