# -*- coding: utf-8 -*-
"""Novel Studio 내장 사용법 도움말 대화상자.

좌측 목차(QTreeWidget) + 우측 본문(QTextBrowser) 분할 레이아웃.
목차 항목을 클릭하면 본문의 해당 앵커로 스크롤하고,
창 크기·위치는 QSettings에 저장해 다음에도 유지한다.
"""
from PySide6.QtCore import Qt, QSettings, QTimer
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QSplitter, QTreeWidget,
                               QTreeWidgetItem, QTextBrowser, QHBoxLayout,
                               QPushButton, QLabel)

from novel_studio.ui.help.content import get_help_html, get_sections, get_style

# QTextBrowser/목차 트리에 적용할 위젯 스타일 (기본 QSS는 목록류만 커버하므로 보완)
_WIDGET_QSS = """
QTreeWidget {
    background: #2B2B2B;
    color: #E8E6E3;
    border: 1px solid #5E5B57;
    border-radius: 4px;
}
QTreeWidget::item:selected {
    background: #6B5B4A;
    color: #FFFFFF;
}
QTextBrowser {
    background: #2B2B2B;
    color: #E8E6E3;
    border: 1px solid #5E5B57;
    border-radius: 4px;
    selection-background-color: #6B5B4A;
}
"""


