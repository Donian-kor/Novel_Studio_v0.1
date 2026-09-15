"""
서비스 인터페이스 정의 - View와 비즈니스 로직 사이의 계약
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Iterator
from dataclasses import dataclass


@dataclass
class ChapterInfo:
    """화 정보를 저장하는 데이터 클래스."""
    number: int
    title: str
    status: str
    char_count: int
    char_count_spaces: int
    target_chars: int


@dataclass
class EntityState:
    """엔티티 상태를 저장하는 데이터 클래스."""
    kind: str
    entity_key: str
    chapter_number: int
    state: str
    source_hash: str
    updated_at: str


@dataclass
class ContinuityResult:
    """연속성 검사 결과를 저장하는 데이터 클래스."""
    chapter: int
    severity: str
    category: str
    message: str
    evidence: str


class ProjectService(ABC):
    """프로젝트 관리 서비스 계약."""
    
    @abstractmethod
    def get_settings(self) -> dict:
        """프로젝트 설정 반환"""
        pass
    
    @abstractmethod
    def save_settings(self, settings: dict) -> None:
        """프로젝트 설정 저장"""
        pass
    
    @abstractmethod
    def get_chapter_count(self) -> int:
        """총 화수 반환"""
        pass
    
    @abstractmethod
    def get_chapter_info(self, chapter: int) -> Optional[ChapterInfo]:
        """화 정보 조회"""
        pass
    
    @abstractmethod
    def update_chapter(self, chapter: int, title: str, status: str, 
                       char_count: int, char_count_spaces: int, 
                       target_chars: int) -> None:
        """화 정보 업데이트"""
        pass


class AIService(ABC):
    """AI 서비스 계약."""
    
    @abstractmethod
    def generate(self, prompt: str, *, temperature: float = 0.7, 
                 max_tokens: int = 2000, timeout: int = 60) -> str:
        """단일 AI 생성을 수행한다."""
        pass
    
    @abstractmethod
    def generate_stream(self, prompt: str, *, temperature: float = 0.7,
                        max_tokens: int = 2000, timeout: int = 60) -> Iterator[str]:
        """스트리밍 생성 결과를 순차적으로 반환한다."""
        pass
    
    @abstractmethod
    def list_models(self) -> list:
        """사용 가능한 모델 목록을 반환한다."""
        pass


class DatabaseService(ABC):
    """데이터베이스 서비스 계약."""
    
    @abstractmethod
    def get_chapters(self) -> List[ChapterInfo]:
        """전체 화 목록을 조회한다."""
        pass
    
    @abstractmethod
    def get_chapter_content(self, chapter: int) -> str:
        """화 원고를 조회한다."""
        pass
    
    @abstractmethod
    def save_chapter(self, chapter: int, content: str) -> None:
        """화 원고를 저장한다."""
        pass
    
    @abstractmethod
    def get_chapter_story(self, chapter: int) -> Optional[str]:
        """화별 스토리를 조회한다."""
        pass
    
    @abstractmethod
    def save_chapter_story(self, chapter: int, title: str, content: str, status: str) -> None:
        """화별 스토리를 저장한다."""
        pass
    
    @abstractmethod
    def get_continuity_checks(self, chapter: int) -> List[ContinuityResult]:
        """연속성 검사 결과를 조회한다."""
        pass
    
    @abstractmethod
    def add_continuity_check(self, chapter: int, severity: str, 
                             category: str, message: str, evidence: str) -> None:
        """연속성 검사 결과를 저장한다."""
        pass


class ContextService(ABC):
    """컨텍스트 관리 서비스"""
    
    @abstractmethod
    def build_context(self, chapter: int, extra: str = '') -> str:
        """AI 컨텍스트를 구성한다."""
        pass
    
    @abstractmethod
    def get_token_budget(self) -> int:
        """토큰 예산을 조회한다."""
        pass


class SettingsService(ABC):
    """설정 관리 서비스 계약."""
    
    @abstractmethod
    def get_active_provider(self) -> str:
        """활성 Provider ID를 반환한다."""
        pass
    
    @abstractmethod
    def get_provider_config(self, provider_id: str) -> dict:
        """Provider 설정을 조회한다."""
        pass
    
    @abstractmethod
    def save_provider_config(self, provider_id: str, config: dict) -> None:
        """Provider 설정을 저장한다."""
        pass
    
    @abstractmethod
    def get_ai_settings(self) -> dict:
        """AI 설정 전체를 반환한다."""
        pass


class ContinuityService(ABC):
    """연속성 검사 서비스 계약."""
    
    @abstractmethod
    def check_chapter(self, chapter: int, text: str) -> ContinuityResult:
        """단일 화의 연속성을 검사한다."""
        pass
    
    @abstractmethod
    def audit_long_form(self, size: int = 50, 
                        progress_callback=None, 
                        cancelled_check=None) -> str:
        """장편 연속성을 검사한다."""
        pass


class WritingService(ABC):
    """집필과 윤문 서비스 계약."""
    
    @abstractmethod
    def write_chapter(self, chapter: int, stream_callback=None) -> str:
        """화 집필을 수행하고 스트리밍을 지원한다."""
        pass
    
    @abstractmethod
    def revise_chapter(self, text: str) -> str:
        """원고를 윤문한다."""
        pass
    
    @abstractmethod
    def check_consistency(self, chapter: int, text: str) -> str:
        """설정 충돌 검사"""
        pass
    
    @abstractmethod
    def adjust_length(self, text: str, target: int, tolerance: int) -> str:
        """글자 수 보정"""
        pass


class ExportService(ABC):
    """내보내기 서비스"""
    
    @abstractmethod
    def export_manuscript(self) -> str:
        """전체 원고 내보내기 (파일 경로 반환)"""
        pass