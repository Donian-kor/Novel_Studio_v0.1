from PySide6.QtCore import QRunnable, QObject, Signal, Slot


class JobCancelled(Exception):
    """스트리밍 작업을 즉시 중단하기 위한 내부 예외."""


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


class StreamJob(Job):
    """토큰 스트리밍 작업.

    fn(callback) 형태로 받는다. fn은 생성되는 토큰마다 callback(token)을
    호출하며(→ progress 시그널 방출), 마지막에 전체 텍스트를 return한다.
    """

    @Slot()
    def run(self):
        if self._cancelled:
            self.signals.cancelled.emit()
            return
        collected = []

        def on_token(t):
            if self._cancelled:
                raise JobCancelled()
            if not t:
                return
            collected.append(t)
            self.signals.progress.emit(t)

        try:
            total = self.fn(on_token) or ''.join(collected)
            if self._cancelled:
                self.signals.cancelled.emit()
            else:
                self.signals.finished.emit(total)
        except JobCancelled:
            self.signals.cancelled.emit()
        except Exception as e:
            if self._cancelled:
                self.signals.cancelled.emit()
            else:
                self.signals.error.emit(str(e))
