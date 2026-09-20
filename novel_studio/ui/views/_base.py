from PySide6.QtWidgets import QWidget,QVBoxLayout
from novel_studio.ui.loader import load_ui
class BaseView(QWidget):
    ui = None

    def mount(self, filename):
        self.ui = load_ui(filename)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)
