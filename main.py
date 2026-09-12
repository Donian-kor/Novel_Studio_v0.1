import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from novel_studio.logging_config import setup_logging
from novel_studio.ui.startup import StartupDialog


def main() -> int:
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("Novel Studio")
    app.setOrganizationName("Novel Studio")
    qss = Path(__file__).parent / "resources" / "default.qss"
    if qss.exists():
        app.setStyleSheet(qss.read_text(encoding="utf-8"))
    dlg = StartupDialog()
    if dlg.exec() != dlg.DialogCode.Accepted:
        return 0
    from novel_studio.ui.main_window import MainWindow
    window = MainWindow(dlg.selected_project)
    window.show()
    window.open_ai_chat()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
