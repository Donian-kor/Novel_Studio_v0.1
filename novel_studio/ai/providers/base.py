from __future__ import annotations

import urllib.error
from abc import ABC, abstractmethod

from novel_studio.utils.retry import NETWORK_RETRY_EXCEPTIONS, retry_stream_with_backoff, retry_with_backoff


class ProviderError(RuntimeError):
    """AI Provider 공통 예외."""


class AIProvider(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def _chat_impl(self, messages, *, temperature, top_p, max_tokens, timeout=None):
        ...

    @abstractmethod
    def _chat_stream_impl(self, messages, *, temperature, top_p, max_tokens, timeout=None):
        ...

    def _is_retryable_error(self, error: Exception) -> bool:
        if isinstance(error, urllib.error.HTTPError):
            if error.code == 429 or 500 <= error.code < 600:
                return True
            if 400 <= error.code < 500:
                return False
        return isinstance(error, (TimeoutError, ConnectionError, OSError, urllib.error.URLError))

    def _get_retry_after(self, error: Exception) -> float | None:
        headers = getattr(error, "headers", None)
        if headers and "Retry-After" in headers:
            try:
                return float(headers["Retry-After"])
            except (TypeError, ValueError):
                return None
        return None

    def _retry_config(self):
        return {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 60.0,
            "exponential_base": 2.0,
            "jitter": 0.1,
            "retryable_exceptions": NETWORK_RETRY_EXCEPTIONS,
        }

    def chat(self, messages, *, temperature, top_p, max_tokens, timeout=None):
        config = self._retry_config()
        return retry_with_backoff(**config)(self._chat_impl)(
            messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            timeout=timeout,
        )

    def chat_stream(self, messages, *, temperature, top_p, max_tokens, timeout=None):
        """스트리밍 미지원 Provider는 전체 결과를 한 덩어리로 반환한다."""
        config = self._retry_config()
        stream_impl = self._stream_retry_decorator(self._chat_stream_impl, config)
        yield from stream_impl(
            messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            timeout=timeout,
        )

    def _stream_retry_decorator(self, func, config=None):
        cfg = config or self._retry_config()
        return retry_stream_with_backoff(**cfg)(func)

    def list_models(self):
        return []

    def quick_test(self):
        return self.chat(
            [{"role": "user", "content": "Reply with exactly: 연결 테스트 성공"}],
            temperature=0.1,
            top_p=0.9,
            max_tokens=32,
            timeout=15,
        )

    def test(self):
        return self.quick_test()
