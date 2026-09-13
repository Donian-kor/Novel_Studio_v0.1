# Novel Studio v1.4.5 코드 점검 종합 보고서

검토 대상: `Novel_Studio(2).zip` / v1.4.5  
기준 문서: `Novel Studio v1.4.0 프로그램 설계의도·기획서 상세`  
검토 목적: **기획서 대비 실제 구현 상태 확인 + 버그 + 구조 문제 + 하드코딩 + 중복 + 기능 불량 + 데이터 무결성 + UI 배치/사용성 점검**

---

## 1. 결론

### 종합 판정

**v1.4.5는 현재 상태에서 “리팩토링 완료 버전”으로 판단하기 어렵다.**

핵심 기능을 담당하는 코드 자체는 상당 부분 존재하고, 프로젝트/설정 DB/플롯/원고/기억/연속성/검색 등의 기본 뼈대도 갖추어져 있다. 그러나 v1.4.2 이후 도입한 Controller·Service·ThreadSafeDatabase 구조가 실제 실행 흐름 전체에 완전히 적용되지 않았고, 그 결과 **집필·윤문·연속성 검사·취소·서비스 계층 일부가 실제로 끊어져 있다.**

특히 다음 문제는 단순한 정리 수준이 아니라 실제 사용자 기능에 직접 영향을 주는 **P0/P1급 문제**다.

1. Controller의 스트리밍 callback 연결이 끊겨 있어 집필/윤문 흐름이 정상적으로 연결되지 않음.
2. `WritingServiceImpl`이 callback을 `extra` 프롬프트로 잘못 넘기는 구조적 오류.
3. `check_current_chapter()`가 중복 정의되어 최종 정의가 자기 자신을 다시 호출하며, 동시에 MainWindow 호출 시 인자 수도 맞지 않음.
4. `stop_current_job()`도 중복 정의 후 최종 구현이 `pass`라서 Controller 정지가 동작하지 않음.
5. Controller가 현재 작업 객체를 `self._current_job`에 저장하지 않아 취소 기능이 실질적으로 연결되지 않음.
6. Provider의 `chat_stream()`이 중복 정의되어 실제 provider 스트리밍 구현이 덮어써짐.
7. `ThreadSafeDatabase`가 정의된 메서드와 `BaseDatabase` 위임 메서드가 섞이며 서로 다른 DB 연결을 사용함.
8. `EntitiesView.save_entry()`가 저장 시 현재 선택 항목의 이름을 현재 카테고리의 **모든 캐시 행에 덮어씀**.
9. 장편 정밀 연속성 검사가 UI의 `_run()` 안에서 다시 `_run()`을 호출하는 구조라 버튼 흐름이 잘못 설계됨.
10. 서비스 구현체 일부가 실제 필드/테이블 구조와 맞지 않거나 `pass` 상태로 남아 있음.

따라서 현 시점에서 권장되는 방향은 기능을 계속 추가하는 것이 아니라 **P0/P1 오류 제거 → Controller/Service 단일 경로화 → DB 접근 계층 단일화 → 데이터 무결성 검증 → 테스트 자동화 → UI 세부 개선** 순서다.

---

# 2. 검토 방법과 범위

## 2.1 정적 검사

- 전체 Python 소스 AST 분석
- 중복 함수/메서드 정의 검색
- 중복 import 검색
- 주요 클래스의 직접 의존성 확인
- UI XML 구조와 최소/최대 크기 확인
- DB 스키마와 CRUD 메서드 대조
- Controller → Service → Core 호출 경로 추적
- AI Provider → AIEngine → Writing/Context 호출 경로 추적
- 예외 처리 및 `pass` 구문 점검
- 버전/README/CHANGELOG/실행 스크립트 일치 여부 확인

## 2.2 실행 검증

### 통과

```text
python -m compileall -q novel_studio main.py
```

결과: **통과**

### 테스트

```text
PYTHONPATH=. pytest -q
```

결과:

```text
no tests ran in 0.01s
```

즉, 제출된 압축본 안에는 실행 가능한 pytest 테스트가 존재하지 않는다.

### 제한 사항

검토 환경에는 `PySide6`가 설치되어 있지 않아 실제 GUI를 화면으로 띄운 상태의 클릭/렌더링 검증까지는 수행할 수 없었다. 따라서 UI 항목은 **UI XML + 코드 연결 + 레이아웃 값 + 이벤트 배선**을 기준으로 점검했다.

이는 GUI가 정상이라고 단정할 수 없다는 의미가 아니라, 화면 실측 검증이 별도로 필요하다는 의미다.

---

# 3. 기획서 대비 구현 상태

| 기획 항목 | 상태 | 판정 |
|---|---|---|
| 프로젝트 단위 작품 관리 | 구현됨 | ✅ |
| DB + 파일 분리 저장 | 구현됨 | ✅ |
| AI를 보조 엔진으로 사용 | 구현됨 | ✅ |
| Story / Writing 역할 분리 | 모듈은 존재하지만 실제 호출 흐름은 혼재 | ⚠️ |
| UI → Controller → Service 구조 | 일부만 적용 | ❌ |
| 현재 화 중심 Context Retrieval | 기본 구현 존재 | ⚠️ |
| 토큰 예산 관리 | 구현됨 | ⚠️ |
| 화별 상태 관리 | 원장 구조 존재 | ⚠️ |
| 인물 관계 관리 | DB 테이블만 존재, 실질 CRUD 없음 | ❌ |
| 아이템 관리 | 별도 데이터 모델/CRUD 없음 | ❌ |
| 복선 관리 | 기본 CRUD 존재 | ⚠️ |
| 복선 사건 이력 | 테이블/함수 존재하나 자동 연계 약함 | ⚠️ |
| 화→구간→아크 장기 기억 | 구현됨 | ✅/⚠️ |
| 단일 화 연속성 검사 | 코드 존재하나 Controller 호출 오류 | ❌ |
| 장편 정밀 연속성 검사 | 구현은 있으나 실제 입력 범위가 얕고 UI 배선 문제 | ❌/⚠️ |
| AI 결과 검증/후처리 | 일부 존재 | ⚠️ |
| 사용자 검토 후 확정 | 원칙은 있으나 저장 상태/흐름에서 보완 필요 | ⚠️ |
| 설정 변경 영향 관리 | 제안/기록 구조는 있으나 실제 영향 추적 미흡 | ⚠️ |
| 500화 이상 장편 안정성 | 기본 구조는 있으나 현재 상태로는 안정버전 판정 불가 | ❌ |
| 버전/배포 일관성 | 불일치 다수 | ❌ |
| 자동 테스트 | 사실상 없음 | ❌ |

