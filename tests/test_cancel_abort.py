# -*- coding: utf-8 -*-
"""정지 버튼 즉시 중단: provider abort / 메모리 경계 / controller 배선 테스트."""
import os
import unittest
from types import SimpleNamespace

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from novel_studio.jobs.worker import JobCancelled


class TestProviderAbort(unittest.TestCase):
    def test_provider_abort_closes_active_response(self):
        from novel_studio.ai.providers.base import AIProvider

        class _FakeResponse:
            closed = False

            def close(self):
                self.closed = True

        class _P(AIProvider):
            def _chat_impl(self, *a, **kw):
                return ""

            def _chat_stream_impl(self, *a, **kw):
                return iter(())

        provider = _P({})
        resp = _FakeResponse()
        with provider._open_response(resp) as r:
            self.assertIs(r, resp)
            provider.abort()
            self.assertTrue(resp.closed)
        self.assertIsNone(provider._active_response)

    def test_abort_handler_not_called_to_avoid_recursion(self):
        """abort()가 _abort_handler를 호출하지 않는다 (무한 재귀 방지)."""
        from novel_studio.ai.providers.base import AIProvider

        called = []

        class _P(AIProvider):
            def _chat_impl(self, *a, **kw):
                return ""

            def _chat_stream_impl(self, *a, **kw):
                return iter(())

        provider = _P({}, abort_handler=lambda: called.append(1))
        provider.abort()
        self.assertEqual(called, [])

    def test_job_cancelled_never_retried(self):
        """취소는 네트워크 오류로 오인해 재시도되지 않는다."""
        from novel_studio.utils.retry import is_retryable_error
        self.assertFalse(is_retryable_error(JobCancelled()))

    def test_read_json_raises_cancelled_when_interrupted(self):
        from novel_studio.ai.providers.base import AIProvider

        class _FakeResponse:
            def __init__(self, chunks):
                self.chunks = iter(chunks)

            def read(self, size):
                try:
                    return next(self.chunks)
                except StopIteration:
                    return b""

            def close(self):
                pass

        class _P(AIProvider):
            def _chat_impl(self, *a, **kw):
                return ""

            def _chat_stream_impl(self, *a, **kw):
                return iter(())

        # 취소가 세워진 상태에서 read로 진입하면 JobCancelled가 발생한다.
        provider = _P({}, cancel_check=lambda: True)
        resp = _FakeResponse([b'{"choices": [{"message": {"content": "a' + b'}]}' ])
        with self.assertRaises(JobCancelled):
            provider._read_json(resp)


class TestMemoryManagerCancel(unittest.TestCase):
    def test_update_stops_at_boundary_and_skips_db(self):
        """메모리 순차 갱신 중 취소되면 다음 AI 호출과 DB 기록이 중단된다."""
        from novel_studio.memory.memory_manager import MemoryManager

        calls = []

        class _FakeAI:
            def generate(self, *a, **kw):
                calls.append("ai")
                return "요약"

            def cancelled_check(self):
                # 요약 생성 후에는 취소 상태로 만든다.
                return len(calls) >= 1

        db = SimpleNamespace(
            chapter_state=lambda n: None,
            save_summary=lambda *a: calls.append("save_summary"),
            save_chapter_state=lambda *a: calls.append("save_chapter_state"),
            save_snapshot=lambda *a: calls.append("save_snapshot"),
            section_for_chapter=lambda n: None,
        )
        mm = MemoryManager(db, _FakeAI())
        with self.assertRaises(JobCancelled):
            mm.update(1, "원고")

        # 요약 1회 후 취소 → 상태 생성·DB 기록이 일어나지 않는다.
        self.assertEqual(calls, ["ai"])


class TestContinuityCheckerCancel(unittest.TestCase):
    def test_check_cancelled_before_generate(self):
        from novel_studio.continuity.checker import ContinuityChecker

        class _FakeAI:
            def cancelled_check(self):
                return True

            def generate(self, *a, **kw):
                return "결과"

        db = SimpleNamespace(add_continuity=lambda *a: None)
        ctx = SimpleNamespace(build=lambda n: "")
        with self.assertRaises(JobCancelled):
            ContinuityChecker(db, _FakeAI(), ctx).check(1, "원고")


class TestControllerStopAborts(unittest.TestCase):
    def test_stop_current_job_aborts_ai_service(self):
        from novel_studio.controllers.novel_controller import NovelController

        controller = NovelController()
        aborted = []
        controller.ai_service = SimpleNamespace(abort=lambda: aborted.append(1))

        controller._busy = True
        controller._current_job = SimpleNamespace(cancel=lambda: None)

        self.assertTrue(controller.stop_current_job())
        self.assertTrue(controller._cancel_token.is_set())
        self.assertEqual(aborted, [1])

    def test_stop_current_job_noop_when_idle(self):
        from novel_studio.controllers.novel_controller import NovelController

        controller = NovelController()
        controller.ai_service = SimpleNamespace(abort=lambda: None)
        self.assertFalse(controller.stop_current_job())


class TestAIServiceAbortWiring(unittest.TestCase):
    def test_set_services_wires_cancel_and_abort(self):
        """set_services가 ai_service.set_cancel_handler에 토큰/abort를 전달한다."""
        from novel_studio.controllers.novel_controller import NovelController

        received = {}

        class _FakeAI:
            def set_cancel_handler(self, cancel_check, abort_handler=None):
                received["cancel"] = cancel_check
                received["abort"] = abort_handler
                return abort_handler

            def abort(self):
                pass

        controller = NovelController()
        controller.set_services({"ai": _FakeAI()})
        self.assertIn("cancel", received)
        self.assertTrue(callable(received["cancel"]))
        # 취소 요청을 세우면 전달된 검사 함수가 True를 반환한다.
        controller._cancel_token.set()
        self.assertTrue(received["cancel"]())


if __name__ == '__main__':
    unittest.main()