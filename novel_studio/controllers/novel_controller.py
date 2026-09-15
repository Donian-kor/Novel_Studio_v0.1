"""Novel Studio 애플리케이션 컨트롤러."""
from __future__ import annotations

from typing import Any, Callable, Optional

from PySide6.QtCore import QObject, QThreadPool, Signal, Slot

from novel_studio.jobs.worker import Job, StreamJob
from novel_studio.utils.cancellation import CancelToken


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
        self._cancel_token = CancelToken()
        self._job_queue: list[tuple] = []

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
            "continuity", "writing", "end_state", "export",
        ):
            setattr(self, f"{name}_service", self._services.get(name))
        # 정지 버튼 → AI provider I/O 중단 경로를 연결한다.
        ai_service = getattr(self, "ai_service", None)
        if ai_service is not None and hasattr(ai_service, "set_cancel_handler"):
            try:
                ai_service.set_cancel_handler(
                    lambda: self._cancel_token.is_set(),
                    getattr(ai_service, "abort", None),
                )
            except Exception:
                pass
        # 일부 배선 오류에 대비해 취소 검사 함수만이라도 항상 보장한다.
        self._cancel_check = lambda: self._cancel_token.is_set()

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
        # 새 작업 시작 시 이전 작업의 취소 상태를 초기화한다.
        try:
            self._cancel_token.reset()
        except Exception:
            pass
        self.status_changed.emit(label)
        self.pool.start(job)

    def cancelled_check(self) -> Callable[[], bool]:
        """현재 작업의 취소 여부를 묻는 함수(순차 AI 호출 경계에서 사용)."""
        return lambda: bool(
            self._busy
            and self._current_job is not None
            and self._cancel_token.is_set()
        )

    def _finish_job_state(self) -> None:
        self._busy = False
        self._current_job = None
        self._active_stream_callback = None
        # If there are queued jobs, start the next one
        if self._job_queue:
            queued = self._job_queue.pop(0)
            if queued[5]:  # is_stream True
                label, fn, done_cb, error_cb, cancelled_cb, _, progress_cb = queued
                self._run_stream(label, fn, done_cb, progress_cb, error_cb, cancelled_cb)
            else:
                label, fn, done_cb, error_cb, cancelled_cb, _ = queued
                self._run_job(label, fn, done_cb, error_cb, cancelled_cb)

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
            # Queue the job to run after current job finishes
            self._job_queue.append((
                label, fn, done_callback, error_callback, cancelled_callback,
                False  # is_stream = False
            ))
            return True  # Indicate job is queued (will be run later)

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
            # Queue the job to run after current job finishes
            self._job_queue.append((
                label, fn, done_callback, error_callback, cancelled_callback,
                True,  # is_stream = True
                progress_callback  # store progress_callback
            ))
            return True  # Indicate job is queued

        job = StreamJob(fn)
        self._active_stream_callback = progress_callback
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
        """현재 Controller 작업에 취소를 요청한다.

        취소 토큰을 세우는 동시에 진행 중인 provider 응답을 닫아,
        블로킹 read/readline 대기도 즉시(수 초 내) 풀리게 한다.
        """
        job = self._current_job
        if job is None or not self._busy:
            return False
        job.cancel()
        self._cancel_token.set()
        # 진행 중인 HTTP 응답 close (worker 스레드의 read/readline을 깨운다)
        ai_service = getattr(self, "ai_service", None)
        abort = getattr(ai_service, "abort", None)
        if callable(abort):
            try:
                abort()
            except Exception:
                pass
        self.status_changed.emit("작업 취소 요청됨...")
        return True

    def generate_end_state(self, chapter: int, text: str, done_callback=None, error_callback=None, cancelled_callback=None) -> bool:
        return self._run_job("화 종료 상태 생성 중...", lambda: self.end_state_service.generate(int(chapter), text), done_callback, error_callback, cancelled_callback)

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

    # ---------- 설정/내보내기 ----------
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
