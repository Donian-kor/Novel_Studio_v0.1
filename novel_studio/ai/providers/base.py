from __future__ import annotations

import socket
import threading
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from contextlib import contextmanager

from novel_studio.utils.cancellation import JobCancelled
from novel_studio.utils.retry import NETWORK_RETRY_EXCEPTIONS, retry_stream_with_backoff, retry_with_backoff

# 서버의 기본 빠른 연결 테스트에만 사용한다.
CONNECT_TIMEOUT = 1.0

# 취소는 별도 abort()로 처리하므로 스트리밍 read timeout을 두지 않는다.
CANCEL_POLL_INTERVAL = 1.0

# AI 추론 + 응답 대기를 허용하는 전체 요청 시간(초).
# 이 값 동안 첫 토큰이 오지 않아도 정상적인 장기 추론으로 간주한다.
DEFAULT_CHAT_TIMEOUT = 1800


def _post_connect_timeout(sock, timeout):
    """연결 후 소켓의 읽기 timeout을 설정한다. 짧은 값은 무제한으로 완화한다."""
    try:
        value = None if timeout is None or float(timeout) <= CONNECT_TIMEOUT else float(timeout)
        sock.settimeout(value)
    except Exception:
        pass


def _shutdown_underlying_socket(resp) -> None:
    """차단된 recv/readline을 깨우기 위해 하위 소켓을 shutdown 한다(best-effort).

    ``HTTPResponse.close()``만으로는 플랫폼에 따라 블로킹 중인 read가
    풀리지 않을 수 있어(Linux 등), 원시 소켓에 SHUT_RDWR을 시도한다.
    Windows에서는 close()만으로도 대기 중인 읽기가 풀린다.
    """
    for _ in range(2):  # fp 래퍼 단계가 구현마다 달라 최대 2단계까지 파고든다.
        try:
            sock = getattr(resp, "fp", None)
            if sock is None:
                return
            raw = getattr(sock, "raw", None)
            target = raw if raw is not None else sock
            inner = getattr(target, "_sock", None)
            if inner is not None:
                target = inner
            shutdown = getattr(target, "shutdown", None)
            if callable(shutdown):
                try:
                    shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                return
            # 더 깊이 들어갈 속성이 없으면 중단한다.
            if raw is None and inner is None:
                return
            resp = target
        except Exception:
            return


class ProviderError(RuntimeError):
    """AI Provider 공통 예외."""


