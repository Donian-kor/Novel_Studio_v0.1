"""버전 정보 유틸리티"""

import os
from pathlib import Path


def get_version() -> str:
    """버전 정보를 version.txt에서 읽어 반환합니다.
    
    Returns:
        str: 버전 문자열 (예: "1.4.1"). 파일을 읽을 수 없으면 "0.0.0"을 반환합니다.
    """
    # 현재 파일의 위치를 기준으로 프로젝트 루트를 찾습니다.
    # novel_studio/utils/version.py -> novel_studio/ -> 프로젝트 루트
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent  # novel_studio/utils/version.py -> novel_studio/utils -> novel_studio -> 프로젝트 루트
    version_file = project_root / "version.txt"
    
    try:
        return version_file.read_text(encoding="utf-8").strip()
    except Exception:
        # 파일을 읽을 수 없는 경우 기본 버전 반환
        return "0.0.0"