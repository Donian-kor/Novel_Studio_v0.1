"""프로젝트 DB의 단일 연결을 직렬화하는 스레드 안전 래퍼."""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from novel_studio.db.sqlite_storage import SQLiteStorage


class ThreadSafeDatabase:
    """SQLiteStorage를 감싸 모든 DB 호출을 하나의 락으로 직렬화한다."""

    def __init__(
        self,
        path: str | Path,
        max_retries: int = 5,
        base_delay: float = 0.1,
        max_delay: float = 5.0,
        profile: str | None = None,
    ) -> None:
        self.path = Path(path)
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._lock = threading.RLock()
        self.profile = profile
        self._base = SQLiteStorage(self.path, profile=profile)
        self.conn = self._base.conn
        self._closed = False

    def __getattr__(self, name: str) -> Any:
        base = object.__getattribute__(self, "_base")
        attr = getattr(base, name)
        if not callable(attr):
            return attr

        def locked_method(*args, **kwargs):
            with self._lock:
                return attr(*args, **kwargs)

        return locked_method

    def table_exists(self, name: str) -> bool:
        return self._base._table_exists(name)

    def execute(self, sql: str, args=()):
        """쓰기 SQL을 직렬화하고 즉시 커밋한다."""
        with self._lock:
            cursor = self.conn.execute(sql, args)
            self.conn.commit()
            return cursor

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._base.close()
            self.conn = None
            self._closed = True

    def __enter__(self):
        if self._closed:
            raise RuntimeError("이미 닫힌 데이터베이스입니다.")
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
