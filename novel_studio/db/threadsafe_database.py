"""프로젝트 DB의 단일 연결을 직렬화하는 스레드 안전 래퍼."""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from novel_studio.db.database import Database as BaseDatabase


class ThreadSafeDatabase:
    """기존 Database API를 유지하면서 모든 DB 호출을 하나의 락으로 직렬화한다."""

    def __init__(
        self,
        path: str | Path,
        max_retries: int = 5,
        base_delay: float = 0.1,
        max_delay: float = 5.0,
    ) -> None:
        self.path = Path(path)
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._lock = threading.RLock()
        self._base = BaseDatabase(self.path)
        self.conn = self._base.conn

    def __getattr__(self, name: str) -> Any:
        base = object.__getattribute__(self, "_base")
        attr = getattr(base, name)
        if not callable(attr):
            return attr

        def locked_method(*args, **kwargs):
            with self._lock:
                return attr(*args, **kwargs)

        return locked_method

    def execute(self, sql: str, args=()):
        """쓰기 SQL을 직렬화하고 즉시 커밋한다."""
        with self._lock:
            cursor = self.conn.execute(sql, args)
            self.conn.commit()
            return cursor

    def close(self) -> None:
        with self._lock:
            self._base.close()