---

# 4. 최우선 버그(P0) 

## P0-01. Controller 스트리밍 작업의 callback 연결이 끊겨 있음

**파일**

`novel_studio/controllers/novel_controller.py:266-286`

### 문제

`_run_stream()`은 다음 인자를 받는다.

```python
_run_stream(label, fn, done_callback, append_widget=None, replace=True)
```

그런데 실제 signal 연결은 다음처럼 되어 있다.

```python
job.signals.progress.connect(lambda t, w=None: self._on_stream_token(w, t))
job.signals.finished.connect(lambda v: self._on_stream_done(None, v))
```

즉,

- 전달받은 `append_widget`을 실제 signal에 연결하지 않음
- 전달받은 `done_callback`을 버림
- 항상 `None`을 `_on_stream_token()`에 전달
- 항상 `None`을 `_on_stream_done()`에 전달

### 영향

MainWindow의 다음 흐름이 끊긴다.

```text
write_current()
    ↓
controller.write_chapter()
    ↓
_run_stream()
    ↓
AI 생성
    ↓
완료 결과
    X done_callback으로 전달되지 않음
```

따라서 집필 완료 후 `_handle_written_result()`로 들어가야 하는 연결이 끊긴다.

### 영향 기능

- AI 집필
- AI 윤문
- 실시간 원고 스트리밍 UI
- 생성 완료 후 글자 수 보정
- 생성 완료 후 기억 갱신
- 생성 완료 후 연속성 검사

### 수정

Controller의 스트리밍 인프라를 다음 형태로 고정해야 한다.

```text
StreamJob
 ├─ progress → controller token signal → UI
 ├─ finished → done_callback
 ├─ error → error_callback
 └─ cancelled → cancel callback
```

그리고 `stream_callback`, `append_widget`, `done_callback` 중 한 가지 방식만 남겨야 한다.

---

## P0-02. `WritingServiceImpl.write_chapter()`가 callback을 잘못된 인자로 전달

**파일**

`novel_studio/services/implementations.py:205-216`

### 문제

```python
return self.writer.write_stream(chapter, stream_callback)
```

하지만 `ChapterWriter.write_stream()`의 두 번째 인자는 callback이 아니라 `extra` 문자열이다.

```python
def write_stream(self, n, extra=''):
```

즉 실제 의미는 다음과 같다.

```text
stream_callback 함수
      ↓
extra 프롬프트 인자
      ↓
ContextManager.build(..., extra)
```

### 결과

문맥 구성 단계에서 문자열로 취급되어야 할 값에 함수 객체가 들어간다.

정상 설계라면 `StreamJob`이 generator를 소비하면서 token signal을 발생시켜야 하고 `ChapterWriter.write_stream()`은 **추가 프롬프트만 담당**해야 한다.

### 수정 방향

`WritingServiceImpl`에서 callback을 제거하고

```python
return self.writer.write_stream(chapter)
```

처럼 generator를 반환한 뒤, 실제 callback은 `StreamJob`에 맡기는 방식이 가장 단순하다.

---

## P0-03. `check_current_chapter()` 중복 정의로 기능이 깨짐

**파일**

`novel_studio/controllers/novel_controller.py`

첫 구현:

`385-390`

최종 구현:

`436-438`

최종 구현은 다음과 같다.

```python
def check_current_chapter(self, chapter: int, text: str):
    return self.check_current_chapter(chapter, text)
```

### 문제 1: 이전 구현이 덮어써짐

정상 구현은 `done_callback`을 받아 `_run_job()`을 실행한다.

그러나 두 번째 동일한 이름의 메서드가 그 구현을 덮어쓴다.

### 문제 2: 자기 자신 호출

최종 메서드는 자기 자신을 다시 호출한다.

논리적으로는 무한 재귀 구조다.

### 문제 3: MainWindow 인자 불일치

MainWindow는 다음처럼 세 번째 인자까지 전달한다.

```python
self.controller.check_current_chapter(self.current, text, done_callback)
```

하지만 최종 메서드는 `chapter, text`만 받는다.

따라서 재귀 이전에 인자 수 오류가 발생할 가능성이 높다.

### 영향

**현재 화 연속성 검사 기능 불량**

### 수정

동일 메서드 1개만 남기고 첫 구현을 유지해야 한다.

---

## P0-04. Controller의 작업 취소가 사실상 연결되지 않음

### 문제

`_run_job()`와 `_run_stream()`에서는

```python
job = Job(fn)
```

또는

```python
job = StreamJob(fn)
```

을 생성하지만

```python
self._current_job = job
```

가 없다.

따라서 Controller의

```python
stop_current_job()
```

이 호출되어도 현재 실행 중인 실제 job을 찾지 못한다.

또한 `stop_current_job()`은 파일 뒤쪽에서 중복 정의된 뒤 최종적으로 `pass`가 된다.

### 영향

Controller 경로에서는

```text
정지 버튼
 ↓
Controller.stop_current_job
 ↓
실제 Job
```

연결이 보장되지 않는다.

### 수정

Job 생성 직후 반드시

