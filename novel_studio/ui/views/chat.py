from PySide6.QtWidgets import QMainWindow, QWidget, QPlainTextEdit, QPushButton, QLabel
from novel_studio.ui.loader import load_ui
from typing import Protocol, runtime_checkable, Any


@runtime_checkable
class ChatWindowHost(Protocol):
    """ChatWindow가 통신하는 메인 윈도우 계약."""

    def send_chat(self) -> Any: ...

    def search_chat(self) -> Any: ...


class ChatWindow(QMainWindow):
    def __init__(self, w: ChatWindowHost):
        # 부모 종속을 없애고 독립 창으로 만들어 메인 창 뒤에 숨지 않게 한다.
        super().__init__()
        self.ui = load_ui('chat.ui')
        self.setCentralWidget(self.ui)
        self.w = w
        self.log = self.ui.findChild(QPlainTextEdit, 'log')
        self.input = self.ui.findChild(QPlainTextEdit, 'input')
        self.sendBtn = self.ui.findChild(QPushButton, 'sendBtn')
        self.searchBtn = self.ui.findChild(QPushButton, 'searchBtn')
        self.contextLabel = self.ui.findChild(QLabel, 'contextLabel')
        self.sendBtn.clicked.connect(w.send_chat)
        self.searchBtn.clicked.connect(w.search_chat)
        t = self.ui.windowTitle()
        if t:
            self.setWindowTitle(t)

    def refresh(self, rows):
        self.log.clear()
        for r in rows:
            self.log.appendPlainText(
                ('사용자: ' if r['role'] == 'user' else 'AI: ') + r['content'] + '\n'
            )
