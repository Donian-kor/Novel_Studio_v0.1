"""
공통 재시도 유틸리티 - 지수 백오프 + 지터
"""
import time
import random
import logging
from functools import wraps
from typing import Callable, Type, Tuple, Optional, Any

from novel_studio.utils.cancellation import JobCancelled

logger = logging.getLogger(__name__)

# 취소 대기 응답성을 위한 대기 조각 크기(초)
CANCEL_POLL_INTERVAL = 0.2


def is_retryable_error(exception: Exception, retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)) -> bool:
    """예외가 재시도 가능한지 판단합니다."""
    # 사용자 취소는 어떤 경우에도 재시도하지 않는다 (취소 후 작업 부활 방지).
    if isinstance(exception, JobCancelled):
        return False
    if not isinstance(exception, retryable_exceptions):
        return False

    # HTTPError인 경우 상태 코드 확인
    if hasattr(exception, 'code'):
        code = exception.code
        # 429 (Too Many Requests), 5xx 서버 에러만 재시도
        if code == 429 or 500 <= code < 600:
            return True
        # 4xx 클라이언트 에러는 재시도 안 함 (401, 403 등 인증 오류 포함)
        if 400 <= code < 500:
            return False

    # urllib.error.URLError, timeout 등 네트워크 에러는 재시도
    if isinstance(exception, (TimeoutError, ConnectionError, OSError)):
        return True

    logger.debug(f"재시도 가능 여부 미확인 예외: {exception!r}, 기본 재시도 불가")
    return False


def get_retry_after(exception: Exception) -> Optional[float]:
    """예외에서 Retry-After 헤더 값(초)을 추출합니다."""
    if hasattr(exception, 'headers'):
        headers = exception.headers
        if 'Retry-After' in headers:
            try:
                return float(headers['Retry-After'])
            except (ValueError, TypeError):
                pass
    return None


def _interruptible_sleep(delay: float, cancel_check: Optional[Callable[[], bool]] = None) -> None:
    """취소를 지연 없이 감지하기 위해 대기를 0.2초 조각으로 나눈다.

    취소 요청이 들어오면 즉시 ``JobCancelled``를 발생시켜 수십 초 대기를 끝내고,
    취소 후의 재시도도 원천 차단한다.
    """
    if cancel_check is not None and cancel_check():
        raise JobCancelled()
    deadline = time.monotonic() + max(0.0, delay)
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        if cancel_check is not None and cancel_check():
            raise JobCancelled()
        time.sleep(min(CANCEL_POLL_INTERVAL, remaining))


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: float = 0.1,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
):
    """
    지수 백오프 + 지터 재시도 데코레이터

    Args:
        max_retries: 최대 재시도 횟수 (기본 3회)
        base_delay: 초기 대기 시간(초)
        max_delay: 최대 대기 시간(초)
        exponential_base: 지수 증가 배수
        jitter: 지터 비율 (0.0~1.0)
        retryable_exceptions: 재시도할 예외 타입들
        on_retry: 재시도 시 호출할 콜백 (exception, attempt) -> None
        cancel_check: 취소 여부 판별 함수. True면 대기 없이 즉시 JobCancelled.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # 마지막 시도였으면 예외 발생
                    if attempt >= max_retries:
                        logger.warning(
                            f"{func.__name__} 최대 재시도 횟수({max_retries}) 초과: {e}"
                        )
                        raise

                    # 취소 확인 (재시도 가능 여부와 무관하게 즉시 처리)
                    if cancel_check is not None and cancel_check():
                        raise JobCancelled()

                    # 재시도 가능한 예외인지 확인
                    if not is_retryable_error(e, retryable_exceptions):
                        logger.debug(f"{func.__name__} 재시도 불가 예외: {e}")
                        raise

                    # Retry-After 헤더 확인
                    retry_after = get_retry_after(e)

                    # 대기 시간 계산
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    # 지터 추가 (±jitter%)
                    jitter_range = delay * jitter
                    delay = delay + random.uniform(-jitter_range, jitter_range)
                    delay = max(0, delay)

                    # Retry-After가 있으면 그 값을 우선 사용
                    if retry_after is not None:
                        delay = max(delay, retry_after)

                    logger.warning(
                        f"{func.__name__} 시도 {attempt + 1}/{max_retries + 1} 실패: {e}. "
                        f"{delay:.2f}초 후 재시도..."
                    )

                    if on_retry:
                        on_retry(e, attempt + 1)

                    _interruptible_sleep(delay, cancel_check)

            # 여기 도달하면 안 됨
            raise last_exception

        return wrapper
    return decorator


# 스트리밍용 별도 재시도 (첫 청크 전까지만 재시도)
def retry_stream_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: float = 0.1,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    cancel_check: Optional[Callable[[], bool]] = None,
):
    """스트리밍 함수용 재시도 - 첫 yield 전까지만 재시도"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    # 제너레이터 함수 호출
                    generator = func(*args, **kwargs)
                    first_chunk = True
                    for chunk in generator:
                        if first_chunk:
                            first_chunk = False
                        yield chunk
                    return  # 정상 완료
                except Exception as e:
                    # 첫 청크가 이미 yield된 후면 재시도 안 함
                    if not first_chunk:
                        raise

                    last_exception = e

                    # 취소 확인 (재시도 가능 여부와 무관하게 즉시 처리)
                    if cancel_check is not None and cancel_check():
                        raise JobCancelled()

                    if attempt >= max_retries:
                        logger.warning(f"스트리밍 최대 재시도 횟수 초과: {e}")
                        raise

                    if not is_retryable_error(e):
                        raise

                    retry_after = get_retry_after(e)
                    delay = min(1.0 * (2.0 ** attempt), 60.0)
                    delay = delay + random.uniform(-delay * 0.1, delay * 0.1)
                    delay = max(0, delay)

                    if retry_after is not None:
                        delay = max(delay, retry_after)

                    logger.warning(f"스트리밍 시도 {attempt + 1} 실패: {e}. {delay:.2f}초 후 재시도...")
                    _interruptible_sleep(delay, cancel_check)

            raise last_exception
        return wrapper
    return decorator


# Provider별 재시도 설정
DEFAULT_RETRY_CONFIG = {
    'max_retries': 3,
    'base_delay': 1.0,
    'max_delay': 60.0,
    'exponential_base': 2.0,
    'jitter': 0.1,
    'retryable_exceptions': (Exception,)
}

# 네트워크/HTTP 에러만 재시도하도록 제한
NETWORK_RETRY_EXCEPTIONS = (
    TimeoutError,
    ConnectionError,
    OSError,
    IOError,
)

# HTTPError는 코드별로 판단하므로 별도 처리
try:
    import urllib.error
    NETWORK_RETRY_EXCEPTIONS = NETWORK_RETRY_EXCEPTIONS + (urllib.error.HTTPError, urllib.error.URLError)
except ImportError:
    pass