```python
self._current_job = job
```

을 설정하고 종료/실패/취소 시 `None`으로 되돌려야 한다.

---

## P0-05. AI Provider의 `chat_stream()`이 중복 정의되어 실제 스트리밍이 덮어쓰기됨

**파일**

`novel_studio/ai/providers/base.py:72-82`

첫 번째 구현:

```python
def chat_stream(...):
    return self._stream_retry_decorator(self._chat_stream_impl)(...)
```

두 번째 구현:

```python
def chat_stream(...):
    text = self.chat(...)
    yield text
```

Python에서는 두 번째 정의가 최종 적용된다.

### 결과

Provider별 `_chat_stream_impl()`이 있어도 호출되지 않고 일반 `chat()`으로 한 번에 전체 결과를 받아 한 번 yield한다.

즉 CHANGELOG가 설명하는 진짜 provider-level streaming과 실제 동작이 다르다.

### 영향

- 스트리밍 UX 저하
- 토큰 단위 취소 반응성 저하
- 긴 원고 생성 시 진행 표시가 사실상 전체 완료까지 지연될 수 있음
- retry_stream 로직도 사용되지 않음

### 수정

`chat_stream()`을 1개만 유지한다.

스트리밍을 지원하지 않는 Provider만 별도로 fallback 하도록 구조화한다.

---

## P0-06. Entities 저장 로직이 현재 카테고리의 모든 항목 이름을 덮어쓸 수 있음

**파일**

`novel_studio/ui/views/entities.py:289-367`

핵심 문제는 다음 코드다.

```python
for i, (kind, label, row) in enumerate(self._cache):
    if self.nameEdit:
        row['name'] = self.nameEdit.text().strip()
```

선택된 행인지 확인하는 조건보다 먼저 모든 row에 대해 이름을 수정한다.

그 다음에야

```python
if i == self._selected_index:
```

가 나온다.

### 결과 예시

인물 10명이 있을 때 3번 인물을 선택하고 이름을 수정한 후 저장하면, 0~9번 모든 캐시 row의 `name`이 현재 `nameEdit` 값으로 들어갈 수 있다.

### 영향

- 기존 인물 데이터 오염
- 동일 이름 충돌
- 의도치 않은 upsert
- 설정 DB 무결성 훼손 가능
- 사용자 입장에서 “한 명 수정했는데 다른 인물이 바뀌는” 치명적인 오류

### 수정

`name` 수정은 반드시

```python
if i == self._selected_index:
```

안에서만 수행해야 한다.

또한 저장 자체도 현재 선택 항목만 저장하고, 전체 저장은 별도의 명확한 동작으로 분리하는 것이 안전하다.

---

## P0-07. 장편 정밀 연속성 검사에서 `_run()`이 중첩 호출됨

**파일**

`novel_studio/ui/main_window.py:146-148`, `935-968`

버튼 연결이 다음 구조다.

```python
mem.auditBtn.clicked.connect(
    lambda: self._run(..., self.audit_long_form, ...)
)
```

그런데 `audit_long_form()` 내부에서도 다시

```python
self._run(...)
```

을 호출한다.

### 결과

외부 `_run`이 먼저 `_busy=True`로 만든 다음 내부 `_run()`이 실행된다.

내부 `_run()`은 이미 작업 중이라고 판단할 가능성이 높다.

### 추가 문제

`audit_long_form()`의 `progress_callback()`은 worker thread에서 직접

```python
self.statusBar().showMessage(...)
mem.edit.setPlainText(...)
```

를 호출한다.

Qt UI 객체를 worker thread에서 직접 수정하는 구조다.

### 수정

`audit_long_form()`은 worker job function만 제공하고 UI 업데이트는 Signal을 통해 main thread에서 수행해야 한다.

---

## P0-08. ThreadSafeDatabase가 실제로는 하나의 DB 접근 계층이 아님

**파일**

`novel_studio/db/threadsafe_database.py`

### 문제 구조

생성 시점에 이미

```python
self._base = BaseDatabase(Path(path))
```

가 별도의 SQLite connection을 만든다.

그 후 `__getattr__()`로 ThreadSafeDatabase에 없는 메서드를 `_base`에 위임한다.

즉 현재 DB 접근은 사실상 다음처럼 나뉜다.

```text
ThreadSafeDatabase
 ├─ 직접 구현 메서드
 │   └─ thread-local / write lock 사용
 │
 └─ 없는 메서드
     └─ BaseDatabase connection 사용
```

### 문제

서로 다른 connection이 동일 DB 파일을 사용하면서 일부는 wrapper lock을 사용하고 일부는 wrapper를 우회한다.

이 구조는 “thread-safe database”라는 이름과 실제 사용 방식이 일치하지 않는다.

### 추가 문제

`_create_schema`, `execute`, `get_plan`, `save_plan`, `get_contract`, `save_contract` 등이 파일 내부에서 여러 차례 중복 정의되어 있다.

### 수정

가장 좋은 방향은 둘 중 하나다.

**A안**: `ThreadSafeDatabase`가 Database API 전체를 명시적으로 구현한다.  
**B안**: BaseDatabase를 제거하고 ThreadSafeDatabase만 단일 DB abstraction으로 사용한다.

현재처럼 `__getattr__()`으로 무차별 위임하는 방식은 제거하는 편이 좋다.

---

# 5. 주요 구조적 문제(P1)

## P1-01. MainWindow가 여전히 모든 핵심 로직을 직접 조정함

**파일**

`novel_studio/ui/main_window.py:69-92`

현재 `_init_services()`는 Controller에 서비스를 주입하면서도 동시에 MainWindow 안에 다음 객체를 전부 보유한다.

```text
ProjectManager
Database
ProviderManager
AIEngine
ContextManager
IdeaService
MasterPlanner
PlotManager
StateLedger
MasterDiffService
ChapterWriter
MemoryManager
ContinuityChecker
```

