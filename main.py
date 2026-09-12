from __future__ import annotations
import sys
from PySide6.QtWidgets import QApplication,QMenuBar
from novel_studio.ui.main_window import MainWindow

def main():
    app=QApplication(sys.argv); win=MainWindow();
    file_menu=win.menuBar().addMenu('프로젝트'); a=file_menu.addAction('새 작품'); a.triggered.connect(win.create_project); a=file_menu.addAction('작품 열기'); a.triggered.connect(win.open_project); b=file_menu.addAction('백업'); b.triggered.connect(lambda: win.backups.backup() if win.pm.active else None)
    win.show(); sys.exit(app.exec())
if __name__=='__main__': main()
