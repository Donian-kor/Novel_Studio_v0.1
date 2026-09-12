from __future__ import annotations
from pathlib import Path
from novel_studio.core.project import ProjectManager
from novel_studio.db.database import Database


class SettingsManager:
    """프로젝트 설정을 관리하는 헬퍼 클래스"""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.pm = ProjectManager()
        self.db_path = self.project_root / "novel.db"
        self.db = None

    def open(self):
        """프로젝트를 열고 데이터베이스 연결"""
        self.pm.open(self.project_root)
        self.db = Database(self.db_path)
        return self

    def close(self):
        """데이터베이스 연결 종료"""
        if self.db:
            self.db.close()
            self.db = None

    @property
    def settings(self):
        """프로젝트 설정 반환"""
        return self.pm.settings

    def get_meta(self, key: str, default: str = "") -> str:
        """메타 데이터 조회"""
        if not self.db:
            return default
        row = self.db.get_meta(key)
        return row["value"] if row else default

    def set_meta(self, key: str, value: str):
        """메타 데이터 저장"""
        if self.db:
            self.db.set_meta(key, value)

    def get_plan(self) -> str:
        """마스터 플랜 조회"""
        if not self.db:
            return ""
        row = self.db.get_plan()
        return row["content"] if row else ""

    def save_plan(self, content: str):
        """마스터 플랜 저장"""
        if self.db:
            self.db.save_plan(content)

    def chapter_list(self):
        """화 목록 조회"""
        if not self.db:
            return []
        return self.db.chapters()

    def current_chapter(self) -> int:
        """현재 작업 중인 화 번호 (기본값 1)"""
        return 1