### 결과

실제 구조는

```text
UI
 ├─ Controller
 │   └─ Service
 │
 └─ Core 직접 호출
```

이다.

기획서가 원하는 구조는

```text
UI
 ↓
Controller
 ↓
Service / Story Engine / Writing Engine
 ↓
Core / DB / AI
```

이다.

### 판정

**리팩토링의 외형만 적용되고 실행 경로는 완전히 이전되지 않은 상태**다.

### 수정

MainWindow는 다음 정보만 가져야 한다.

```text
View 상태
사용자 입력
Controller 호출
Signal 수신
```

DB/AI/Writer/Memory 직접 호출은 제거해야 한다.

---

## P1-02. Service 계층 일부가 실제로 사용할 수 없는 상태

### ProjectServiceImpl

`novel_studio/services/implementations.py:27-60`

생성자는

```python
ProjectServiceImpl(project_manager, app_settings)
```

인데 `self.db`가 없다.

그런데

```python
get_chapter_info()
update_chapter()
```

에서는 `self.db`를 사용한다.

→ 실행 시 AttributeError 가능.

### DatabaseServiceImpl

`get_chapter_content()`:

```python
row = self.db.chapter(chapter)
return row['content']
```

그러나 현재 DB의 `chapters` 테이블에는 `content` 컬럼이 없다.

원고 본문은 프로젝트의 `chapters/*.txt`에 저장되는 설계다.

→ 서비스 인터페이스 자체가 현재 저장 모델과 맞지 않는다.

### save_chapter()

`save_chapter()`는 실제 구현 없이 `pass`다.

### WritingServiceImpl

`write_chapter()`가 앞서 설명한 callback/extra 혼동 문제를 갖고 있다.

### check_consistency()

`self.checker`를 사용하지만 생성자에서 `self.checker`를 저장하지 않는다.

→ 실행 시 AttributeError 가능.

### 판정

**Service layer는 현재 “완성된 서비스 계층”이 아니라 부분적으로 남아 있는 리팩토링 스캐폴드**다.

---

## P1-03. Controller 파일 자체가 심각한 중복 상태

AST 기준 주요 중복 정의:

| 항목 | 중복 정의 횟수 |
|---|---:|
| `busy` | 2 |
| `current_chapter` | 1 property + setter 구조가 중복/혼재 |
| `stop_current_job` | 2 |
| `check_current_chapter` | 2 |
| import `Job/StreamJob` | 9 |
| `MemoryManager` | 9 |
| `StateLedger` | 9 |
| `MasterDiffService` | 9 |
| `ProviderManager` | 7 |
| `AIEngine` | 7 |
| `ContextManager` | 7 |
| prompt imports | 7 |
| Writer/Plot/Planner 등 | 다수 |

이 정도 중복은 단순 가독성 저하가 아니라 **잘못된 최종 정의가 앞선 정상 구현을 덮어쓰는 실제 버그 원인**이다.

---

## P1-04. `stop_current_job()` 중복 후 최종 구현이 `pass`

앞쪽에는 실제 cancel 코드가 존재하지만 뒤에서 다시

```python
def stop_current_job(self):
    pass
```

로 정의된다.

Python에서는 뒤의 함수가 최종 적용된다.

따라서 코드만 보면 취소 기능을 구현했지만 실제 호출되는 메서드는 아무것도 하지 않는다.

---

## P1-05. Controller의 `audit_long_form()`는 실제 작업을 하지 않음

`novel_studio/controllers/novel_controller.py:392-407`

job 내부가

```python
def job():
    pass
```

이다.

즉 Controller 경유 장편 검사 API는 실제 구현이 없다.

MainWindow가 우회해서 `self.controller.continuity_service.audit_long_form()`을 직접 호출하기 때문에 겉으로 기능이 존재하는 것처럼 보일 뿐이다.

이 역시 “Controller가 작업 순서를 책임진다”는 기획과 맞지 않는다.

---

# 6. 장편 기억 / 연속성 설계 문제(P1)

## P1-06. 장편 정밀 검사에 실제 원고가 거의 사용되지 않음

**파일**

`novel_studio/plot/plot_manager.py:37-77`

검사에 사용하는 데이터는

```python
secs = self.db.sections_overlapping(s0, e0)
source = '\n'.join(r['content'] for r in secs)[:22000]
```

이다.

즉 실제 `chapters/*.txt` 원고를 직접 분석하는 것이 아니라 **스토리 구간 내용**을 대상으로 검사한다.

기획서에서는 장편 연속성을 다음 상태까지 관리하려고 했다.

```text
이전 화 종료 상태
현재 화 시작 상태
현재 화 사건
현재 화 종료 상태
다음 화 시작 상태
위치
부상
경지
소지품
관계
지식
목표
```

현재 정밀 감사는 이 모든 데이터를 직접 종합하지 않는다.

### 판정

**구간 플롯 연속성 검사에 가깝고, 실제 원고 장편 감사 시스템으로는 부족하다.**

---

## P1-07. 인물 Relevance가 실제 원장 데이터와 연결되지 않음

`Database.characters_relevant()`는 `character_states` 테이블을 참고한다.

하지만 현재 자동 기억 갱신은 `entity_state_ledger`에 상태를 저장한다.

즉

```text
실제 자동 갱신
 → entity_state_ledger

Context relevance
 → character_states
```

로 데이터가 갈라져 있다.

결과적으로 캐릭터 relevance가 실제 자동 상태 원장을 충분히 반영하지 못한다.

### 수정

`character_states`와 `entity_state_ledger` 중 하나를 canonical state store로 결정해야 한다.

현재 기획과 v1.4 계층형 기억 구조를 고려하면 `entity_state_ledger`를 중심으로 정리하는 편이 일관성이 높다.

---

## P1-08. 인물 관계 데이터 모델이 있지만 실제 기능이 없음

