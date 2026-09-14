## v1.4.6

- Controller 작업 실행/스트리밍/취소 경로 통합
- 집필·윤문·연속성 검사의 callback 연결 수정
- 장편 정밀 연속성 검사를 Controller → Service 경로로 연결
- 장편 정밀 검사 입력에 화별 플롯·확정 상태·실제 원고를 포함
- Controller 중복 메서드 및 placeholder 제거
- ThreadSafeDatabase의 이중 DB 연결/중복 메서드 제거
- Provider 스트리밍 재시도 설정을 네트워크/HTTP 오류 중심으로 정비
- 스트리밍 취소 시 다음 토큰 수신 지점에서 즉시 중단되도록 보완
- 설정 DB 저장 시 전체 항목 이름이 덮어써지는 버그 수정
- 엔티티 편집 저장 범위를 선택 항목으로 제한하고 이름 변경을 정상 처리
- 확정 저장 전 AI 기억/상태 갱신을 실행하지 않도록 변경
- ServiceFactory를 실제 애플리케이션 구성 경로에 적용
- 버전 표기 1.4.6으로 통일
- DB/재시도 회귀 테스트 추가

# Changelog

## v1.4.5 — entities.ui 버그 수정

### 인물/세력/장소 상세 UI 버그 수정
- `entities.ui` 위젯 레이아웃 문제 수정 (6줄 변경)

---

## v1.4.3 — 설정 DB 개편

### 설정 DB(인물/세력/장소) 상세 기능 개편
- `entities.py` 뷰 로직 재구성 (585줄 변경) — 인물/세력/장소 상세 편집 UI 대폭 개선
- `entities.ui` 레이아웃 갱신 (111줄 변경) — 상세 입력 필드 및 레이아웃 수정
- 데이터 입출력 로직 정비 및 편집/저장/삭제 흐름 재구성

---

## v1.4.2 — 아키텍처 리팩토링 및 안정화

### 서비스 계층 분리
- `NovelController` 도입으로 UI 로직과 비즈니스 로직 분리
- `ThreadSafeDatabase` 구현으로 DB 접근 안전성 강화
- `services/interfaces.py` + `services/implementations.py` 추가 — AI, 스토리지, 검색, 연속성 검사 등 서비스 인터페이스/구현체 분리
- `factories.py` 추가 — 서비스 팩토리 패턴 도입

### AI Provider 리팩토링
- `ai/providers/base.py` 대폭 수정 — 공통 Provider 인터페이스 정비
- `ai/providers/anthropic.py`, `gemini.py`, `openai_compatible.py` 대폭 수정 — 프로바이더별 구현 리팩토링
- `ai/context.py` 대폭 수정 — 컨텍스트 빌더 로직 개선

### 메인 창 기능 추가
- AI 연결 테스트 버튼(●) 추가 — 상단 툴바에 연결 상태를 색상으로 표시하는 원형 아이콘 버튼
- 연결 상태 색상: 초록(연결 성공) / 빨강(미연결·실패) / 회색(테스트 중)
- `run_connection_test()`로 현재 활성 프로바이더 연결 상태 확인 기능 제공

### 유틸리티/인프라
- `utils/retry.py` 추가 — 재시도 로직 유틸리티
- `requirements.txt` 업데이트
- `run_windows.bat` 수정

### 프로젝트 규칙/문서 정비
- `.clinerules/python-agent.md`, `.kilo/rules/kilorules.md`, `.kilo/kilo.jsonc` 추가
- `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md` 추가 — 개발 규칙 및 코딩 에이전트 지침 문서화

### 기타
- `novel_studio/ui/views/entities.py` 미세 조정 (2줄)
- `main_window.ui` 2줄 변경

---

## v1.4.1 — Feature Release

### 엔티티 상태 원장 실활용
- 화 집필 완료 시 AI가 "이번 화에서 상태가 실제로 변한 인물/세력/장소만" 추출해 `kind='character'/'world'`, `entity_key=명칭`으로 개별 기록 (같은 원고 재갱신 시 추출 생략)
- Retrieval Engine이 현재 화 직전 10화 구간의 확정 엔티티 상태를 컨텍스트에 공급 — 기존에는 `entity_states` 키가 누락돼 원장 블록이 항상 비어 있던 버그 수정
- 설정 DB의 인물/세력/장소 상세에 화별 `[상태 타임라인]` 표시 추가 (저장 시 타임라인 텍스트는 데이터에서 자동 분리)

### 토큰 기반 컨텍스트 예산 매니저
- `ai.context_budget_tokens`(기본 60,000) 설정 추가 — 컨텍스트 블록을 우선순위 순서(PLAN CONTRACT > 마스터 기획/플롯 > 직전 상태 > 참고 자료)로 누적 배분하고, 예산 초과 시 하위 블록부터 제거
- PLAN CONTRACT와 [USER REQUEST]는 항상 유지

### DB 마이그레이션 프레임워크
- `CURRENT_SCHEMA_VERSION` + 순차 `MIGRATIONS` 목록 구조로 전환 (v3: `idx_entity_state_updated` 인덱스 추가)
- 구버전 DB는 열 때 자동으로 순차 마이그레이션 적용

### CI 및 품질
- GitHub Actions CI 파이프라인 추가 — `compileall` + `pytest` 자동화 (push/PR 시 전체 검증)
- 저장 시점 FTS 인덱싱과 채팅 대화 이력 반영은 v1.4.0에서 이미 구현된 것을 확인하고 유지
- 신규 테스트 6개 추가: 엔티티 추출/타임라인/마이그레이션/컨텍스트 예산

### 보류 (평가 후 연기)
- 가상 스크롤/모델-뷰 리스트 전환: `insertItems` 일괄 삽입 개선으로 수천 항목 렌더링은 충분히 원활해져, 리스크 대비 이득이 적어 연기. 필요 시 DB `limit/offset` 연결부터 단계적 도입 권장.

---

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
