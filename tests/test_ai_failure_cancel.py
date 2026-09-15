from __future__ import annotations

from novel_studio.utils.cancellation import CancelToken, JobCancelled, cancelled_check
from novel_studio.utils.retry import retry_with_backoff


def test_cancel_token_is_sticky_and_resettable() -> None:
    token = CancelToken()
    assert not token.is_set()
    token.set()
    assert token.is_set()
    token.reset()
    assert not token.is_set()


def test_cancelled_retry_is_interrupted() -> None:
    token = CancelToken()
    token.set()
    attempts: list[int] = []

    def work() -> None:
        attempts.append(1)
        raise RuntimeError("호출되면 안 된다")

    decorated = retry_with_backoff(
        max_retries=3,
        base_delay=0.01,
        max_delay=0.01,
        retryable_exceptions=(Exception,),
        cancel_check=cancelled_check(token),
    )

    try:
        decorated(work)()
    except JobCancelled:
        pass
    else:
        raise AssertionError("취소된 작업은 JobCancelled를 발생시켜야 한다.")

    assert attempts == [1]
