from __future__ import annotations
from PySide6.QtCore import QObject, Signal, QRunnable, Slot
import traceback
class JobSignals(QObject):
    result=Signal(object); error=Signal(str); progress=Signal(str); finished=Signal()
class Job(QRunnable):
    def __init__(self,title,fn,*args,**kwargs):super().__init__();self.title=title;self.fn=fn;self.args=args;self.kwargs=kwargs;self.signals=JobSignals()
    @Slot()
    def run(self):
        try:self.signals.result.emit(self.fn(*self.args,**self.kwargs))
        except Exception as e:self.signals.error.emit(f'{e}\n\n{traceback.format_exc()}')
        finally:self.signals.finished.emit()
