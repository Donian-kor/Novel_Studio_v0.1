import pytest

pytest.importorskip("PySide6")
# -*- coding: utf-8 -*-
"""정지 버튼 즉시 중단: 취소 토큰 / 재시도 대기 / worker 회귀 테스트."""
import os
import threading
import time
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from novel_studio.jobs.worker import Job, JobCancelled
from novel_studio.utils.cancellation import CancelToken, cancelled_check
from novel_studio.utils.retry import retry_stream_with_backoff, retry_with_backoff


class TestCancelToken(unittest.TestCase):
    def test_token_set_reset_check(self):
        token = CancelToken()
        self.assertFalse(token.is_set())
        token.set()
        self.assertTrue(token.is_set())
        self.assertTrue(token.check())
        token.reset()
        self.assertFalse(token.is_set())

    def test_cancelled_check_without_token_returns_false(self):
        check = cancelled_check(None)
        self.assertFalse(check())


class TestRetryCancel(unittest.TestCase):
    def test_retry_with_backoff_aborts_sleep_on_cancel(self):
        """재시도 대기 중 취소되면 즉시 JobCancelled를 발생시키고 재시도하지 않는다."""
        attempts = []

        def flaky():
            attempts.append(1)
            raise ConnectionError("일시적 네트워크 오류")

        token = CancelToken()

        def cancel_later():
            time.sleep(0.05)
            token.set()

        threading.Thread(target=cancel_later, daemon=True).start()

        deco = retry_with_backoff(
            max_retries=3, base_delay=2.0, max_delay=60.0,
            retryable_exceptions=(Exception,),
            cancel_check=lambda: token.is_set(),
        )
        try:
            deco(flaky)()
        except JobCancelled:
            # 대기 중 취소 → 재시도 자체가 진행되지 않아 1회만 시도된다.
            self.assertEqual(len(attempts), 1)
            return
        except Exception:
            pass
        self.fail("취소 대기 중 JobCancelled가 발생해야 한다.")

    def test_retry_stream_aborts_sleep_on_cancel(self):
        token = CancelToken()

        def gen():
            # 첫 청크가 나오기 전에 실패 → 스트림 재시도 대기 구간에 진입한다.
            raise ConnectionError("stream 오류")
            yield  # noqa (제너레이터로 유지)

        deco = retry_stream_with_backoff(
            max_retries=3, base_delay=2.0, max_delay=60.0,
            retryable_exceptions=(Exception,),
            cancel_check=lambda: token.is_set(),
        )

        def cancel_later():
            time.sleep(0.05)
            token.set()

        threading.Thread(target=cancel_later, daemon=True).start()
        g = deco(gen)()
        try:
            next(g)
        except JobCancelled:
            return
        self.fail("스트림 재시도 대기 중 취소 시 JobCancelled가 발생해야 한다.")


class TestJobWorker(unittest.TestCase):
    def test_job_raises_cancelled_emits_cancelled_signal(self):
        """worker의 fn()이 JobCancelled를 던지면 cancelled 시그널이 방출된다."""
        events = []

        def fn():
            raise JobCancelled()

        job = Job(fn)
        job.signals.cancelled.connect(lambda: events.append("cancelled"))
        job.signals.error.connect(lambda e: events.append(f"error:{e}"))
        job.signals.finished.connect(lambda r: events.append("finished"))
        job.run()
        self.assertEqual(events, ["cancelled"])

    def test_job_normal_error_emits_error_signal(self):
        events = []

        def fn():
            raise ValueError("실패")

        job = Job(fn)
        job.signals.cancelled.connect(lambda: events.append("cancelled"))
        job.signals.error.connect(lambda e: events.append("error"))
        job.run()
        self.assertEqual(events, ["error"])


if __name__ == '__main__':
    unittest.main()