"""Novel Studio 애플리케이션 컨트롤러."""
from __future__ import annotations

from typing import Any, Callable, Optional

from PySide6.QtCore import QObject, QThreadPool, Signal, Slot

from novel_studio.jobs.worker import Job, StreamJob


class NovelController(QObject):
    """View와 Service 사이의 작업 흐름을 단일 경로로 조정한다."""

    status_changed = Signal(str)
    progress_updated = Signal(int, int, str)
    chapter_changed = Signal(int)
    ai_status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, main_window=None) -> None:
        super().__init__(main_window)
        self.main_window = main_window
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self._busy = False
        self._current_job: Optional[Job] = None
        self._current_chapter = 1
        self._services: dict[str, Any] = {}
        self._active_stream_callback: Optional[Callable[[str], None]] = None

    def set_main_window(self, main_window) -> None:
        self.main_window = main_window

    def set_main_window_ref(self, main_window) -> None:
        self.set_main_window(main_window)

    @property
    def main_window_ref(self):
        return self.main_window

    def set_services(self, services: dict[str, Any]) -> None:
        """서비스 의존성을 한 곳에서 주입한다."""
        self._services = dict(services)
        for name in (
            "project", "ai", "db", "context", "settings",
            "continuity", "writing", "memory", "export",
        ):
            setattr(self, f"{name}_service", self._services.get(name))

    @property
    def busy(self) -> bool:
        return self._busy

    @property
    def cancel_requested(self) -> bool:
        """현재 작업에 취소 요청이 들어왔는지 반환한다."""
        return bool(self._current_job and self._current_job.is_cancelled())

    @property
    def current_chapter(self) -> int:
        return self._current_chapter

    @current_chapter.setter
    def current_chapter(self, value: int) -> None:
        self._current_chapter = max(1, int(value))
        self.chapter_changed.emit(self._current_chapter)

    def _begin_job(self, job: Job, label: str) -> None:
        if self._busy:
            raise RuntimeError("이미 작업이 실행 중입니다.")
        self._busy = True
        self._current_job = job
        self.status_changed.emit(label)
        self.pool.start(job)

    def _finish_job_state(self) -> None:
        self._busy = False
        self._current_job = None
        self._active_stream_callback = None

    def _run_job(
        self,
        label: str,
        fn: Callable[[], Any],
        done_callback: Optional[Callable[[Any], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
        cancelled_callback: Optional[Callable[[], None]] = None,
    ) -> bool:
        """일반 작업을 단일 실행 경로로 처리한다."""
        if self._busy:
            self.error_occurred.emit("이미 작업이 실행 중입니다.")
            return False

        job = Job(fn)
        job.signals.finished.connect(lambda result: self._on_job_done(done_callback, result))
        job.signals.error.connect(lambda error: self._on_job_error(error_callback, error))
        job.signals.cancelled.connect(lambda: self._on_job_cancelled(cancelled_callback))
        self._begin_job(job, label)
        return True

    def _run_stream(
        self,
        label: str,
        fn: Callable[[Callable[[str], None]], Any],
        done_callback: Optional[Callable[[Any], None]] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
        cancelled_callback: Optional[Callable[[], None]] = None,
    ) -> bool:
        """스트리밍 작업을 Controller가 일관되게 관리한다."""
        if self._busy:
            self.error_occurred.emit("이미 작업이 실행 중입니다.")
            return False

        job = StreamJob(fn)
        self._active_stream_callback = progress_callback
        # Controller(QObject)의 bound slot에 직접 연결해 토큰을 UI 스레드로 전달한다.
        # lambda로 UI callback을 직접 호출하면 worker thread에서 위젯을 건드릴 수 있다.
        job.signals.progress.connect(self._on_stream_token)
        job.signals.finished.connect(lambda result: self._on_stream_done(done_callback, result))
        job.signals.error.connect(lambda error: self._on_stream_error(error_callback, error))
        job.signals.cancelled.connect(lambda: self._on_stream_cancelled(cancelled_callback))
        self._begin_job(job, label)
        return True

    def _on_job_done(self, callback: Optional[Callable[[Any], None]], result: Any) -> None:
        self._finish_job_state()
        if callback:
            callback(result)

    def _on_job_error(self, callback: Optional[Callable[[str], None]], error: str) -> None:
        self._finish_job_state()
        self.error_occurred.emit(str(error))
        if callback:
            callback(str(error))

    def _on_job_cancelled(self, callback: Optional[Callable[[], None]]) -> None:
        self._finish_job_state()
        self.status_changed.emit("작업이 취소되었습니다.")
        if callback:
            callback()

    @Slot(str)
    def _on_stream_token(self, token: str) -> None:
        callback = self._active_stream_callback
        if callback:
            callback(token)

    def _on_stream_done(self, callback: Optional[Callable[[Any], None]], result: Any) -> None:
        self._finish_job_state()
        if callback:
            callback(result)

    def _on_stream_error(self, callback: Optional[Callable[[str], None]], error: str) -> None:
        self._finish_job_state()
        self.error_occurred.emit(str(error))
        if callback:
            callback(str(error))

    def _on_stream_cancelled(self, callback: Optional[Callable[[], None]] = None) -> None:
        self._finish_job_state()
        self.status_changed.emit("작업이 취소되었습니다.")
        if callback:
            callback()

    def run_task(
        self,
        label: str,
        fn: Callable[[], Any],
        done_callback: Optional[Callable[[Any], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
        cancelled_callback: Optional[Callable[[], None]] = None,
    ) -> bool:
        """임의의 백그라운드 작업을 Controller 경로로 실행한다."""
        return self._run_job(
            label, fn, done_callback, error_callback, cancelled_callback
        )

    def run_stream(
        self,
        label: str,
        fn: Callable[[Callable[[str], None]], Any],
        stream_callback: Optional[Callable[[str], None]] = None,
        done_callback: Optional[Callable[[Any], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
        cancelled_callback: Optional[Callable[[], None]] = None,
    ) -> bool:
        """임의의 스트리밍 작업을 Controller 경로로 실행한다."""
        return self._run_stream(
            label, fn, done_callback, stream_callback, error_callback, cancelled_callback
        )

    def stop_current_job(self) -> bool:
        """현재 Controller 작업에 취소를 요청한다."""
        job = self._current_job
        if job is None or not self._busy:
            return False
        job.cancel()
        self.status_changed.emit("작업 취소 요청됨...")
        return True

    # ---------- 프로젝트 ----------
    def new_project(self, path: str) -> bool:
        """StartupDialog에서 생성된 프로젝트가 유효한지 확인한다."""
        try:
            from pathlib import Path
            root = Path(path)
            return (root / "project.json").exists()
        except Exception as exc:
            self.error_occurred.emit(f"프로젝트 확인 실패: {exc}")
            return False

    def open_project(self, path: str) -> bool:
        """열 대상이 유효한 Novel Studio 프로젝트인지 확인한다."""
        return self.new_project(path)

    def save_project_settings(self, settings: dict[str, Any]) -> bool:
        try:
            self.project_service.save_settings(settings)
            return True
        except Exception as exc:
            self.error_occurred.emit(f"설정 저장 실패: {exc}")
            return False

    # ---------- 집필 ----------
    def write_chapter(
        self,
        chapter: int,
        stream_callback: Optional[Callable[[str], None]] = None,
        done_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
        cancelled_callback: Optional[Callable[[], None]] = None,
    ) -> bool:
        def stream_fn(callback: Callable[[str], None]):
            return self.writing_service.write_chapter(chapter, callback)

        return self._run_stream(
            f"{chapter}화 AI 집필 중...",
            stream_fn,
            done_callback,
            stream_callback,
            error_callback,
            cancelled_callback,
        )

    def revise_current(self, text: str) -> str:
        return self.writing_service.revise_chapter(text)

    def revise_text(
        self,
        text: str,
        stream_callback: Optional[Callable[[str], None]] = None,
        done_callback: Optional[Callable[[str], None]] = None,
    ) -> bool:
        prompt = "사건과 설정을 변경하지 말고 다음 원고를 자연스럽게 윤문하라. 본문만 출력.\n" + text

        def stream_fn(callback: Callable[[str], None]):
            chunks: list[str] = []
            for token in self.ai_service.generate_stream(
                prompt, temperature=0.38, max_tokens=14000
            ):
                callback(token)
                chunks.append(token)
            return "".join(chunks)

        return self._run_stream("AI 윤문 중...", stream_fn, done_callback, stream_callback)

    def check_current_chapter(
        self,
        chapter: int,
        text: str,
        done_callback: Optional[Callable[[Any], None]] = None,
    ) -> bool:
        def job():
            return self.continuity_service.check_chapter(chapter, text)

        return self._run_job("AI 연속성 검사 중...", job, done_callback)

    def check_consistency(
        self,
        chapter: int,
        text: str,
        done_callback: Optional[Callable[[Any], None]] = None,
    ) -> bool:
        return self.check_current_chapter(chapter, text, done_callback)

    def audit_long_form(
        self,
        size: int = 50,
        done_callback: Optional[Callable[[str], None]] = None,
    ) -> bool:
        def progress(current: int, total: int, range_str: str, result_text: str) -> None:
            pct = int(current / max(1, total) * 100)
            self.progress_updated.emit(current, total, f"{pct}% ({current}/{total}) {range_str}")

        def job():
            return self.continuity_service.audit_long_form(
                size=size,
                progress_callback=progress,
                cancelled_check=lambda: bool(
                    self._current_job and self._current_job.is_cancelled()
                ),
            )

        return self._run_job("장편 정밀 연속성 검사 중...", job, done_callback)

    # ---------- 기억/설정/내보내기 ----------
    def refresh_memory(self, chapter: int, text: str, previous_state: str) -> bool:
        def job():
            return self.memory_service.update_memory(chapter, text, previous_state)

        return self._run_job("기억 업데이트 중...", job)

    def save_memory_notes(self, notes: str) -> bool:
        return self.memory_service.save_memory_notes(notes)

    def get_ai_settings(self) -> dict[str, Any]:
        return self.settings_service.get_ai_settings()

    def save_provider_config(self, provider_id: str, config: dict[str, Any]) -> bool:
        try:
            self.settings_service.save_provider_config(provider_id, config)
            return True
        except Exception as exc:
            self.error_occurred.emit(f"AI 설정 저장 실패: {exc}")
            return False

    def export_manuscript(self) -> str:
        return self.export_service.export_manuscript()

    def update_ai_status(self) -> None:
        try:
            provider_id = self.settings_service.get_active_provider()
            config = self.settings_service.get_provider_config(provider_id)
            name = config.get("name", provider_id)
            model = config.get("model", "")
            self.ai_status_changed.emit(f"AI ● {name} / {model or '모델 미설정'}")
        except Exception:
            self.ai_status_changed.emit("AI ● 확인 필요")