class HelpDialog(QDialog):
    def __init__(self, parent=None, anchor=None):
        super().__init__(parent)
        self.setWindowTitle('Novel Studio 사용법')
        self.resize(1000, 720)
        self._last_anchor = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)

        # ---------- 글씨 크기 조절 툴바 ----------
        font_bar = QHBoxLayout()
        self.fontMinus = QPushButton('A-')
        self.fontMinus.setFixedWidth(40)
        self.fontPlus = QPushButton('A+')
        self.fontPlus.setFixedWidth(40)
        self.fontReset = QPushButton('기본 크기')
        self.fontLabel = QLabel('')
        self.fontLabel.setStyleSheet('color:#A8A5A0;')
        font_bar.addWidget(self.fontMinus)
        font_bar.addWidget(self.fontLabel)
        font_bar.addWidget(self.fontPlus)
        font_bar.addStretch(1)
        font_bar.addWidget(self.fontReset)
        lay.addLayout(font_bar)

        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet(_WIDGET_QSS)
        self.browser = QTextBrowser(self)
        self.browser.setStyleSheet(_WIDGET_QSS)
        self.browser.setOpenExternalLinks(True)
        # QTextDocument 기본 스타일시트는 요소 선택자만 지원
        self.browser.document().setDefaultStyleSheet(get_style())
        self.browser.setHtml(get_help_html())
        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.browser)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([240, 760])
        lay.addWidget(self.splitter)

        row = QHBoxLayout()
        row.addStretch(1)
        close = QPushButton('닫기')
        close.clicked.connect(self.accept)
        row.addWidget(close)
        lay.addLayout(row)

        # 목차 트리 채우기
        for title, anc in get_sections():
            item = QTreeWidgetItem([title])
            item.setData(0, Qt.ItemDataRole.UserRole, anc)
            self.tree.addTopLevelItem(item)
        self.tree.currentItemChanged.connect(self._on_tree_changed)

        # ---------- 글씨 크기(배율) 적용 ----------
        self._zoom = self._load_zoom()
        self._apply_zoom()
        self.fontPlus.clicked.connect(self._zoom_in)
        self.fontMinus.clicked.connect(self._zoom_out)
        self.fontReset.clicked.connect(self._zoom_reset)
        self._update_font_label()

        self._restore_geometry()
        # anchor가 지정되면(예: 메뉴의 [단축키]) 해당 섹션으로 이동
        target = anchor
        if target:
            for i in range(self.tree.topLevelItemCount()):
                it = self.tree.topLevelItem(i)
                if it.data(0, Qt.ItemDataRole.UserRole) == target:
                    self.tree.setCurrentItem(it)
                    break
        else:
            self.tree.setCurrentItem(self.tree.topLevelItem(0))

    # ---------- 내비게이션 ----------
    def _on_tree_changed(self, current, _previous):
        if current is None:
            return
        self._goto(str(current.data(0, Qt.ItemDataRole.UserRole)))

    def _goto(self, anchor: str):
        """본문을 해당 앵커 위치로 스크롤한다."""
        if anchor == self._last_anchor:
            return
        self._last_anchor = anchor

        def _scroll():
            # 같은 앵커를 다시 눌러도 동작하도록 먼저 최상단으로 이동
            self.browser.scrollToAnchor('top')
            self.browser.scrollToAnchor(anchor)
        # 렌더링 완료 후 스크롤해야 정확히 이동한다
        QTimer.singleShot(0, _scroll)

    # ---------- 글씨 크기 조절 ----------
    # QTextDocument의 기본 스타일시트는 요소별 pt 크기를 고정하므로,
    # zoomIn 대신 스타일시트의 pt 값 자체를 배율에 맞게 재계산해 다시 렌더링한다.
    _BASE_PT = 10
    _DEFAULT_ZOOM = 130          # 기본 10pt는 작아서 130%(≈13pt)를 기본값으로 사용
    _MIN_ZOOM, _MAX_ZOOM = 80, 220

    def _load_zoom(self) -> int:
        try:
            v = QSettings(self._ORG, self._APP).value('help_font_zoom', self._DEFAULT_ZOOM, type=int)
            return max(self._MIN_ZOOM, min(int(v), self._MAX_ZOOM))
        except Exception:
            return self._DEFAULT_ZOOM

    def _save_zoom(self):
        try:
            QSettings(self._ORG, self._APP).setValue('help_font_zoom', self._zoom)
        except Exception:
            pass

    @staticmethod
    def _scaled_style(pct: int) -> str:
        """기본 스타일시트의 모든 pt 크기를 pct 배율로 환산한다."""
        import re
        f = pct / 100.0

        def _fmt(v: float) -> str:
            return f'{int(v)}pt' if float(v).is_integer() else f'{v}pt'

        return re.sub(r'(\d+(?:\.\d+)?)pt',
                      lambda m: _fmt(round(float(m.group(1)) * f, 1)),
                      get_style())

    def _update_font_label(self):
        self.fontLabel.setText(f'글씨 {self._zoom}% (약 {round(self._BASE_PT * self._zoom / 100)}pt)')

    def _apply_zoom(self):
        """현재 배율로 본문을 다시 렌더링한다. (스크롤 위치 유지)"""
        sb = self.browser.verticalScrollBar()
        pos = sb.value()
        self.browser.document().setDefaultStyleSheet(self._scaled_style(self._zoom))
        self.browser.setHtml(get_help_html())
        self._last_anchor = None  # 문서가 새로 로드됨
        QTimer.singleShot(0, lambda: sb.setValue(min(pos, sb.maximum())))

    def _zoom_in(self):
        if self._zoom >= self._MAX_ZOOM:
            return
        self._zoom = min(self._MAX_ZOOM, self._zoom + 10)
        self._apply_zoom(); self._save_zoom(); self._update_font_label()

    def _zoom_out(self):
        if self._zoom <= self._MIN_ZOOM:
            return
        self._zoom = max(self._MIN_ZOOM, self._zoom - 10)
        self._apply_zoom(); self._save_zoom(); self._update_font_label()

    def _zoom_reset(self):
        if self._zoom == self._DEFAULT_ZOOM:
            return
        self._zoom = self._DEFAULT_ZOOM
        self._apply_zoom(); self._save_zoom(); self._update_font_label()

    # ---------- 창 크기·위치 기억 ----------
    _ORG = 'Novel Studio'
    _APP = 'HelpDialog'

    def _restore_geometry(self):
        try:
            s = QSettings(self._ORG, self._APP)
            g = s.value('geometry')
            if g is not None:
                self.restoreGeometry(g)
            sizes = s.value('splitter')
            if sizes is not None:
                self.splitter.restoreState(sizes)
        except Exception:
            pass

    def closeEvent(self, event):
        try:
            s = QSettings(self._ORG, self._APP)
            s.setValue('geometry', self.saveGeometry())
            s.setValue('splitter', self.splitter.saveState())
        except Exception:
            pass
        super().closeEvent(event)