DB에는

```text
relationships
```

테이블이 존재한다.

하지만 프로젝트 전체 코드에서 관계 CRUD/UI/Context 통합 로직을 찾기 어렵다.

기획서는 인물 관계를 Story Engine의 핵심 책임으로 정의했다.

따라서 현재는

```text
스키마만 있음
```

상태에 가깝다.

### 수정

최소한 다음은 필요하다.

```text
관계 추가/수정/삭제
현재 관계 상태
관계 시작 화
관계 변화 이력
현재 화 기준 관계 조회
Context 포함
```

---

## P1-09. 아이템 관리가 아예 독립 모델로 구현되지 않음

기획서에는

```text
세력 / 장소 / 아이템
```

그리고 Story Engine 책임에

```text
아이템 관리
```

가 명시되어 있다.

하지만 현재 DB에는 전용 `items` 테이블과 CRUD가 없다.

따라서 현재 설정 DB는 사실상

```text
인물
세력
장소
복선
핵심 사건
시간축
```

구조다.

### 판정

기획 대비 **미구현 기능**이다.

---

## P1-10. 복선 이력 구조는 존재하지만 실제 사건 자동 생성이 약함

DB에는 `foreshadow_events`가 있고 `add_foreshadow_event()`도 존재한다.

그러나 원고 집필 → 기억 갱신 과정에서 실제 복선 등장/진척/암시/회수 사건을 자동 생성해서 관리하는 연결이 부족하다.

`save_foreshadow()` 시점에 현재 필드 값을 저장하는 것과 실제 원고의 사건 이력을 기록하는 것은 다르다.

### 결과

복선 “DB 구조”는 있지만 복선 “변화 추적 시스템”으로는 아직 부족하다.

---

# 7. Context / Retrieval 문제(P1~P2)

## P1-11. Context token budget이 실제로는 초과할 수 있음

`novel_studio/ai/context.py:121-146`

설명에는 `[USER REQUEST]`를 항상 유지한다고 되어 있다.

실제 구현도

```python
if blk.startswith('[USER REQUEST]'):
    keep.append(blk)
    used += need
```

로 예산 초과 여부와 관계없이 추가한다.

### 결과

사용자 입력이 길어지면 `context_budget_tokens`를 초과할 수 있다.

### 수정

최소한

```text
system/contract reserve
+ user request reserve
+ context budget
```

을 분리하고, 사용자 요청에 대해서도 상한을 둬야 한다.

---

## P1-12. Context의 “관련 데이터 선별”이 아직 충분히 지능적이지 않음

현재 retrieval은

- 현재 화 플롯
- 현재 스토리 구간
- 최근 요약
- 이전 상태
- 이전 화 tail
- 타임라인
- 사건
- 최근 entity state
- 검색 결과
- 인물 40개
- 세계 40개
- 복선 60개

등을 정해진 범위로 가져온다.

이것은 “전체를 넣지 않는다”는 점에서는 기획에 부합하지만, 500화 규모에서 **진짜 관련 엔티티만 골라내는 의미 기반 retrieval**과는 차이가 있다.

특히 현재 화에서 등장하는 인물/장소/세력/복선과 직접 관련이 없는 항목도 상당수 들어갈 수 있다.

### 개선 방향

```text
현재 화 플롯
 ↓
등장 엔티티 추출
 ↓
엔티티 관계/상태 조회
 ↓
복선/사건 연결 조회
 ↓
우선순위 점수화
 ↓
Context 구성
```

방식으로 발전시키는 것이 장기적으로 적합하다.

---

## P2-01. 토크나이저 처리 명칭이 “정확한 토큰 수”와 실제 구현이 다름

`ContextManager`는 OpenAI 계열이 아닌 Claude/Gemini/기타 모델에 `cl100k_base`를 근사치로 사용한다.

따라서 문서의 “정확한 토큰 수”라는 표현보다는

```text
토큰 예산 추정
```

이라고 정의하는 것이 맞다.

특히 LM Studio의 GGUF 계열 모델에서는 실제 tokenizer와 차이가 날 수 있다.

---

# 8. DB / 검색 무결성 문제(P1~P2)

## P1-13. Timeline FTS key 설계가 중복될 수 있음

`save_timeline()` 계열 코드에서는 chapter number를 ref key로 사용하는 구조가 있다.

여러 timeline event가 같은 화에 존재하면 동일한 `(category, ref_key)`가 될 수 있다.

검색 문서 테이블이

```text
UNIQUE(category, ref_key)
```

이므로 같은 화의 여러 timeline event가 하나의 검색 문서 키를 공유할 수 있다.

### 결과

검색 색인에서 일부 timeline 정보가 덮어써질 수 있다.

### 수정

```text
timeline:{id}
```

형태의 안정적인 고유 키를 사용해야 한다.

---

## P1-14. 검색 인덱스 재구축 범위가 실시간 색인 범위와 다름

`rebuild_search_index()`는 다음과 같은 핵심 데이터만 재구축한다.

- meta
- chapter plans
- characters
- world entities
- foreshadowing
- timeline
- major events
- summaries

그러나 현재 데이터 모델의 다른 상태 정보는 충분히 포함되지 않는다.

즉

```text
실시간 저장시 색인
≠
전체 재구축 후 색인
```

이 될 가능성이 있다.

### 결과

인덱스 재구축 후 검색 가능한 정보가 달라질 수 있다.

---

## P1-15. Entity State Ledger에 존재하지 않는 엔티티 이름이 들어갈 수 있음

`MemoryManager._extract_entities()`는 AI가 반환한 이름을 그대로 저장한다.

즉 실제 설정 DB에 등록되지 않은 이름이 들어와도 차단되지 않는다.

### 위험

AI가

```text
주인공
```

대신

```text
이준서
```

처럼 정확하게 쓰는 것이 아니라 임의 표현/별칭/오타를 생성하면 동일 인물이 여러 entity key로 분산될 수 있다.

