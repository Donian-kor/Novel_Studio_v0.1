from abc import ABC, abstractmethod
import urllib.error
from novel_studio.utils.retry import (
    retry_with_backoff,
    retry_stream_with_backoff,
    NETWORK_RETRY_EXCEPTIONS,
    get_retry_after,
    is_retryable_error,
)

# 베이스 에러 클래스 정의
class ProviderError(RuntimeError): 
    pass


class AIProvider(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def _chat_impl(self, messages, *, temperature, top_p, max_tokens, timeout=None): ...

    @abstractmethod
    def _chat_stream_impl(self, messages, *, temperature, top_p, max_tokens, timeout=None): ...

    def _is_retryable_error(self, e: Exception) -> bool:
        """HTTPError의 경우 상태 코드별로 재시도 여부 판단"""
        if isinstance(e, urllib.error.HTTPError):
            code = e.code
            if e.code == 429 or 500 <= e.code < 600:
                return True
            if 400 <= e.code < 500:
                return False
        # 네트워크 관련 예외는 재시도
        import urllib.error
        return isinstance(e, (TimeoutError, ConnectionError, OSError, urllib.error.URLError))

    def _get_retry_after(self, e: Exception) -> float | None:
        """HTTPError에서 Retry-After 헤더 추출"""
        if hasattr(e, 'headers'):
            headers = e.headers
            if 'Retry-After' in headers:
                try:
                    return float(headers['Retry-After'])
                except (ValueError, TypeError):
                    pass
        return None

    def _retry_config(self):
        """기본 재시도 설정 반환"""
        return {
            'max_retries': 3,
            'base_delay': 1.0,
            'max_delay': 60.0,
            'exponential_base': 2.0,
            'jitter': 0.1,
            'retryable_exceptions': (Exception,)
        }

    def _retry_decorator(self, func):
        """동기 메서드용 재시도 데코레이터"""
        from novel_studio.utils.retry import retry_with_backoff
        config = self._retry_config()
        return retry_with_backoff(**config)(func)

    def _stream_retry_decorator(self, func):
        """스트리밍 메서드용 재시도 데코레이터"""
        from novel_studio.utils.retry import retry_stream_with_backoff
        config = self._retry_config()
        return retry_stream_with_backoff(**config)(func)

    def chat(self, messages, *, temperature, top_p, max_tokens, timeout=None):
        return self._retry_decorator(self._chat_impl)(messages, temperature=temperature, top_p=top_p, max_tokens=max_tokens, timeout=timeout)

    def chat_stream(self, messages, *, temperature, top_p, max_tokens, timeout=None):
        return self._stream_retry_decorator(self._chat_stream_impl)(messages, temperature=temperature, top_p=top_p, max_tokens=max_tokens, timeout=timeout)

    def chat_stream(self, messages, *, temperature, top_p, max_tokens, timeout=None):
        """스트리밍 폴백: 스트리밍 미지원 provider는 전체 결과를 한 번에 yield."""
        text = self.chat(messages, temperature=temperature, top_p=top_p,
                         max_tokens=max_tokens, timeout=timeout)
        yield text

    def list_models(self):
        return []

    def quick_test(self):
        """짧은 타임아웃 연결 테스트 (기본 구현)."""
        return self.chat([{"role": "user", "content": "Reply with exactly: 연결 테스트 성공"}], temperature=.1, top_p=.9, max_tokens=32, timeout=15)

    def test(self):
        return self.quick_test()