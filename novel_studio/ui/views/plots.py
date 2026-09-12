from ._base import BaseView
from PySide6.QtWidgets import QSpinBox,QListWidget,QPlainTextEdit,QPushButton,QSplitter
from PySide6.QtCore import Qt, QSettings
class PlotsView(BaseView):
    def __init__(self,w):
        super().__init__(w); self.mount('plots.ui'); self.w=w
        self.start=self.ui.findChild(QSpinBox,'start'); self.end=self.ui.findChild(QSpinBox,'end'); self.list=self.ui.findChild(QListWidget,'list'); self.detail=self.ui.findChild(QPlainTextEdit,'detail')
        self.generateBtn=self.ui.findChild(QPushButton,'generateBtn'); self.allBtn=self.ui.findChild(QPushButton,'allBtn'); self.improveBtn=self.ui.findChild(QPushButton,'improveBtn'); self.saveBtn=self.ui.findChild(QPushButton,'saveBtn')
        self.splitter=self.ui.findChild(QSplitter,'plotsSplitter')
        if self.splitter:
            self.splitter.setChildrenCollapsible(False); self.splitter.setHandleWidth(9)
            self.splitter.setStyleSheet('QSplitter::handle { background: #6a6a6a; } QSplitter::handle:hover { background: #9a9a9a; }')
            settings=QSettings('NovelStudio','NovelStudio'); saved=settings.value('plotsSplitterSizes', None)
            try: self.splitter.setSizes([int(x) for x in saved]) if saved else self.splitter.setSizes([420,980])
            except Exception: self.splitter.setSizes([420,980])
            self.splitter.splitterMoved.connect(lambda pos,index,sp=self.splitter: QSettings('NovelStudio','NovelStudio').setValue('plotsSplitterSizes', sp.sizes()))
        self.list.currentRowChanged.connect(self.show_selected); self.detail.textChanged.connect(self._on_edited); self.saveBtn.setEnabled(False) if self.saveBtn else None
    def refresh(self):
        current = self.list.currentRow() if self.list else -1
        self.list.blockSignals(True)
        self.list.clear(); [self.list.addItem(f"{p['chapter_number']:03d}화 {p['title']} | {p['status']}") for p in self.w.db.chapter_plans()]
        if self.list.count(): self.list.setCurrentRow(min(max(current,0), self.list.count()-1))
        else: self.detail.clear()
        self.list.blockSignals(False)
        if self.saveBtn: self.saveBtn.setEnabled(self.selected() is not None)
    def selected(self):
        rows=self.w.db.chapter_plans(); i=self.list.currentRow(); return rows[i] if 0<=i<len(rows) else None
    def show_selected(self):
        p=self.selected(); self.detail.setPlainText(p['content'] if p else '')
        if self.saveBtn: self.saveBtn.setEnabled(p is not None)
    def _on_edited(self):
        if self.saveBtn: self.saveBtn.setEnabled(self.selected() is not None)
    def save_detail(self):
        p=self.selected();
        if not p:return False
        self.w.db.save_chapter_plan(p['chapter_number'],p['title'],self.detail.toPlainText(),p['status'] or '초안'); return True
