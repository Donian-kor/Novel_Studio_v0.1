import sys
from PySide6.QtWidgets import QApplication
from novel_studio.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Novel Studio")
    app.setOrganizationName("Novel Studio")
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
