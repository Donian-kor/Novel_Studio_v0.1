from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPlainTextEdit, QPushButton, QSplitter, QAbstractItemView

class StoryView(QWidget):
    changed = Signal()
    def __init__(self, w):
        super().__init__(w); self.w=w
        root=QVBoxLayout(self); root.setContentsMargins(8,8,8,8); root.setSpacing(6)
        title=QLabel("스토리"); title.setStyleSheet("font-size:18px;font-weight:700;"); root.addWidget(title)
        top=QSplitter(Qt.Orientation.Horizontal); root.addWidget(top,0)
        self.longList=QListWidget(); self.subList=QListWidget()
        for lst in (self.longList,self.subList):
            lst.setMinimumHeight(118); lst.setMaximumHeight(118); lst.setUniformItemSizes(True); lst.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerItem)
        lb=QWidget(); ll=QVBoxLayout(lb); ll.setContentsMargins(0,0,0,0); ll.addWidget(QLabel("장기 스토리 구간")); ll.addWidget(self.longList)
        sb=QWidget(); sl=QVBoxLayout(sb); sl.setContentsMargins(0,0,0,0); sl.addWidget(QLabel("세부 스토리 구간")); sl.addWidget(self.subList)
        top.addWidget(lb); top.addWidget(sb); top.setStretchFactor(0,1); top.setStretchFactor(1,1)
        bar=QHBoxLayout(); self.chapterLabel=QLabel("화별 스토리"); bar.addWidget(self.chapterLabel); self.chapterCombo=QListWidget(); self.chapterCombo.setMaximumHeight(74); self.chapterCombo.setMinimumWidth(260); self.chapterCombo.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); bar.addWidget(self.chapterCombo,1)
        self.generateChapterBtn=QPushButton("AI 화별 스토리 생성"); self.regenerateChapterBtn=QPushButton("선택 화 재생성"); bar.addWidget(self.generateChapterBtn); bar.addWidget(self.regenerateChapterBtn); root.addLayout(bar,0)
        toolbar=QHBoxLayout(); self.generateBtn=QPushButton("AI 스토리 생성"); self.regenerateSelectedBtn=QPushButton("선택 구간 재생성"); self.regenerateAllBtn=QPushButton("전체 다시 생성"); self.saveBtn=QPushButton("저장"); toolbar.addWidget(self.generateBtn); toolbar.addWidget(self.regenerateSelectedBtn); toolbar.addWidget(self.regenerateAllBtn); toolbar.addStretch(); toolbar.addWidget(self.saveBtn); root.addLayout(toolbar,0)
        self.detail=QPlainTextEdit(); self.detail.setPlaceholderText("선택한 스토리의 내용을 확인·수정합니다."); root.addWidget(self.detail,1)
        self.longList.currentRowChanged.connect(self._long_changed); self.subList.currentRowChanged.connect(self._sub_changed); self.chapterCombo.currentRowChanged.connect(self._chapter_changed); self.detail.textChanged.connect(lambda: self.saveBtn.setEnabled(True)); self.saveBtn.clicked.connect(self.save_detail)
        self._long_rows=[]; self._sub_rows=[]; self._chapter_rows=[]; self._selected_kind='long'; self._loading=False; self.saveBtn.setEnabled(False)

    @staticmethod
    def _range_label(row): return f"{int(row['start_chapter']):03d}~{int(row['end_chapter']):03d}화 | {row['status'] or '미작성'}"
    def refresh(self):
        long_current=max(0,self.longList.currentRow()); self._long_rows=self.w.db.sections(); self.longList.blockSignals(True); self.longList.clear(); self.longList.addItems([self._range_label(r) for r in self._long_rows]);
        if self._long_rows: self.longList.setCurrentRow(min(long_current,len(self._long_rows)-1))
        self.longList.blockSignals(False); self._load_subrows(self.subList.currentRow()); self.saveBtn.setEnabled(False)
    def _selected_long(self):
        i=self.longList.currentRow(); return self._long_rows[i] if 0<=i<len(self._long_rows) else None
    def _load_subrows(self, keep=-1):
        r=self._selected_long(); self._sub_rows=self.w.db.story_subsections(int(r['start_chapter']),int(r['end_chapter'])) if r else []
        self.subList.blockSignals(True); self.subList.clear(); self.subList.addItems([self._range_label(x) for x in self._sub_rows]);
        if self._sub_rows: self.subList.setCurrentRow(max(0,min(keep if keep>=0 else 0,len(self._sub_rows)-1)))
        self.subList.blockSignals(False); self._load_chapter_rows(); self._show_selected()
    def _load_chapter_rows(self):
        sub=self._selected_sub(); long=self._selected_long();
        if sub: self._chapter_rows=self.w.db.chapter_stories_in_range(int(sub['start_chapter']), int(sub['end_chapter']))
        elif long: self._chapter_rows=self.w.db.chapter_stories_in_range(int(long['start_chapter']), int(long['end_chapter']))
        else: self._chapter_rows=[]
        self.chapterCombo.blockSignals(True); self.chapterCombo.clear(); self.chapterCombo.addItems([f"{int(x['chapter_number']):03d}화 | {x['status'] or '초안'} | {x['title'] or ''}" for x in self._chapter_rows]); self.chapterCombo.blockSignals(False)
        self.chapterCombo.setCurrentRow(0 if self._chapter_rows else -1)
    def _selected_sub(self):
        i=self.subList.currentRow(); return self._sub_rows[i] if 0<=i<len(self._sub_rows) else None
    def _selected_chapter(self):
        i=self.chapterCombo.currentRow(); return self._chapter_rows[i] if 0<=i<len(self._chapter_rows) else None
    def _long_changed(self,_): self._selected_kind='long'; self._load_subrows(0)
    def _sub_changed(self,_): self._selected_kind='sub'; self._load_chapter_rows(); self._show_selected()
    def _chapter_changed(self,_): self._selected_kind='chapter'; self._show_selected()
    def _show_selected(self):
        row=None
        if self._selected_kind=='chapter': row=self._selected_chapter()
        elif self._selected_kind=='sub': row=self._selected_sub()
        else: row=self._selected_long()
        self._loading=True; self.detail.blockSignals(True); self.detail.setPlainText((row['content'] if row else '') or ''); self.detail.blockSignals(False); self._loading=False; self.saveBtn.setEnabled(row is not None)
    def selected(self):
        if self._selected_kind=='chapter' and self._selected_chapter(): return ('chapter',self._selected_chapter())
        if self._selected_kind=='sub' and self._selected_sub(): return ('sub',self._selected_sub())
        row=self._selected_long(); return ('long',row) if row else (None,None)
    def save_detail(self):
        kind,row=self.selected();
        if not row:return False
        content=self.detail.toPlainText()
        if kind=='chapter': self.w.db.save_chapter_story(row['chapter_number'],row['long_start'],row['long_end'],row['sub_start'],row['sub_end'],row['title'],content,row['status'] or '초안')
        elif kind=='sub': self.w.db.save_story_subsection(row['parent_start'],row['parent_end'],row['start_chapter'],row['end_chapter'],row['title'],content,row['status'] or '초안')
        else: self.w.db.save_section(row['start_chapter'],row['end_chapter'],row['status'] or '초안',content)
        self.refresh(); self.saveBtn.setEnabled(False); return True
