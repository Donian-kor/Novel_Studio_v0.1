from __future__ import annotations

import threading
from typing import Any, Callable

from PySide6.QtCore import QRunnable, QObject, Signal, Slot
from novel_studio.utils.cancellation import JobCancelled

JobFunction = Callable[[], Any]
StreamFunction = Callable[[Callable[[str], None]], Any]


class Signals(QObject):
    """백그라운드 작업이 UI에 상태를 전달하기 위한 Qt 신호 모음이다."""

    finished = Signal(object)
    error = Signal(str)
    progress = Signal(str)
    cancelled = Signal()


class Job(QRunnable):
    """취소 가능한 백그라운드 작업을 실행한다."""

    def __init__(self, fn: JobFunction) -> None:
        super().__init__()
        self.fn = fn
        self.signals = Signals()
        self._cancelled = False
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        """작업 취소를 요청하고 취소 이벤트를 설정한다."""
        self._cancelled = True
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        """현재 작업이 취소 요청을 받았는지 반환한다."""
        return self._cancelled

    @Slot()
    def run(self) -> None:
        """작업을 실행하고 완료·오류·취소 신호 중 하나를 보낸다."""
        if self._cancelled:
            self.signals.cancelled.emit()
            return
        try:
            result = self.fn()
            if self._cancelled:
                self.signals.cancelled.emit()
            else:
                self.signals.finished.emit(result)
        except JobCancelled:
            self.signals.cancelled.emit()
        except Exception as exc:
            if self._cancelled:
                self.signals.cancelled.emit()
            else:
                self.signals.error.emit(str(exc))


class StreamJob(Job):
    """토큰을 순차적으로 전달하는 취소 가능한 백그라운드 작업이다."""

    def __init__(self, fn: StreamFunction) -> None:
        super().__init__(fn)

    @Slot()
    def run(self) -> None:
        """스트리밍 작업을 실행하고 토큰마다 진행 신호를 보낸다."""
        if self._cancelled:
            self.signals.cancelled.emit()
            return
        collected: list[str] = []

        def on_token(token: str) -> None:
            if self._cancelled:
                raise JobCancelled()
            if not token:
                return
            collected.append(token)
            self.signals.progress.emit(token)

        try:
            total = self.fn(on_token) or ''.join(collected)
            if self._cancelled:
                self.signals.cancelled.emit()
            else:
                self.signals.finished.emit(total)
        except JobCancelled:
            self.signals.cancelled.emit()
        except Exception as exc:
            if self._cancelled:
                self.signals.cancelled.emit()
            else:
                self.signals.error.emit(str(exc))