### 수정

```text
AI 추출 이름
 ↓
canonical entity resolver
 ↓
정확한 entity ID
 ↓
원장 저장
```

구조가 필요하다.

---

## P1-16. Entity 추출 실패가 사용자에게 보이지 않음

`MemoryManager._extract_entities()`에서

```python
except Exception:
    pass
```

로 끝난다.

이 경우 엔티티 원장 갱신이 실패해도 UI는 성공한 것처럼 보일 수 있다.

### 설계상 문제

장편 기억 시스템에서는 “기억 갱신 실패”가 중요한 상태다.

최소한

```text
자동 갱신 성공
자동 갱신 일부 실패
자동 갱신 실패
```

정도는 사용자에게 보여야 한다.

---

# 9. 저장 / 데이터 무결성 문제(P1~P2)

## P1-17. 원고 파일과 DB 메타 저장 사이에 트랜잭션 경계가 없음

기획상 원고 본문은 파일, DB는 메타/상태다.

이 구조 자체는 좋다.

문제는 두 저장이 별도 동작이라는 점이다.

예:

```text
원고 파일 저장 성공
 ↓
DB 메타 저장 실패
```

또는 반대 상황이 가능하다.

### 결과

본문과 상태 정보가 순간적으로 불일치할 수 있다.

### 개선

저장 완료 순서를 명확히 정의하고 journal/dirty state를 두는 것이 좋다.

예:

```text
SAVE START
 ↓
원고 파일 atomic write
 ↓
DB metadata update
 ↓
state hash update
 ↓
SAVE COMMIT
```

실패하면 dirty 상태를 유지한다.

---

## P1-18. AI 결과가 “초안”인지 “확정 원고”인지 상태 체계가 약함

기획서에서는 AI가 생성한 내용은 확정 데이터가 아니고 사용자가 검토/채택해야 한다는 원칙이 중요하다.

하지만 현재 저장 흐름에서는 자동 저장/종료 저장으로 사용자가 명시적으로 확정하지 않은 텍스트가 `작성완료` 상태로 들어갈 여지가 있다.

특히 `closeEvent()`에서 저장을 수행하는 구조와 자동 저장이 있다.

### 개선

원고 상태를 최소 다음처럼 분리하는 것이 좋다.

```text
미작성
AI 초안
사용자 검토 중
확정
수정됨
검사 필요
```

---

# 10. UI 점검 결과

## 10.1 전체 배치

현재 메인 UI는 기본 방향 자체는 좋다.

```text
┌──────────────────────────────────────────────┐
│ 상단: 작품 / AI 상태 / 설정 / 정지           │
├──────┬────┬──────────────────┬────┬─────────┤
│ 좌측 │핸들│ 중앙 작업 영역   │핸들│ 우측 상태│
│ 메뉴 │    │                  │    │          │
├──────┴────┴──────────────────┴────┴─────────┤
│ 하단: 자동저장 / AI기호삭제 / 전체저장 / 비서 │
└──────────────────────────────────────────────┘
```

기획서의 “집필 흐름이 한눈에 들어오는 화면”이라는 방향과 크게 어긋나지는 않는다.

---

## P2-01. 메인 창의 최소 크기 보장이 없음

`main_window.ui`는

- leftPanel 최소 220 / 최대 360
- rightPanel 최소 290 / 최대 460
- 각 handle 26

으로 고정되어 있다.

초기 창은

```python
self.resize(1700, 1000)
```

이지만 사용자가 창을 축소하면 중앙 작업 영역이 빠르게 좁아질 수 있다.

### 개선

권장 최소 크기 예:

```text
1200 × 750
```

또는 중앙 원고 영역을 우선적으로 확보하도록 좌/우 패널을 자동 축소해야 한다.

---

## P2-02. 상단 대시보드 정보가 길어질 때 배치가 깨질 가능성

상단에

- 작품 제목
- 진행 화수
- 총 글자 수
- 활성 복선
- AI 상태
- 연결 테스트
- 설정
- 정지

를 함께 둔다.

작품 제목이 길거나 AI 모델명이 길면 수평 공간이 빠르게 부족해질 수 있다.

### 개선

- 작품명 elide
- 모델명 tooltip 처리
- 정보 카드를 중앙 대시보드로 분리
- AI 상태는 짧은 상태 아이콘 + tooltip

등이 좋다.

---

## P2-03. 설정 DB 화면 저장 UX가 위험함

현재 `save_entry()`가 현재 카테고리 전체를 순회해서 저장한다.

설정 저장 UI는 사용자에게

```text
[현재 항목 저장]
[카테고리 전체 저장]
```

가 명확히 보이는 것이 안전하다.

지금은 “저장” 버튼 하나가 내부적으로 전체 카테고리를 저장하기 때문에 데이터 오염 버그가 발생하기 쉽다.

---

## P2-04. Entities 화면의 단일 폼에 정보가 많음

인물은 현재

- 이름
- 역할
- 프로필
- 성격
- 말투
- 목표
- 비밀
- 아크

를 한 화면에 둔다.

기능 자체는 좋지만 긴 원고 프로젝트에서는 다음처럼 탭 또는 접기 구조를 적용하는 것이 더 읽기 좋다.

```text
기본 정보
성격 / 말투
목표 / 비밀
스토리 아크
현재 상태
관계
상태 이력
```

특히 관계/현재 상태가 추가되면 현재 구조는 더 복잡해질 가능성이 높다.

---

# 11. 하드코딩 점검

## 확인된 주요 하드코딩

### AI 파라미터

여러 모듈에 다음 값들이 개별적으로 들어간다.

```text
temperature=.72
.62
.60
.55
.38
.35
.25
.20
.18
.15
.10
```

그리고

```text
max_tokens=4500
5000
6000
9000
10000
12000
14000
16000
```

