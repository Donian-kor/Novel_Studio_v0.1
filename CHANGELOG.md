## v1.4.0 — Stabilization Release

### 핵심 안정화
- SQLite FTS5 자동 인덱싱을 실제 저장 경로에 연결하고 프로젝트 열기 시 누락 인덱스를 자동 복구
- Retrieval Engine의 검색 결과를 실제 AI 컨텍스트에 통합해 채팅의 중복 DB 검색 제거
- 엔티티 상태 원장을 인물/세계관 단위로 실제 갱신하고 컨텍스트에 공급
- 채팅 시 최근 대화 이력을 AI 요청에 포함
- 집필 후 글자 수 보정 최대 3회 제한
- 원고 저장을 임시 파일 + 원자 교체 방식으로 변경하고 이전 원고 백업 자동 생성
- Anthropic temperature/top_p 반영 및 SSE 스트리밍 구현
- Master Diff JSON 펜스/설명문 파싱 강화
- DB schema version 기록 추가
- pytest 기준 전체 테스트 실행 체계 정리
- 잘못된 로그 경로 수정

### 코드 정리 및 성능
- 죽은 파일 삭제: `core/settings.py`, `ui/views/sections.py`, `ui/views/dashboard.py`, `ui/views/idea.py` 및 대응 폼/`.ui` 6종
- [프로젝트] 메뉴에 "전체 원고 내보내기" 추가 — `exports/` 폴더를 실제로 사용
- 화 목록/플롯/구간 리스트를 `insertItems` 일괄 삽입으로 변경하고 뷰 선택 시 전체 재조회 제거(캐시 사용)

## v1.3.1

### Critical fixes
- 수정된 Qt `.ui` 레이아웃의 잘못된 중첩으로 인한 신규 버튼 로드 실패 가능성 제거
- `AI 구간별 플롯 생성`의 tuple/dict 접근 오류 수정
- 구간별 플롯 생성 결과 범위 검증 추가
- 구간별 플롯 생성을 백그라운드 Job으로 실행해 UI 프리즈 방지
- AI 아이디어/마스터/핵심 기준/전체 플롯 재생성 시 기존 텍스트 누적 방지
- AI 채팅은 기존 대화 로그를 유지하도록 스트리밍 교체 동작 예외 처리

# CHANGELOG

## v1.3.0 — Long-form Story Intelligence 통합
- 복선 이력(`foreshadow_events`) 추가
- 화별 엔티티 상태 원장(`entity_state_ledger`) 추가
- 현재 화 중심 Retrieval Engine 추가
- Master 변경 Diff 제안 기록 추가
- 화별 플롯을 25화 단위로 나누는 계층형 배치 생성 추가
- 장편 정밀 연속성 검사 및 장기 기억 수동 갱신 추가
- SQLite FTS5 검색을 실제 `search()` 경로에 연결하고 실패 시 LIKE fallback 제공
- 마우스 기반 글꼴/글자 크기/색상 설정 UI(v1.2.3) 유지
- `CHANGELOG_v*.md` 파일을 만들지 않고 단일 `CHANGELOG.md`만 누적 관리

## v1.2.2 — 계층형 Section / Arc Memory

### 핵심
- 화별 기억(`chapter_states`) 위에 스토리 구간 장기 기억(`section_memories`)을 추가했습니다.
- 전체 작품을 매번 읽지 않고 현재 구간의 압축 기억을 AI 컨텍스트에 주입합니다.
- 작품을 5개 아크로 균등 분할해 아크 장기 기억(`arc_memories`)을 저장할 수 있습니다.
- 구간 종료 시 Section Memory, 아크 종료 시 Arc Memory를 자동 갱신해 상위 기억의 호출 빈도를 제한합니다.
- Section/Arc Memory에는 생성에 사용한 원천 데이터의 SHA-256 해시를 저장합니다.
- 기존 `story_sections.snapshot`, `summaries`, `chapter_states`는 호환성을 위해 유지합니다.

### 컨텍스트 구조
- Contract / Master Plan
- Master Plot
- 현재 화 플롯
- 현재 Story Section + Section Snapshot
- Section Long-term Memory
- Arc Long-term Memory
- 최근 화별 Summary / 직전 Chapter State / 전 화 원고 tail
- 설정 DB의 제한 조회 데이터

### 문서 정책
- 버전별 `CHANGELOG_v*.md` 파일을 사용하지 않고 이 `CHANGELOG.md` 하나만 누적 관리합니다.
- 다음 버전도 새 파일을 만들지 않고 이 문서에 상단에 계속 추가합니다.

## v1.2.1 — Chapter State
- `chapter_states` 테이블 추가
- 화별 확정 상태를 요약과 별도의 장기 메모리 레이어로 저장
- AI 집필 완료 후 Chapter State 자동 갱신
- 직전 확정 Chapter State를 다음 화의 상태 추출에 참고
- 현재 화 집필 컨텍스트에 가장 최근 확정 Chapter State 주입
- 원고 해시 저장

## v1.2.0 — DB 조회 최적화
- 범위/페이지 조회 API 추가
- 대시보드 COUNT/SUM 집계
- 주요 조회 인덱스 추가
- AI 컨텍스트/검색의 무제한 전체 조회 축소

## v1.1.4 — 글자수 표시 중복 수정
- 메인 화면 하단 중복 글자수 표시 제거
- 원고 화면의 글자수 표시만 유지

## v1.1.3 — 설정 DB CRUD 정상화
- 설정 DB 추가/AI 생성/저장/삭제 버튼 연결
- 직접 수정 후 DB 갱신

## v1.1.2 — 도움말/README 개편
- 실제 UI 동작 기준 도움말 개편
- GitHub README 갱신

## v1.1.1 — 장편 집필 안정화
- 마스터 기획 기반 설정 자동 동기화
- 설정 DB/화별 플롯/원고 분할바 지원

## v1.1 — 화별 플롯 생성 안정화
- 다양한 화 헤더 파싱
- 누락 화 검증 및 1회 보완
- 5000화 입력 지원
- Plan Contract 잠금
