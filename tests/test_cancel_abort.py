import pytest

pytest.importorskip("PySide6")
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


class TestEndStateServiceCancel(unittest.TestCase):
    def test_cancelled_generation_does_not_persist(self):
        from novel_studio.services.end_state_service import EndStateService
        from novel_studio.utils.cancellation import JobCancelled
        class _AI:
            def cancelled_check(self): return True
            def generate(self, *a, **kw): raise AssertionError('cancelled request must not call AI')
        class _DB:
            def chapter_state(self, n): return None
            def save_chapter_state(self, *a, **kw): raise AssertionError('cancelled request must not persist')
        with self.assertRaises(JobCancelled): EndStateService(_DB(), _AI()).generate(2, '원고')
