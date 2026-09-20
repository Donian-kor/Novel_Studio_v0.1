from pathlib import Path
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
BASE = Path(__file__).resolve().parent / 'forms'


def load_ui(filename, parent=None):
    f = QFile(str(BASE / filename))
    f.open(QFile.ReadOnly)
    w = QUiLoader().load(f, parent)
    f.close()
    if w is None:
        raise RuntimeError(f'UI 로드 실패: {BASE / filename}')
    return w
