from PySide6.QtCore import QRunnable, QObject, Signal, Slot


class Signals(QObject):
    finished = Signal(object)
    error = Signal(str)
    progress = Signal(str)
    cancelled = Signal()


class Job(QRunnable):
    """취소 가능한 백그라운드 작업

    - cancel(): 작업 취소 요청 (협력적 취소이므로 진행 중인 I/O는 완료까지 대기)
    - is_cancelled(): 취소 상태 확인
    - 취소된 작업의 결과는 무시됨
    """

    def __init__(self, fn):
        super().__init__()
        self.fn = fn
        self.signals = Signals()
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def is_cancelled(self) -> bool:
        return self._cancelled

    @Slot()
    def run(self):
        if self._cancelled:
            self.signals.cancelled.emit()
            return
        try:
            result = self.fn()
            if self._cancelled:
                self.signals.cancelled.emit()
            else:
                self.signals.finished.emit(result)
        except Exception as e:
            if self._cancelled:
                self.signals.cancelled.emit()
            else:
                self.signals.error.emit(str(e))