class AIProvider(ABC):
    def __init__(self, config, cancel_check=None, abort_handler=None):
        self.config = config
        # 정지 버튼과 연결되는 취소 훅. provider()가 생성 시 주입한다.
        self.cancel_check = cancel_check or (lambda: False)
        self._abort_handler = abort_handler
        # 작업 중 응답 핸들을 보관해 다른 스레드(UI)에서 abort할 수 있게 한다.
        self._active_response = None
        self._active_lock = threading.Lock()

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

    def _interrupted(self) -> bool:
        """현재 작업이 취소 요청되었는지(네트워크 오류인지 취소 오류인지 구분)."""
        try:
            return bool(self.cancel_check and self.cancel_check())
        except Exception:
            return False

    def abort(self) -> None:
        """진행 중인 HTTP 응답을 닫아 대기 중인 read/readline을 즉시 풀어준다."""
        with self._active_lock:
            resp, self._active_response = self._active_response, None
        if resp is not None:
            # 소켓 shutdown을 먼저 시도해 recv/readline 대기를 깨운 뒤 close 한다.
            # 주의: self._abort_handler는 호출하지 않는다. ProviderManager가
            # 정지 시 abort_handler로 ai_service.abort(=providers.abort)를
            # 넘기면, 다시 이 abort()로 돌아오는 무한 재귀가 되기 때문이다.
            _shutdown_underlying_socket(resp)
            if hasattr(resp, "close"):
                try:
                    resp.close()
                except Exception:
                    pass

    def _check_urlopen(self, req, timeout):
        """HTTP 연결과 첫 응답을 하나의 장기 timeout으로 처리한다.

        ``urllib.request.urlopen(timeout=1)``은 TCP connect뿐 아니라 응답 헤더를
        기다리는 동안에도 적용되므로, LM Studio가 긴 추론을 수행하면 첫 토큰 전에
        timeout이 발생할 수 있다. AI 요청에서는 전달된 전체 timeout(기본 1800초)을
        사용하고, 연결 후 소켓 read timeout은 별도로 설정하지 않는다.
        """
        if timeout is None or float(timeout) <= CONNECT_TIMEOUT:
            timeout = DEFAULT_CHAT_TIMEOUT
        if self._interrupted():
            self.abort()
            raise JobCancelled()
        try:
            # 서버가 꺼져 있으면 connection refused가 즉시 발생하고,
            # 서버가 켜져 있으면 긴 추론/첫 토큰 대기까지 timeout을 보장한다.
            return urllib.request.urlopen(req, timeout=float(timeout))
        except (TimeoutError, socket.timeout) as e:
            if self._interrupted():
                raise JobCancelled() from e
            raise
        except OSError as e:
            if self._interrupted():
                raise JobCancelled() from e
            raise

    def _set_read_timeout(self, resp, timeout):
        """응답 소켓의 읽기 타임아웃을 설정한다 (取消 폴링용)."""
        try:
            sock_timeout = getattr(resp, "fp", None)
            raw = getattr(sock_timeout, "raw", None) if sock_timeout is not None else None
            raw_sock = getattr(raw, "_sock", None) if raw is not None else None
            target = raw_sock if raw_sock is not None else raw
            if target is not None and hasattr(target, "settimeout"):
                target.settimeout(timeout)
        except Exception:
            pass

    @contextmanager
    def _open_response(self, resp):
        """응답 핸들을 활성 목록에 등록하고, with 종료 시 해제한다(컨텍스트 매니저)."""
        with self._active_lock:
            self._active_response = resp
        try:
            yield resp
        finally:
            with self._active_lock:
                if self._active_response is resp:
                    self._active_response = None

    def _read_json(self, resp):
        """응답 전체를 청크 단위로 읽되 매 청크마다 취소를 확인한다.

        취소로 인해 응답이 닫혀 읽기가 실패했으면 ``JobCancelled``로 바꾸어
        네트워크 오류로 오인한 재시도를 차단한다.
        """
        chunks = []
        read1 = getattr(resp, "read1", None)
        while True:
            if self._interrupted():
                self.abort()
                raise JobCancelled()
            try:
                chunk = read1(8192) if callable(read1) else resp.read(8192)
            except (TimeoutError, socket.timeout) as e:
                if self._interrupted():
                    raise JobCancelled() from e
                continue
            except Exception as e:
                if self._interrupted():
                    raise JobCancelled() from e
                raise
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)

    def _readline_cancelable(self, resp):
        """스트리밍 한 줄을 읽는다. 첫 토큰까지는 timeout 없이 기다린다.

        사용자가 정지하면 ``abort()``가 활성 응답 소켓을 shutdown/close 하여
        블로킹 read를 깨운다. timed-out BufferedReader에 다시 readline()을
        호출하는 기존 폴링 방식은 ``cannot read from timed out object``를 만들 수
        있으므로 사용하지 않는다.
        """
        if self._interrupted():
            self.abort()
            raise JobCancelled()
        try:
            return resp.readline()
        except (TimeoutError, socket.timeout, OSError) as e:
            if self._interrupted():
                raise JobCancelled() from e
            raise
        except Exception as e:
            if self._interrupted():
                raise JobCancelled() from e
            raise

    def _retry_config(self):
        return {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 60.0,
            "exponential_base": 2.0,
            "jitter": 0.1,
            "retryable_exceptions": NETWORK_RETRY_EXCEPTIONS,
            "cancel_check": self.cancel_check,
        }

    def chat(self, messages, *, temperature, top_p, max_tokens, timeout=None):
        if timeout is None:
            timeout = DEFAULT_CHAT_TIMEOUT
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
        if timeout is None:
            timeout = DEFAULT_CHAT_TIMEOUT
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