등이 기능별 코드에 흩어져 있다.

### 문제

모델이나 GPU 환경을 바꾸면 여러 파일을 직접 수정해야 한다.

### 권장

```text
AIProfile
├─ writing
├─ revision
├─ planning
├─ memory
├─ continuity
└─ extraction
```

형태의 중앙 설정을 만들 것을 권장한다.

---

## 기타 하드코딩

### 기본 창 크기

```python
1700, 1000
```

### LM Studio URL

```text
http://localhost:1234/v1
```

기본값 자체는 타당하지만 중앙 설정을 통해 관리하는 편이 좋다.

### 자동 저장

현재 선택지는 코드에 직접

```text
안 함
5분
10분
```

으로 정의되어 있다.

확장성을 고려하면 설정 파일에서 가져오는 편이 좋다.

### Context 기본 예산

```text
60000 tokens
```

등이 여러 파일에서 반복된다.

---

# 12. 예외 처리 문제

프로젝트에서 `except Exception:` 사용 위치가 상당수 확인되었다.

대략적인 검색 결과:

```text
22개 파일에서 사용
53개 구문
```

모든 것이 잘못된 것은 아니지만, 다음 영역에서는 특히 위험하다.

## 위험한 유형

### 1. 기억 시스템

```python
except Exception:
    pass
```

엔티티 추출 실패를 숨김.

### 2. DB 검색

FTS 오류가 나도 fallback 또는 pass로 지나가는 구조가 많아 실제 색인 문제를 발견하기 어렵다.

### 3. UI 스트리밍

토큰 표시 오류를 무조건 무시하면 사용자 입장에서는 AI가 멈춘 것으로 보인다.

### 4. 설정 로딩

모델 목록 조회 실패를 조용히 무시하면 빈 모델 목록만 보일 수 있다.

## 권장

예외를 최소한 다음 단계로 구분한다.

```text
recoverable
warning
error
fatal
```

그리고 UI에 필요한 오류만 사용자에게 표시한다.

---

# 13. 버전 및 배포 문서 문제(P1)

## P1-19. 버전 표기가 서로 다름

### 실제 버전

`version.txt`:

```text
1.4.5
```

### MainWindow

```python
Novel Studio v1.4.1
```

### About

```text
v1.4.1
```

### README

```text
Novel Studio v1.4.0
```

### CHANGELOG

최상단은 v1.4.5.

### 문제

사용자 화면/문서/파일이 서로 다른 버전을 표시한다.

### 수정

버전은 한 곳에서만 관리해야 한다.

예:

```text
novel_studio/version.py
VERSION = "1.4.5"
```

그리고

- About
- Window title
- README 생성
- 로그
- 패키지 메타

가 모두 이 값을 참조하게 해야 한다.

---

## P1-20. README가 실제 배포본과 불일치

README에는

```text
Windows: run_windows.bat
```

가 적혀 있지만 현재 압축본 최상위에는 `run_windows.bat`가 없다.

CHANGELOG에도 run_windows.bat 수정 기록이 있다.

### 판정

배포물 무결성 문제다.

---

## P2-05. generated `_ui.py` 파일이 실제로 사용되지 않는 것으로 보임

`forms/`에는 여러 `*_ui.py` 파일이 존재하지만 코드에서 직접 import하는 사용처가 확인되지 않았다.

현재 `loader.py`를 통해 `.ui`를 직접 로드하는 구조다.

### 결과

두 가지 UI 소스가 존재한다.

```text
.ui
_generated _ui.py
```

실제 기준 파일이 하나가 아니라는 혼란을 만든다.

### 권장

둘 중 하나만 사용한다.

- `.ui` runtime loading 유지 → generated Python 제거
- pyuic generated Python 사용 → runtime loader 제거

현재 구조에서는 `.ui` 직접 로딩을 유지하는 편이 단순하다.

---

# 14. 코드 품질 / 유지보수 문제(P2)

## P2-06. `PlotManager.ranges()` 중복 정의

`novel_studio/plot/plot_manager.py:6-7`와 `13-14`

완전히 동일한 함수가 중복되어 있다.

실행 버그 가능성은 낮지만 리팩토링 잔재다.

---

## P2-07. `dialogs.py`의 `__init__` 중복 정의

AST 기준 같은 이름의 `__init__`이 두 클래스에 존재하는 것은 정상일 수 있으나, 파일 구조를 단순 AST로만 볼 때 이름 중복이 탐지되는 형태다.

이 항목은 실질 버그로 분류하지 않지만 클래스 경계가 명확한지 재확인할 필요가 있다.

---

## P2-08. Controller에 MainWindow 참조 구조가 여러 형태로 존재

현재

```text
self.main_window
set_main_window()
_main_window_ref
set_main_window_ref()
```

같은 여러 방식이 혼재한다.

Controller가 View를 몰라야 한다는 관점에서 `main_window` 직접 참조 자체를 제거하는 것이 좋다.

---

## P2-09. Controller와 MainWindow에 별도의 ThreadPool이 존재

MainWindow:

```python
self.pool = QThreadPool(self)
self.pool.setMaxThreadCount(1)
```

Controller:

```python
self.pool = QThreadPool()
self.pool.setMaxThreadCount(1)
```

그런데 Controller의 실행 함수는 `self.pool`을 사용하지 않고 `QThreadPool.globalInstance()`도 사용한다.

### 결과

작업 실행기가 세 종류로 분리된다.

```text
MainWindow pool
Controller pool
Qt global pool
```

관리 기준이 불명확하다.

### 권장

**하나의 Application Job Manager**로 통합한다.

---

# 15. 기획과 구현 사이의 핵심 간극

기획서는 매우 명확한 철학을 갖고 있다.

> AI가 작품을 관리하는 것이 아니라 프로그램이 작품의 기준 데이터를 관리하고 AI는 그 데이터를 바탕으로 생성한다.

