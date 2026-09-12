from __future__ import annotations
from PySide6.QtCore import QObject, Signal
class Worker(QObject):
    finished=Signal(object); failed=Signal(str)
    def __init__(self,fn): super().__init__(); self.fn=fn
    def run(self):
        try: self.finished.emit(self.fn())
        except Exception as e: self.failed.emit(str(e))
