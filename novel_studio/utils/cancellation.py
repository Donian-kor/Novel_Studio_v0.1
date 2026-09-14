"""백그라운드 작업의 협력적 취소를 위한 공용 토큰.

- ``CancelToken``: 작업 단위/앱 단위 취소 플래그(스레드 안전).
- ``cancelled_check``: 주기적으로 불러 취소 여부를 확인하는 함수를 만든다.

모든 AI I/O(provider 읽기, retry 대기, 순차 생성 경계)는 이 토큰을 통해
정지 버튼 = "연결 끊기 + 다음 호출 차단"을 실현한다.
"""
from __future__ import annotations

import threading
from typing import Callable, Optional


class CancelToken:
    """스레드 안전한 취소 토큰.

    - ``set()``: 취소 요청. 한 번 세우면 재사용 전까지 유지된다.
    - ``reset()``: 새 작업을 시작할 때 사용한 토큰을 초기화한다.
      reset 직후 다른 스레드가 다시 set()한 경우를 보호하기 위해
      반환값으로 "정말 초기화됨" 여부를 돌려준다.
    - ``check()``: 취소 요청 여부. I/O 폴링과 순차 생성 경계에서 호출한다.
    """

    def __init__(self) -> None:
        self._evt = threading.Event()

    def set(self) -> None:
        self._evt.set()

    def is_set(self) -> bool:
        return self._evt.is_set()

    def check(self) -> bool:
        """취소 요청이 있었는지 반환한다(폴링용)."""
        return self._evt.is_set()

    def reset(self) -> bool:
        """초기화한다. reset() 전에 이미 취소 요청이 있었으면 False를
        돌려주므로 호출자는 이 토큰이 여전히 취소 상태인지 알 수 있다."""
        return self._evt.clear()


def cancelled_check(token: Optional[CancelToken], default: bool = False) -> Callable[[], bool]:
    """토큰이 없으면 항상 False(또는 default)를 반환하는 검사 함수를 만든다."""
    if token is None:
        return lambda: default

    def _check() -> bool:
        return token.is_set()

    return _check