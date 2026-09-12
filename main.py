import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from novel_studio.logging_config import setup_logging
from novel_studio.core.app_settings import AppSettings
from novel_studio.ui.startup import StartupDialog


def _pick_project() -> Path | None:
    """1) 명령줄 경로 → 2) 마지막 프로젝트 → 3) None(다이어로그 표시)"""
    for a in sys.argv[1:]:
        if not a.startswith('-') and (Path(a) / 'project.json').exists():
            return Path(a)
    try:
        last = AppSettings().data.get('last_project')
    except Exception:
        last = None
    if last and (Path(last) / 'project.json').exists():
        return Path(last)
    return None


def main() -> int:
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("Novel Studio")
    app.setOrganizationName("Novel Studio")
    qss = Path(__file__).parent / "resources" / "default.qss"
    if qss.exists():
        app.setStyleSheet(qss.read_text(encoding="utf-8"))

    root = _pick_project()
    if root is None:
        dlg = StartupDialog()
        if dlg.exec() != dlg.DialogCode.Accepted:
            return 0
        root = dlg.selected_project

    from novel_studio.ui.main_window import MainWindow
    window = MainWindow(root)
    window.show()
    window.open_ai_chat()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
