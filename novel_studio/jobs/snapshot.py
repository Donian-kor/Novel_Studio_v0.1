"""AI 작업 중간 결과를 프로젝트 디스크에 안전하게 보존하는 스냅샷 저장소."""
from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AISnapshotStore:
    """AI 비동기 작업의 중간/최종 결과를 파일로 보존한다.

    UI 생명주기와 분리되어 있으므로 화면을 전환하거나 편집 위젯을 다시
    로드해도 작업 결과 자체는 프로젝트 디스크에 남는다.
    """

    def __init__(self, project_root: str | Path) -> None:
        self.root = Path(project_root) / "temp" / "ai_snapshots"
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _path(self, job_id: str) -> Path:
        return self.root / f"{job_id}.json"

    def start(self, kind: str, target: Any = None, content: str = "") -> str:
        job_id = uuid.uuid4().hex
        payload = {
            "job_id": job_id,
            "kind": str(kind),
            "target": target,
            "status": "running",
            "created_at": self._now(),
            "updated_at": self._now(),
            "content": content or "",
        }
        self._write(job_id, payload)
        return job_id

    def update(self, job_id: str, content: str, **fields: Any) -> None:
        with self._lock:
            current = self.read(job_id) or {"job_id": job_id}
            current.update(fields)
            current["content"] = content or ""
            current["status"] = current.get("status") or "running"
            current["updated_at"] = self._now()
            self._write(job_id, current)

    def finish(self, job_id: str, status: str, content: str | None = None, **fields: Any) -> None:
        with self._lock:
            current = self.read(job_id) or {"job_id": job_id}
            if content is not None:
                current["content"] = content
            current.update(fields)
            current["status"] = status
            current["updated_at"] = self._now()
            self._write(job_id, current)

    def read(self, job_id: str) -> dict[str, Any] | None:
        path = self._path(job_id)
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None

    def _write(self, job_id: str, payload: dict[str, Any]) -> None:
        path = self._path(job_id)
        tmp = path.with_suffix(path.suffix + ".tmp")
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        with self._lock:
            tmp.write_text(text, encoding="utf-8")
            os.replace(tmp, path)
