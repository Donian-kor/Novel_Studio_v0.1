# -*- coding: utf-8 -*-
"""정지 버튼 즉시 중단: provider abort / 메모리 경계 / controller 배선 테스트."""
import json
import os
import threading
import time
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
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


class TestBlockingCancel(unittest.TestCase):
    """블로킹 chat() 경로의 정지: TTFB 대기·본문 읽기·스트림 폴백."""

    def _run_http_server(self, handler_cls):
        server = HTTPServer(('127.0.0.1', 0), handler_cls)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, f'http://127.0.0.1:{server.server_address[1]}'

    def test_check_urlopen_cancelled_during_slow_ttfb(self):
        """첫 바이트가 늦게 오는 서버에서도 정지가 3초 안에 먹는다."""
        from novel_studio.ai.providers.openai_compatible import (
            OpenAICompatibleProvider,
        )

        class _SlowTTFB(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get('Content-Length') or 0)
                self.rfile.read(length)
                time.sleep(10)  # 헤더 지연: 기존 urlopen(timeout=1800)은 10초 대기
                body = json.dumps(
                    {'choices': [{'message': {'content': '늦은 응답'}}]}
                ).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, *args):
                pass

        server, base = self._run_http_server(_SlowTTFB)
        try:
            state = {'cancel': False}
            provider = OpenAICompatibleProvider(
                {'base_url': base, 'model': 'm'},
                cancel_check=lambda: state['cancel'],
            )

            def _blocking_chat():
                try:
                    return provider._chat_impl(
                        [{'role': 'user', 'content': 'hi'}],
                        temperature=0.1, top_p=0.9, max_tokens=32, timeout=30,
                    )
                except JobCancelled:
                    return 'cancelled'

            thread = threading.Thread(target=_blocking_chat, daemon=True)
            started = time.monotonic()
            thread.start()
            time.sleep(0.3)
            state['cancel'] = True
            provider.abort()
            thread.join(timeout=10)
            elapsed = time.monotonic() - started
            self.assertFalse(thread.is_alive())
            # 전체 timeout(30초)을 기다리지 않고 3초 안에 풀려야 한다.
            self.assertLess(elapsed, 3.0)
        finally:
            server.shutdown()
            server.server_close()

    def test_chat_prefers_cancelable_stream(self):
        """chat()은 스트림 누적을 먼저 시도하고 같은 문자열을 돌려준다."""
        from novel_studio.ai.providers.openai_compatible import (
            OpenAICompatibleProvider,
        )

        provider = OpenAICompatibleProvider(
            {'base_url': 'http://127.0.0.1:1', 'model': 'm'})
        calls = []

        def _fake_stream(messages, *, temperature, top_p, max_tokens, timeout=None):
            calls.append('stream')
            yield '안'
            yield '녕'

        provider._chat_stream_impl = _fake_stream
        out = provider.chat(
            [{'role': 'user', 'content': 'hi'}],
            temperature=0.1, top_p=0.9, max_tokens=32, timeout=30,
        )
        self.assertEqual(out, '안녕')
        self.assertEqual(calls, ['stream'])

    def test_chat_falls_back_when_stream_unsupported(self):
        """chat()은 스트림 미지원 표시일 때만 블로킹으로 폴백한다."""
        from novel_studio.ai.providers.openai_compatible import (
            OpenAICompatibleProvider,
        )

        provider = OpenAICompatibleProvider(
            {'base_url': 'http://127.0.0.1:1', 'model': 'm'})

        def _broken_stream(*a, **kw):
            raise RuntimeError('stream unsupported')

        provider._chat_stream_impl = _broken_stream
        provider._chat_impl = lambda *a, **kw: '폴백 응답'
        out = provider.chat(
            [{'role': 'user', 'content': 'hi'}],
            temperature=0.1, top_p=0.9, max_tokens=32, timeout=30,
        )
        self.assertEqual(out, '폴백 응답')

    def test_chat_cancelled_during_stream_is_not_retried_as_error(self):
        """스트림 누적 중 취소는 JobCancelled로 끝나고 재시도되지 않는다."""
        from novel_studio.ai.providers.openai_compatible import (
            OpenAICompatibleProvider,
        )

        state = {'cancel': False}
        provider = OpenAICompatibleProvider(
            {'base_url': 'http://127.0.0.1:1', 'model': 'm'},
            cancel_check=lambda: state['cancel'],
        )

        def _slow_stream(*a, **kw):
            yield '조각'
            state['cancel'] = True
            # 다음 토큰 확인 시 취소가 감지된다.
            yield '뒤늦은 조각'

        provider._chat_stream_impl = _slow_stream
        with self.assertRaises(JobCancelled):
            provider.chat(
                [{'role': 'user', 'content': 'hi'}],
                temperature=0.1, top_p=0.9, max_tokens=32, timeout=30,
            )


if __name__ == '__main__':
    unittest.main()