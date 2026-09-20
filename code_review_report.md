# Novel Studio Maker — 코드 리뷰 보고서

- **리뷰 대상 버전**: v1.5.3
- **리뷰 일시**: 2026-09-15
- **리뷰 범위**: 프로젝트 전체 소스 코드 (`novel_studio/`, `main.py`, 테스트, 설정 파일)

---

## 목차

1. [요약](#1-요약)
2. [프로젝트 구조 평가](#2-프로젝트-구조-평가)
3. [아키텍처 평가](#3-아키텍처-평가)
4. [코드 스타일 및 가독성 이슈](#4-코드-스타일-및-가독성-이슈)
5. [잠재적 버그 및 위험 요소](#5-잠재적-버그-및-위험-요소)
6. [안전성 및 에러 처리 평가](#6-안전성-및-에러-처리-평가)
7. [테스트 평가](#7-테스트-평가)
8. [의존성 및 설정 관리](#8-의존성-및-설정-관리)
9. [권고 사항 요약](#9-권고-사항-요약)
10. [세부 이슈 목록](#10-세부-이슈-목록)

---

## 1. 요약

전체적으로 잘 구조화된 장편 웹소설 집필 도구입니다. 역할별 4개 SQLite DB 분리, AI 작업 안전장치(취소/중단/거부 방지), 원자적 저장, 작업 큐 등 핵심 설계가 견고합니다.

**긍정적 측면:**
- AI 집필/윤문/종료 상태 생성 시 빈 응답·거부 응답 방어 로직이 체계적
- 작업 취소 토큰(CancelToken)과 재시도 백오프 구조가 안정적
- 프로젝트 경로/원고 파일의 원자적 저장(`os.replace`) 처리
- 역할별 4개 DB 분리 및 마이그레이션 경로

**주의/개선이 필요한 측면:**
- 핵심 모듈 여러 곳에서 PEP 8 포맷팅 미준수 (한 줄 함수/클래스)
- 내부 속성 직접 참조 및 불일치된 스키마 버전
- 일부 타입 힌팅 누락
- 테스트 디렉토리가 `.gitignore`에서 제외됨

---

## 2. 프로젝트 구조 평가

```
novel_studio/
├── ai/                    # AI 엔진, Provider, Context, Prompts
├── config/                # (없음 — AppSettings가 핵심)
├── controllers/           # NovelController (작업 흐름)
├── core/                  # ProjectManager, AppSettings
├── db/                    # SQLite, ThreadSafeDB, ProjectDB
├── factories.py           # ServiceFactory (단일 생성 경로)
├── intelligence/          # Retrieval, Diff
├── jobs/                  # Worker (QRunnable)
├── logging_config.py
├── manuscript/            # ChapterWriter
├── plot/                  # PlotManager
├── services/              # Interface + Implementation
├── ui/                    # Qt UI 계층
├── utils/                 # 텍스트, 파서, 재시도, 취소
```

**평가**: 계층 구조가 명확하고 책임 분리가 잘 되어 있습니다. `ServiceFactory`가 유일한 서비스 생성 경로이고, `NovelController`가 View와 Service 사이의 단일 작업 경로를 맡습니다.

**개선점**: `config/` 디렉토리가 없고 `core/` 안에 `AppSettings`가 혼재되어 있음. 규모가 커지면 `ai/`, `db/` 등과 동급의 패키지로 분리 고려 가능.

---

## 3. 아키텍처 평가

### 3.1 서비스 계층 (`services/`)

- `interfaces.py`에 9개 추상 클래스 정의 → `implementations.py`에서 구현
- 인터페이스 계약이 명확하고, `ServiceFactory.create_all()`에서 한 번에 생성
- **긍정적**: 의존성 주입이 일관적이고, 테스트 시 스텁으로 교체 용이

### 3.2 AI 제공자 (`ai/providers/`)

- `base.py`의 `AIProvider` 추상 클래스 → Anthropic, OpenAI Compatible, Gemini 구현
- LM Studio가 `OpenAICompatibleProvider`를 상속받아 사용
- **긍정적**: 재시도, 취소, 소켓 shutdown 처리 등이 베이스 클래스에 집중
- **개선점**: `GeminiProvider._chat_stream_impl`이 전체를 한 번에 읽는 비스트리밍 구현 (주석에 "실제 구현 시 SSE 필요"라고 명시되어 있으나, 현재 `chat_stream`이 `super().chat_stream()`을 호출하여 베이스의 스트림 리트라이 데코레이터를 사용 → 실제로 스트리밍이 안 되고 한 번에 반환됨)

### 3.3 데이터 계층

- `ThreadSafeDatabase`가 단일 RLock로 모든 DB 호출 직렬화
- `ProjectDatabase`가 역할별 4개 DB를 라우팅
- **긍정적**: WAL 모드, 외래키, FTS5 인덱스 활용
- **개선점**: `SQLiteStorage._prune_profile_schema()`에서 `PRAGMA user_version = 1501`을 설정하지만 `CURRENT_SCHEMA_VERSION = 4`와 불일치

### 3.4 Controller 작업 큐 (`controllers/novel_controller.py`)

- `_job_queue`에 `(label, fn, done, error, cancelled, is_stream)` 또는 `(label, fn, done, error, cancelled, is_stream, progress_cb)` 형태로 저장
- `_finish_job_state()`에서 `queued[5]`로 is_stream 구분 → **스트리밍 작업 대기열에는 7개 요소, 일반 작업에는 6개 요소** — 인덱스 5만 사용하므로 동작하지만 향후 유지보수 시 혼동 가능

---

## 4. 코드 스타일 및 가독성 이슈

### 4.1 PEP 8 위반 — 한 줄 함수/클래스

다음 파일에서 함수/메서드 본문이 모두 한 줄로 작성되어 가독성이 매우 낮습니다:

| 파일 | 예시 |
|------|------|
| `ai/engine.py` | `AIEngine` 전체 메서드 (19행 전체가 6줄) |
| `ai/prompts.py` | 모든 프롬프트 함수 (105행 전체가 ~40줄) |
| `intelligence/retrieval.py` | `RetrievalEngine` 전체 (23행) |
| `intelligence/diff.py` | `MasterDiffService` (22행) |
| `continuity/checker.py` | `ContinuityChecker` (22행) |
| `plot/plot_manager.py` | 대부분의 메서드 |
| `manuscript/chapter_writer.py` | `ChapterWriter` 전체 (24행) |
| `utils/story_parser.py` | `parse_chapter_stories` (11행) |
| `utils/entity_parser.py` | `parse_entity_catalog` (17행) |
| `services/idea_service.py` | `IdeaService` 전체 (11행) |
| `services/end_state_service.py` | `EndStateService` 전체 (34행) |
| `ui/views/chat.py` | `ChatWindow` (12행) |
| `ui/views/planning.py` | `PlanningView` (36행) |
| `ui/views/end_state.py` | `EndStateView` (69행) |
| `ui/loader.py` | `load_ui` (7행) |
| `ui/views/_base.py` | `BaseView` (6행) |
| `utils/text.py` | `count_chars` (2행) |
| `core/project.py` | 여러 메서드 |

**영향**: 코드 리뷰와 디버깅이 어렵고, IDE 자동 완성/리팩토링 도구 활용도가 떨어집니다.

**권고**: 복잡한 메서드는 여러 줄로 펼치고, 간단한 메서드(1-2행)도 `pass`, `return` 등을 포함한 최소 구조를 유지할 것.

### 4.2 이중 Docstring

`services/end_state_service.py:8`:
```python
class EndStateService:
    """화 종료 상태를 생성하고 저장하는 서비스."""
    """실제 원고에서 다음 화에 필요한 종료 상태만 생성한다."""
```
첫 번째 문자열이 클래스 docstring이 되고 두 번째는 무시됩니다. 두 내용을 하나로 병합할 것.

### 4.3 변수명/서식 일관성

- `ai/prompts.py:1`: `SECTIONS=[...]` — PEP 8에서는 상수는 `ALL_CAPS`여야 하는데 맞지만, 가독성을 위해 줄바꿈 권장
- `ai/engine.py:2`: `def __init__(self,providers,settings):` — 쉼표 후 공백 없음
- 여러 곳에서 `self.db`에 `ProjectDatabase` 인스턴스와 `ThreadSafeDatabase` 인스턴스가 혼용되어 명확하지 않음

---

## 5. 잠재적 버그 및 위험 요소

### 5.1 🔴 `ProjectManager.create()` — 파라미터 중복 전달

**위치**: `ui/startup.py:50`
```python
section_size=self.longStorySpin.value(), long_story_size=self.longStorySpin.value(), sub_story_size=self.subStorySpin.value()
```
`section_size`와 `sub_story_size`에 **동일한 값**이 전달됩니다. `section_size`에는 `self.longStorySpin.value()`가 전달되어야 합니다.

**영향**: 프로젝트 생성 시 장기 스토리 구간 크기가 세부 스토리 구간 크기와 동일하게 설정됨.

### 5.2 🔴 `ai/context.py:build()` — 변수 스코프 문제

**위치**: `ai/context.py:73-127`

`chapter=None`인 경우 `else` 분기에서 `chars`, `worlds`, `fs`에 값을 할당하지만, `if chapter:` 분기에서는 `r` 변수가 사용됩니다. `chapter=None`일 때 `r`은 정의되지 않으므로 `r` 참조 시 `NameError`가 발생합니다. 다만 현재 코드에서는 `chapter=None` 분기에서 `r`을 사용하지 않아 동작하지만, 향후 확장 시 위험합니다.

### 5.3 🟡 `SQLiteStorage._migrate_schema()` — 마이그레이션 미실행

**위치**: `db/sqlite_storage.py:127-142`

`MIGRATIONS = {4: ""}`로 4번 단계의 마이그레이션 SQL이 빈 문자열입니다. 새 DB이면 `CURRENT_SCHEMA_VERSION`을 기록하고 반환하므로 문제 없으나, 구버전 DB에서 4번 이하 버전일 경우 마이그레이션이 아무것도 실행되지 않습니다.

### 5.4 🟡 `ProjectDatabase._migrate_v150_story()` — 내부 속성 직접 참조

**위치**: `db/project_database.py:221`
```python
if old._base._table_exists("chapter_plans"):
```
`_base`는 내부 속성입니다. `SQLiteStorage`에 공적 메서드로 노출하거나 래퍼를 사용할 것을 권장합니다.

### 5.5 🟡 `ProjectDatabase._apply_legacy_modular_story()` — 외부 DB 직접 연결

**위치**: `db/project_database.py:125-143`

마이그레이션 전용으로 `sqlite3.connect(legacy)`를 직접 생성하고 별도 `con.close()`를 호출하지만, 예외 발생 시 `finally`에서만 닫고, `_read_legacy_modular_story()` 내부에서도 닫습니다. 이중 클로즈 시도 가능.

### 5.6 🟡 `NovelController._finish_job_state()` — 대기열 인덱스 의존성

**위치**: `controllers/novel_controller.py:109-116`

대기열에서 `queued[5]`로 is_stream을 확인합니다. 일반 작업은 6개, 스트리밍 작업은 7개 튜플인데 공통 인덱스 5만 사용하므로 동작하지만, 새로운 작업 유형 추가 시 실수로 인덱스 범위를 벗어날 위험이 있습니다.

### 5.7 🟡 `ChatWindow` — `MainWindow` 메서드 의존성

**위치**: `ui/views/chat.py:7`
```python
self.sendBtn.clicked.connect(w.send_chat)
self.searchBtn.clicked.connect(w.search_chat)
```
`w`가 반드시 `MainWindow` 인스턴스여야 하며, `send_chat`, `search_chat` 메서드가 없으면 런타임 에러입니다. 인터페이스 계약이 명확하지 않습니다.

### 5.8 🟡 `StartupDialog.create()` — 파라미터 매핑 오류 가능

**위치**: `ui/startup.py:50`

`section_size=self.sub_story_size, long_story_size=self.long_story_size, sub_story_size=self.subStorySpin.value()`에서 `section_size`와 `sub_story_size`에 모두 `self.subStorySpin.value()`가 들어갑니다. (5.1과 동일한 문제)

### 5.9 🟢 `app_settings.py` — 예외 무음 처리

**위치**: `core/app_settings.py:30-31`
```python
except Exception:
    pass
```
설정 파일 로드 실패 시 완전히 무시하고 기본값 사용. 로그에 기록되면 디버깅에 도움이 됩니다.

---

## 6. 안전성 및 에러 처리 평가

### 6.1 긍정적 사례

| 영역 | 구현 |
|------|------|
| **AI 거부 방어** | `MainWindow._looks_like_ai_refusal()` — 13개 패턴 + 800자 길이 상한으로 AI 안내/거부 메시지 원고 저장 차단 |
| **빈 원고 보정 방지** | `ChapterWriter.adjust()` — 빈 원고에서 AI 호출 전에 ValueError 차단 |
| **원자적 저장** | `ProjectManager._save_project_json()` — tmp 파일 → `os.replace()` 패턴 |
| **원고 백업** | `ProjectManager.save_chapter()` — 저장 전 `.bak` 파일 생성 |
| **작업 취소** | `CancelToken` + `JobCancelled` 예외로 취소 전파, retry 대기 중 즉시 중단 |
| **소켓 종료** | `AIProvider.abort()` — 소켓 shutdown(SHUT_RDWR)으로 블로킹 read 중단 |
| **AI 빈 응답 방지** | 집필 결과가 빈 문자열이거나 거부 메시지이면 절대 파일 저장하지 않음 |

### 6.2 개선이 필요한 에러 처리

- **`SQLiteStorage.execute()`**: `self.conn.commit()` 후 `return cur` — 커밋이 실패할 수 있는 상황을 고려하지 않음
- **`NovelController._run()`**: 반환값 `False`를 호출부에서 무시할 수 있음 (`main_window.py`의 레거시 `_run()` 래퍼에서 상태바 메시지로만 알림)
- **`ProjectDatabase.close()`**: 일부 DB 닫기 실패 시 전체 raise 처리 — 부분 성공 불가

---

## 7. 테스트 평가

### 7.1 테스트 커버리지

| 테스트 파일 | 검증 항목 |
|-------------|-----------|
| `test_v153_quality.py` | 프로젝트 JSON 원자적 저장, 백업 보존, 레거시 마이그레이션, 반환 타입 힌팅 |
| `test_qt_smoke.py` | Qt 위젯, 메인 윈도우 뷰 전환, 설정 다이얼로그, 연결 상태, 채팅창 |
| `test_ai_failure_cancel.py` | 취소 토큰, 재시도 중단 |
| `test_cancel.py` | 취소 토큰, 재시도 대기 중단, JobWorker 시그널 |
| `test_refusal_guard.py` | AI 거부 메시지 탐지, 빈 원고 보정 방지 |
| `test_database.py` | DB CRUD, 연속성 조회 |
| `test_retry.py` | (미확인 — 별도 읽기 필요) |
| `test_job_quality.py` | (미확인 — 별도 읽기 필요) |
| `test_story_parser.py` | (미확인 — 별도 읽기 필요) |
| `test_v15_architecture.py` | (미확인 — 별도 읽기 필요) |
| `test_v151_stability.py` | (미확인 — 별도 읽기 필요) |
| `test_v152_quality.py` | (미확인 — 별도 읽기 필요) |

### 7.2 `.gitignore` 문제

**.위치**: `.gitignore:33`
```
tests/
```

**테스트 디렉토리가 Git 추적에서 완전히 제외되어 있습니다.** 이는:
- CI에서 회귀 테스트 실행 불가 (레포지토리 외부에 테스트만 있는 경우)
- 버전 관리 이력에서 테스트 코드 추적 불가
- 팀 협업 시 테스트 공유 불가

**강력 권고**: `.gitignore`에서 `tests/` 제거 또는 `tests/` 내 특정 패턴만 무시하도록 변경.

### 7.3 테스트 관련 긍정적 점

- `pytest-qt` 기반 Qt UI 테스트로 실제 GUI 동작 검증
- `pyhanspell` 의존성이 없어도 맞춤법 검사 폴백 동작 (테스트에 반영됨)
- AI 거부 메시지 실제 사례를 테스트로 검증 (test_refusal_guard.py)

---

## 8. 의존성 및 설정 관리

### 8.1 requirements.txt

| 패키지 | 범위 | 용도 |
|--------|------|------|
| PySide6>=6.7,<7 | UI 프레임워크 | Qt 기반 GUI |
| keyring>=25,<27 | 시스템 키체인 | API 키 안전 저장 |
| pytest>=8,<9 | 테스트 프레임워크 | 단위/통합 테스트 |
| tiktoken>=0.5,<1 | 토큰 카운터 | Context 토큰 예산 계산 |

**확인 사항**: `requirements.txt`에 `PySide6-Qt` 관련 빌드 도구(`pyside6-tools` 등)가 없으므로, PySide6 설치 시 pip로만 충분한지 확인 필요.

### 8.2 mypy.ini

- `exclude = ^novel_studio/ui/forms/|^tests/` — UI 자동 생성 파일과 테스트 제외
- `check_untyped_defs = True` — 타입 힌트 없는 함수도 검사 → 위반 코드 많으므로 정적 분석 부담이 큼
- **개선점**: `warn_return_any`, `warn_unused_configs` 추가 권장

### 8.3 설정 파일 위치

- `AppSettings`: `~/.novel_studio_settings.json` (홈 디렉토리)
- 프로젝트 설정: `{project_root}/project.json`
- 로그: `{project_root}/logs/app.log`

**개선점**: 환경 변수 또는 CLI 인자로 설정 경로를 오버라이드할 수 있으면 유연해집니다.

---

## 9. 권고 사항 요약

### 긴급 (High Priority) — 수정 완료

| # | 이슈 | 파일 | 상태 |
|---|------|------|------|
| 1 | `ProjectManager.create()` 파라미터 중복 | `ui/startup.py:50` | ✅ 수정: `section_size` → `longStorySpin.value()` |
| 2 | 동일 파라미터 문제 (startup) | `ui/startup.py:50` | ✅ 수정 완료 |
| 3 | `tests/`가 `.gitignore`에 포함 | `.gitignore:33` | ✅ 제거 완료 |

### 중간 (Medium Priority) — 전부 수정 완료

| # | 이슈 | 파일 | 상태 |
|---|------|------|------|
| 4 | 한 줄 함수/클래스 다수 | 17개 파일 | ✅ PEP 8 가독성 확보를 위해 여러 줄로 펼치기 |
| 5 | 타입 힌트 누락 | 7개 파일 | ✅ 타입 힌팅 보강 |
| 6 | `MIGRATIONS` 빈 값 | `db/sqlite_storage.py:11` | ✅ 수정: 실행 가능한 SQL(`PRAGMA user_version = 4;`) + 주석 추가 |
| 7 | 내부 속성 직접 참조 | `db/project_database.py:221,232` | ✅ 수정: `ThreadSafeDatabase.table_exists()` 공적 메서드 추가 후 `old._base._table_exists()` → `old.table_exists()` 변경 |
| 8 | EndStateService 이중 docstring | `services/end_state_service.py:7-8` | ✅ 수정: 하나로 병합 |
| 9 | `retry.is_retryable_error` 항상 True | `utils/retry.py:40` | ✅ 수정: 마지막 `return True` → `False` + 디버그 로그 추가, 취소 체크를 재시도 판별 전 별도 처리 |

### 낮음 (Low Priority) — 전부 수정 완료

| # | 이슈 | 파일 | 상태 |
|---|------|------|------|
| 10 | 예외 무음 처리 | `core/app_settings.py:30` | ✅ 수정: `except Exception` → 로그 기록 추가 |
| 11 | 대기열 인덱스 의존성 | `controllers/novel_controller.py:32,111-116,129-158` | ✅ 수정: `JobQueueItem` NamedTuple으로 교체, `queued[5]` → `queued.is_stream` |
| 12 | Gemini 스트리밍 미구현 | `ai/providers/gemini.py:48-52` | ✅ 수정: 명시적 비활성 표시 (docstring으로 사유 및 구현 경로 안내) |
| 13 | ChatWindow 인터페이스 불명확 | `ui/views/chat.py` | ✅ 수정: `ChatWindowHost` Protocol로 계약 정의 |
| 14 | `context.py` 변수 스코프 | `ai/context.py:84` | ✅ 수정: `r = None` 명시 초기화 |
| 15 | mypy 검사 범위 확대 | `mypy.ini` | ✅ 수정: `warn_return_any`, `warn_unused_configs` 추가 |

---

## 10. 세부 이슈 목록

### 10.1 코드 줄 수 및 복잡도

| 파일 | 행 수 | 비고 |
|------|-------|------|
| `ui/main_window.py` | 1,450 | 가장 큰 파일. 메서드 분리 고려 필요 |
| `db/sqlite_storage.py` | 496 | DB 작업 집중. 메서드별 분리 가능 |
| `ai/providers/base.py` | 278 | 취소/재시도/소켓 로직 집중 |
| `ui/dialogs.py` | 316 | 설정 다이얼로그 + 프로젝트 설정 |
| `ui/views/entities.py` | 473 | 엔티티 CRUD 복잡 |
| `novel_studio/ui/help/content.py` | 223 | 도움말 콘텐츠 |

### 10.2 아키텍처 패턴 확인

| 패턴 | 구현 위치 | 상태 |
|------|-----------|------|
| 서비스 팩토리 (단일 생성 경로) | `factories.py:ServiceFactory` | ✅ 구현 |
| Controller-View 분리 | `controllers/novel_controller.py` | ✅ 구현 |
| 인터페이스 계약 | `services/interfaces.py` | ✅ 구현 |
| DB 역할 분리 | `db/project_database.py` | ✅ 구현 |
| 원자적 저장 | `core/project.py` | ✅ 구현 |
| 작업 큐 | `controllers/novel_controller.py` | ✅ 구현 (개선 여지) |
| 취소 토큰 | `utils/cancellation.py` | ✅ 구현 |
| 재시도 백오프 | `utils/retry.py` | ✅ 구현 |
| AI 거부 방어 | `ui/main_window.py` | ✅ 구현 |

### 10.3 보안 관련

- API 키는 `keyring`을 통해 시스템 키체인에 저장 (긍정적)
- `app_settings.py`에서 설정 파일 파싱 예외를 무시 — 키 유실 가능성 낮지만 로그 부재
- `ProviderManager.save_key()`에서 `keyring.delete_password()` 호출 시 예외 무시 → 의도적 설계

---

## 부록: 리뷰 범위 포함 파일

- `main.py` — 엔트리 포인트
- `novel_studio/core/` — 프로젝트 관리, 앱 설정
- `novel_studio/ai/` — AI 엔진, Provider, Context, Prompts
- `novel_studio/db/` — SQLite, ThreadSafeDB, ProjectDB
- `novel_studio/services/` — 인터페이스, 구현체
- `novel_studio/controllers/` — NovelController
- `novel_studio/jobs/` — Worker
- `novel_studio/factories.py` — ServiceFactory
- `novel_studio/plot/` — PlotManager
- `novel_studio/manuscript/` — ChapterWriter
- `novel_studio/continuity/` — ContinuityChecker
- `novel_studio/intelligence/` — Retrieval, Diff
- `novel_studio/utils/` — 텍스트, 파서, 재시도, 취소
- `novel_studio/ui/` — 모든 UI 계층 (forms, views, dialogs, help, loader)
- `novel_studio/logging_config.py`
- `novel_studio/logging_config.py`
- 테스트 파일 전체 (13개)
- 설정 파일 (`requirements.txt`, `mypy.ini`, `pytest.ini`, `.gitignore`, `version.txt`)
