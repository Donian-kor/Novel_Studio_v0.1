"""로깅 설정 모듈.

애플리케이션 전체에서 일관된 로그 형식을 사용하기 위한 헬퍼.
"""
from __future__ import annotations

import logging
from pathlib import Path


def setup_logging(level: int = logging.INFO) -> None:
    """기본 로깅 설정을 적용한다 (콘솔 + 프로젝트 루트의 logs/app.log)."""
    fmt = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return
    root.setLevel(level)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    root.addHandler(sh)
    try:
        log_dir = Path(__file__).resolve().parents[1] / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_dir / 'app.log', encoding='utf-8')
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except Exception:
        pass