현재 구현은 이 철학을 절반 정도는 지키고 있지만, 실제 코드 구조에서는 MainWindow가 너무 많은 것을 직접 조정한다.

따라서 현재는

```text
[좋은 방향]
프로그램
 ├─ 작품 데이터 관리
 ├─ DB 관리
 ├─ 기억 관리
 ├─ Context 관리
 └─ AI 생성

[현재 구현]
MainWindow가 위 기능을 상당 부분 직접 호출
```

구조가 된다.

이 상태가 계속 유지되면 기능 추가 때마다 MainWindow가 계속 커지고, Controller/Service는 더 많은 죽은 코드와 중복을 가지게 된다.

---

# 16. 권장 최종 구조

v1.5 이후를 기준으로는 다음 구조로 단순화하는 것이 좋다.

```text
┌──────────────────────────────┐
│             UI               │
│ View / Dialog / Editor       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│        NovelController       │
│ 작업 순서 / 상태 / Signal    │
└───────┬───────────┬──────────┘
        │           │
        ▼           ▼
┌────────────┐ ┌───────────────┐
│ Story      │ │ Writing       │
│ Service    │ │ Service       │
└─────┬──────┘ └───────┬───────┘
      │                │
      └────────┬───────┘
               ▼
┌──────────────────────────────┐
│      Context / Memory        │
│ Retrieval / State / Ledger   │
└──────────────┬───────────────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
┌──────────────┐  ┌────────────┐
│ Project Data │  │ AI Engine  │
│ DB + Files   │  │ Providers  │
└──────────────┘  └────────────┘
```

핵심은 **UI가 Core 객체를 직접 만지지 않는 것**이다.

---

# 17. 수정 우선순위

## P0 — 반드시 먼저 수정

```text
1. Controller _run_stream callback 연결 수정
2. WritingServiceImpl / ChapterWriter streaming 계약 수정
3. check_current_chapter 중복 제거
4. stop_current_job 중복 제거 + current_job 저장
5. AIProvider.chat_stream 중복 제거
6. ThreadSafeDatabase 단일 connection/단일 API 구조로 정리
7. EntitiesView.save_entry 데이터 오염 버그 수정
8. audit_long_form 중첩 _run 제거 + UI Signal 처리
```

## P1 — 다음 단계

```text
9. MainWindow의 Core 직접 호출 제거
10. Service 구현체 완성
11. character_states / entity_state_ledger 통합
12. 관계 데이터 실제 CRUD/UI 구현
13. 아이템 데이터 모델 구현
14. 장편 감사가 실제 원고 + 상태까지 분석하도록 확대
15. 검색 색인 key 및 rebuild 범위 통일
16. Entity canonical resolver 추가
17. AI 초안/확정 상태 분리
18. 버전 단일화
19. README / 실제 배포 파일 일치
```

## P2 — 안정화/품질 개선

```text
20. AI 파라미터 중앙화
21. 예외 처리 등급화
22. generated _ui.py 정리
23. ThreadPool 하나로 통합
24. UI 최소 크기/반응형 개선
25. Entities UI 정보 그룹화
26. dirty state / save journal 도입
27. 자동 테스트 추가
```

---

# 18. 테스트 체계 권장안

현재 테스트가 없기 때문에 기능을 고쳤다고 확인할 수 있는 자동 기준이 없다.

최소 다음 테스트부터 만들어야 한다.

## 단위 테스트

```text
ContextManager
 ├─ budget 유지
 ├─ user request 제한
 └─ 우선순위 제거

StateLedger
 ├─ 저장
 ├─ 최신값 조회
 └─ 이전 화 조회

Entity parser
 ├─ 정상 JSON
 ├─ 잘못된 JSON
 └─ 중복 엔티티

Plot parser
 ├─ 정상 범위
 ├─ 누락 화
 └─ 중복 화
```

## Controller 테스트

```text
write
 ├─ token callback
 ├─ done callback
 ├─ error
 └─ cancel

revision
 ├─ token callback
 └─ done callback

continuity
 ├─ 정상
 └─ error
```

## 저장 테스트

```text
인물 10명
 ↓
3번 인물 이름 수정
 ↓
저장
 ↓
다른 9명 이름이 변경되지 않았는지 확인
```

이 테스트는 현재 P0-06 버그를 바로 잡아낼 수 있다.

---

# 19. 최종 평가

## 잘된 부분

현재 v1.4.5의 방향 자체는 좋다.

특히 다음 요소는 기획서와 일치한다.

- 프로젝트 단위 저장
- 원고 파일 / DB 메타 분리
- 장기 기억을 화/구간/아크로 나누는 구조
- Entity State Ledger 도입
- Context Manager 도입
- FTS 검색 도입
- Master Diff 기록 구조
- 화별 플롯/스토리 구간 관리
- 설정 DB의 구조화
- AI Provider 추상화
- AI 연결 테스트
- 원고 글자 수 보정
- 설정/플롯/기억/연속성을 하나의 프로젝트에서 다루는 방향

즉, **제품의 방향은 맞다.**

## 그러나 현재 문제

리팩토링 과정에서

```text
이전 구조
      +
새 Controller
      +
새 Service
      +
새 ThreadSafeDB
```

가 완전히 정리되지 않고 동시에 남아 있다.

이 때문에 “새 구조처럼 보이지만 실제로는 예전 구조가 실행을 담당하는” 혼합 상태가 되었다.

이 상태에서 기능을 더 추가하면 복잡도가 더 커진다.

---

# 20. 최종 결론 한 줄

**Novel Studio v1.4.5는 기획 방향과 핵심 기능의 뼈대는 제대로 잡혀 있지만, 실제 실행 계층은 아직 리팩토링 중인 상태이며, 현재는 기능 추가보다 Controller·Service·DB·Streaming의 P0/P1 구조 오류를 먼저 제거해야 하는 버전이다.**

