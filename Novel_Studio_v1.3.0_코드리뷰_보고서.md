# Novel Studio v1.3.0 코드 리뷰 보고서

**검토 대상**: `Novel_Studio` (PySide6 기반 장편 웹소설 집필 데스크톱 앱)
**검토 방식**: 전체 소스 정적 분석 + 의심 지점 실행 재현(파서·DB 계층 단위 테스트 직접 구동) + `compileall`/`unittest` 실행
**규모**: Python 약 60개 파일(자동생성 `ui/forms/*` 제외), `main_window.py` 909줄·`database.py` 369줄이 핵심 축

---

## 1. 총평

기획 의도는 매우 좋습니다. "화 단위 집필 → 요약/상태 압축 → 구간/아크 장기기억 → 컨텍스트 재주입"으로 이어지는 계층형 기억 구조, Plan Contract 잠금, 복선 이력 관리 등은 장편 웹소설 집필 도구로서 꽤 정교한 설계입니다.

다만 실제 코드를 뜯어보면 **"README/CHANGELOG가 광고하는 기능"과 "실제로 배선되어 동작하는 코드"사이에 간극이 반복적으로 발견됩니다.** v1.3.0의 핵심 세일즈 포인트 3개(계층형 배치 생성, FTS5 검색, 엔티티 상태 원장) 중 하나는 **버튼을 누르면 항상 에러가 나고**, 하나는 **인덱스가 한 번도 채워지지 않아 항상 껍데기**이며, 하나는 **이름만 다른 채 기존 기능을 중복 저장**하고 있습니다. 또한 UI 폴더의 약 1/3이 죽은 코드이고, 문서화된 테스트 실행 명령이 테스트의 절반가량을 조용히 건너뜁니다.

기능을 더 추가하기보다, **이미 만들어 놓은 것을 실제로 연결하고 검증하는 안정화 스프린트**가 다음 버전에 가장 필요해 보입니다.

---

## 2. 🔴 치명적 문제 — 재현 확인됨

### 2.1 "계층형 화별 플롯 생성" 기능이 실행할 때마다 100% 실패

- **위치**: `novel_studio/plot/plot_manager.py :: PlotManager.generate_hierarchical_plans()`
- **증상**: `parse_chapter_plans()`는 `(화번호, 제목, 본문)` **튜플의 리스트**를 반환하는데, 이 메서드는 `p['chapter_number']`, `p['title']`, `p['content']`처럼 **딕셔너리로 접근**합니다.
- **재현**: 실제로 실행해 아래 오류를 확인했습니다.
  ```
  TypeError: tuple indices must be integers or slices, not str
  ```
- **영향 범위**: `ui/main_window.py`의 `generate_hierarchical_plots()`가 이 메서드를 그대로 호출하며, `PlotsView`의 `hierBtn`(화별 플롯 화면의 "구간별/계층형 플롯 생성" 버튼)에 연결되어 있습니다. 즉 **UI에서 클릭 가능한 정식 기능이며, 예외 없이 항상 크래시**합니다.
- **흥미로운 점**: 바로 옆의 일반 경로(`main_window.py::_generate_plans_worker`)는 같은 `parse_chapter_plans()`를 `for n, title, body in plans:`로 올바르게 언패킹합니다. 즉 한쪽 경로만 고쳐지지 않은 채 남은, 전형적인 "부분 수정" 버그입니다.
- **수정 제안**:
  ```python
  for n, title, body in plans:
      self.db.save_chapter_plan(n, title, body, '초안')
  ```
- **이 버그가 테스트로 못 걸러진 이유**: `tests/test_parser.py`는 파서의 반환값이 튜플임을 정확히 검증하고 있지만(`p[0], p[1]`), `plot_manager.py`에는 테스트가 **전혀 없습니다**.

### 2.2 "SQLite FTS5 통합 검색" — 인덱스가 항상 비어 있음

- **위치**: `novel_studio/db/database.py :: _index_doc()`, `rebuild_search_index()`
- **증상**: 두 메서드 모두 검색 인덱스(`search_documents`/`search_fts`)를 채우는 유일한 경로인데, **코드베이스 전체에서 단 한 곳도 호출하지 않습니다.** (`grep` 전수 조사로 확인)
- **실질적 영향**: `Database.search()`는 "FTS5 우선, 실패 시 LIKE fallback" 구조로 짜여 있지만, 인덱스가 항상 비어 있으므로 **매번 자동으로 LIKE fallback 경로만 실행**됩니다. 예외가 발생하지 않기 때문에 사용자나 개발자 모두 이 사실을 눈치채기 어렵습니다.
- **부수 피해(성능)**: LIKE fallback은 토큰마다 최대 10개 테이블을 `LIKE '%token%'`으로 순차 전수 스캔합니다. 이 경로는 `[DB 검색]` 버튼과 **AI 채팅을 보낼 때마다(매 메시지)** 실행되므로, 화수·설정 항목이 많아질수록(README가 표방하는 "장편, 최대 5000화" 시나리오) 채팅 응답 지연이 누적될 소지가 큽니다.
- **수정 제안**: 각 테이블의 `save_*()` 메서드 끝에서 해당 문서를 `_index_doc()`으로 즉시 갱신하거나, 앱 시작/프로젝트 열기 시 `rebuild_search_index()`를 1회 호출하도록 배선.

### 2.3 `RetrievalEngine`의 검색 결과가 실제로는 버려짐

- **위치**: `novel_studio/intelligence/retrieval.py` ↔ `novel_studio/ai/context.py`
- `RetrievalEngine.retrieve()`는 `'search': self.db.search(query, 25)`를 계산하지만, 이를 소비하는 `ContextManager.build()`는 반환 딕셔너리에서 `search` 키를 **한 번도 읽지 않습니다.**
- 대신 `main_window.py::send_chat()`가 `self.db.search(msg, 40)`을 별도로 다시 호출해 `[DB SEARCH EVIDENCE]`로 수동 접합합니다. 설계 의도(Retrieval Engine을 통한 일원화된 컨텍스트 조립)와 실제 구현(중복 호출 + 죽은 코드 경로)이 어긋나 있습니다.

### 2.4 문서화된 테스트 명령이 테스트의 절반을 조용히 건너뜀

- README가 안내하는 실행법: `PYTHONPATH=. python -m unittest discover -s tests -v`
- 직접 실행한 결과 **`tests/test_parser.py`의 4개만 실행되고, `tests/test_database.py`의 3개(페이지네이션/인덱스/계층형 기억 저장 검증)는 전혀 실행되지 않습니다.**
- 원인: `test_database.py`는 pytest 스타일로 `tmp_path` 픽스처를 인자로 받는 **일반 함수**로 작성되어 있어(`unittest.TestCase` 아님), `unittest discover`가 이를 테스트로 인식하지 못합니다. (pytest로 직접 함수를 호출해 보면 3개 모두 정상 통과함을 확인했습니다 — 테스트 자체는 멀쩡합니다.)
- **위험성**: 신뢰하고 있는 검증 절차가 실제로는 DB 계층을 전혀 검사하지 않고 있다는 뜻이라, "테스트가 통과하니 안전하다"는 판단이 틀릴 수 있습니다.
- **수정 제안**: `requirements`에 `pytest` 추가 후 `pytest tests/`로 통일하거나, `test_database.py`를 `unittest.TestCase` + `tempfile.TemporaryDirectory`로 재작성.

### 2.5 로그 폴더 경로 계산 오류

- **위치**: `novel_studio/logging_config.py :: setup_logging()`
- `log_dir = Path(__file__).resolve().parents[2] / 'logs'`
- 실제 경로 깊이를 계산해보면(`.../Novel_Studio/novel_studio/logging_config.py` 기준) `parents[2]`는 **프로젝트 폴더(`Novel_Studio/`) 자체가 아니라 그 상위 폴더**입니다. 즉 로그가 앱 폴더 밖, 사용자가 앱을 압축 해제한 위치의 부모 디렉터리에 생성됩니다.
- 사용자 환경에 따라(예: 쓰기 권한이 없는 위치에 설치된 경우) 조용히 로깅 자체가 실패할 수 있고(`except Exception: pass`), 정상 동작하더라도 로그 위치가 사용자의 직관과 어긋나 트러블슈팅을 어렵게 만듭니다.
- **수정 제안**: `parents[1]`로 수정(=`Novel_Studio/logs/`), 혹은 `main.py`에서 프로젝트 루트를 명시적으로 전달.

---

## 3. 🟠 "있는 줄 알았던" 기능들 — 이름은 있지만 비어있는 구현

| 기능/자산 | 광고/의도 | 실제 상태 |
|---|---|---|
| `entity_state_ledger` (화별 엔티티 상태 원장) | 인물/장소 등 **엔티티별** 상태를 화 단위로 추적 | `kind='chapter'` 한 종류로만 기록되어 `chapter_states`와 사실상 동일한 데이터를 중복 저장. 조회 메서드 `StateLedger.latest()`는 어디서도 호출되지 않음 |
| `backups/`, `exports/`, `temp/` 폴더 | 도움말에 "백업·내보내기·임시 파일용"이라 명시 | 프로젝트 생성 시 폴더만 만들고, 이 세 경로에 실제로 쓰는 코드가 **전무**. 백업 기능도, 내보내기(export) 기능도 존재하지 않음 |
| `core/settings.py :: SettingsManager` | (추정) 초기 설계상의 설정 접근 계층 | 코드베이스 어디에서도 import되지 않는 완전한 죽은 클래스. 게다가 `get_meta()`/`get_plan()`은 `Database`가 이미 문자열을 반환하는데도 `row["value"]`처럼 재차 인덱싱을 시도해, **실제로 쓰였다면 그 자체로도 크래시**했을 코드 |
| `ui/views/sections.py`(126줄) | 파일명상 "스토리 구간" 화면으로 추정 | 실제로는 오래된 `EntitiesView` 복제본이 통째로 남아있는 파일. `views/__init__.py`에 import되지 않는 완전한 미사용 파일 |
| `ui/views/dashboard.py`, `ui/views/idea.py` | 독립 대시보드/아이디어 화면 | 둘 다 `__init__.py` 미등록, 어디서도 참조되지 않음. 실제 대시보드는 `main_window.py::_build_top_dashboard()`가, 아이디어 화면은 `PlanningView`가 각각 별도로 재구현하고 있음 |

죽은 코드 자체는 즉각적인 버그는 아니지만, **다음 개발자(혹은 AI 어시스턴트)가 이 파일들을 "진짜 사용 중"이라 오인하고 수정하다 시간을 낭비할 위험**이 커서 정리 우선순위가 높습니다.

---

## 4. 🟠 성능·확장성

- **페이지네이션 API는 있는데 UI가 아무도 안 씀**: `database.py`는 CHANGELOG v1.2.0에서 "무제한 전체 조회 축소"를 명시하며 `limit`/`offset` 파라미터를 대부분의 조회 메서드에 마련해 두었습니다. 그런데 실제 UI 레이어(`main_window.py`, `views/*.py`) 전체를 검색해보면 **`limit=`을 쓰는 곳은 채팅 로그 2곳(`chat_messages(limit=200)`)뿐**입니다. `_load_chapters()`, `RangesView.refresh()`, `PlotsView.refresh()`, `EntitiesView._rows()`는 모두 화수·구간·플롯·인물·복선 테이블을 **무제한 전체 로딩**합니다. "5000화 입력 지원"을 표방하는 앱에서, 5000개 화/플롯 항목을 매번 `QListWidget`에 통째로 채우는 구조는 화면 전환마다 체감 지연을 유발할 가능성이 높습니다.
- **컨텍스트 조립에 토큰 예산 개념이 없음**: `ai/context.py`는 각 블록을 문자 수(`[:8000]`, `[:9000]` 등)로만 자릅니다. 모든 블록을 합치면 8만 자를 훌쩍 넘을 수 있는데, 이는 토큰 수와 무관한 단순 문자 자르기라 LM Studio로 구동하는 로컬 소형 모델처럼 컨텍스트 창이 작은 모델에서는 요청이 잘리거나 실패할 수 있습니다.
- **위 2.2의 LIKE fallback**과 결합하면, 채팅 한 번 보낼 때마다 "최대 10개 테이블 전수 스캔 + 8만 자 컨텍스트 조립"이 겹쳐 실행되는 구조입니다.

---

## 5. 🟡 AI 프로바이더 계층의 일관성 문제

- **Anthropic 프로바이더가 `temperature`/`top_p`를 무시**: `providers/anthropic.py::chat()`은 두 값을 인자로 받기만 하고 요청 바디에 넣지 않습니다. `providers/gemini.py`, `providers/openai_compatible.py`는 정상적으로 반영합니다. → Anthropic 사용자만 창의성/다양성 설정이 항상 무시됨.
- **실시간 스트리밍이 프로바이더별로 다름**: `chat_stream()`을 실제로 오버라이드해 진짜 SSE 스트리밍을 구현한 곳은 `OpenAICompatibleProvider`(LM Studio 포함)뿐입니다. Anthropic/Gemini는 `AIProvider.chat_stream()` 기본 구현(전체 응답을 기다렸다가 한 번에 yield)으로 폴백되어, UI에서는 "실시간 집필"이라 되어 있어도 실제로는 완료 후 한꺼번에 붙여넣기처럼 보일 수 있습니다.
- **`ChapterWriter`가 사용자가 설정한 `max_tokens`를 무시**: `chapter_writer.py`는 항상 `max(9000, target*2)`를 자체 계산해서 사용합니다. [설정] 화면의 AI `max_tokens` 값은 집필 시에는 반영되지 않아, 비용 민감한 사용자가 설정을 낮춰도 실제 집필 요청은 그보다 큰 토큰으로 나갈 수 있습니다.
- **`MasterDiffService.propose()`의 JSON 파싱이 취약**: AI가 지시(`JSON만 출력`)를 어기고 코드펜스(\`\`\`json)로 감싸 응답하면 `raw.strip().startswith('[')` 체크에 걸려 **조용히 빈 변경 목록으로 처리**됩니다(에러 없음). 반면 `utils/entity_parser.py::parse_entity_catalog()`는 펜스를 벗겨내는 견고한 처리를 이미 갖추고 있는데, `diff.py`는 이 로직을 재사용하지 않고 있습니다.
- **집필 후 길이 보정 재귀에 상한이 없음**: `main_window.py::_after_write()`는 글자 수가 허용 오차 밖이면 `writer.adjust()`를 호출하고 다시 `_after_write`로 돌아갑니다. 모델이 계속 목표 범위를 못 맞추는 경우(특히 로컬 소형 모델) 이 사이클에 **최대 재시도 횟수 제한이 없어**, 사용자가 직접 정지 버튼을 누르지 않는 한 API 호출이 계속 나갈 수 있습니다. 유료 API 사용자에게는 비용 리스크입니다.

---

## 6. 🟡 데이터 안정성

- **원고 저장이 원자적이지 않음**: `core/project.py::save_chapter()`는 `path.write_text(...)`로 대상 파일을 직접 덮어씁니다. 저장 도중 강제 종료/정전이 발생하면 해당 화 파일이 손상되거나 비워질 수 있습니다. 임시 파일에 쓴 뒤 `os.replace()`로 교체하는 원자적 저장 패턴이 안전합니다. 이미 만들어져 있는(그러나 미사용인) `backups/` 폴더를 저장 시점 스냅샷 용도로 활용하면 더 좋습니다.
- **DB 스키마 마이그레이션 체계 부재**: `_schema()`는 `CREATE TABLE IF NOT EXISTS`만 사용하며 버전 관리·`ALTER TABLE` 경로가 없습니다. CHANGELOG에 이미 "기존 `story_sections.snapshot`, `summaries`, `chapter_states`는 호환성을 위해 유지"라는 문구가 등장하는데, 이는 스키마를 정리하지 못하고 계속 옆에 쌓아가는 패턴이 시작됐다는 신호입니다. 장기적으로 컬럼 이름 변경/정규화가 필요해질 때 대응이 어려워집니다.

---

## 7. 🟡 코드 품질·유지보수성

- **극단적으로 압축된 스타일**: `database.py`, `main_window.py`, `plot_manager.py` 등 핵심 로직 다수가 세미콜론으로 여러 문장을 한 줄에 이어 붙인 형태입니다(`database.py`의 여러 줄이 200자 이상). 기능은 동작하지만 diff 리뷰, 브레이크포인트 디버깅, 향후 유지보수 난이도를 크게 높입니다.
- **`main_window.py`가 909줄짜리 God Object**: UI 위젯 배선, 백그라운드 잡 오케스트레이션, AI 프롬프트 조립, DB 접근, 파일 저장이 한 클래스에 모두 뒤섞여 있습니다. 예: `write_current` → `_after_write` → `memory_job`(내부에서 메모리 갱신 + 연속성 검사 동시 실행) 흐름이 전부 `MainWindow` 메서드로 구현되어 있어, 이 로직을 UI 없이 단위 테스트하기가 사실상 불가능합니다.
- **광범위한 `except Exception: pass`**: `database.py::close()`, `_index_doc()`, `rebuild_search_index()` 등 다수 지점에서 오류를 조용히 삼킵니다. 특히 `_index_doc()`의 실패는 2.2번 문제를 은폐하는 데 일조했을 가능성이 있습니다.
- **채팅 UI가 실제로는 대화 맥락을 기억하지 못함**: `send_chat()`이 모델에 보내는 메시지는 `[system(컨텍스트), user(이번 메시지)]` 뿐입니다. 화면에는 과거 대화 로그가 200개까지 표시되지만, 실제 API 호출에는 **이전 턴이 전혀 포함되지 않습니다.** 사용자가 "방금 그거 좀 더 설명해줘"라고 하면 모델은 맥락을 알 수 없습니다. 화면 표시와 실제 동작이 달라 혼란을 줄 수 있는 부분입니다.
- **`EntitiesView._store_catalog()`의 카운트 로직이 혼란스러움**: '인물' 분기만 `count += 1; continue`가 빠져 있고, 루프 맨 끝의 별도 `if cat=='인물' ...: count += 1`로 흘러들어가 우연히 정상 동작합니다. 결과는 맞지만, 이후 누군가 '인물' 분기에 `continue`를 무심코 추가하면 카운트가 조용히 틀어지는 함정이 있습니다.

---

## 8. 🟢 잘 되어 있는 부분 (긍정 평가)

공정한 평가를 위해 잘 짜인 부분도 짚습니다.

- **API 키를 `keyring`으로 관리**하고 평문 설정 파일에는 저장하지 않으며, 입력란도 `QLineEdit::Password`로 마스킹되어 있습니다.
- **연결 테스트 성공 시에만 설정을 저장**하는 UX(`AISettingsDialog.test()`) — 잘못된 설정이 남는 것을 방지하는 세심한 설계입니다.
- **취소 가능한 백그라운드 Job 구조**(`jobs/worker.py`)와 스트리밍 UI, 자동 저장 실패를 사용자에게 항목별로 알려주는 `save_all()`의 실패 처리 로직은 완성도가 높습니다.
- **`plot/parser.py`의 다양한 AI 헤더 포맷 파싱**은 정규식 우선순위·중복 제거까지 꼼꼼히 처리되어 있고, 이에 대응하는 유닛 테스트(`test_parser.py`)도 실제 엣지 케이스(레거시 헤더, 누락 화 탐지)를 잘 다룹니다. 이 모듈은 리뷰한 코드 중 가장 신뢰도가 높습니다.
- **화 번호 파싱 실패 시 누락분만 1회 보완 생성**하는 재시도 로직(`main_window.py::_generate_plans_worker`)은 AI 출력의 불안정성을 실용적으로 흡수하는 좋은 패턴입니다.

---

## 9. 우선순위별 조치 제안

| 우선순위 | 항목 | 근거 |
|---|---|---|
| **P0 (즉시)** | `plot_manager.generate_hierarchical_plans()` 튜플/딕셔너리 접근 수정 | 버튼 클릭 시 100% 크래시, 재현 확인됨 |
| **P0** | 검색 인덱스 갱신을 실제 저장 경로에 연결 | 핵심 기능이 항상 비활성 상태로 조용히 동작 |
| **P0** | `unittest discover`가 `test_database.py`를 건너뛰는 문제 해결 (pytest 도입 권장) | 검증 절차 자체에 대한 신뢰 문제 |
| **P1** | 원고 저장 원자화(temp write + replace) + `backups/` 실제 활용 | 데이터 유실 위험 |
| **P1** | Anthropic 프로바이더 temperature/top_p 반영, 스트리밍 지원 | 프로바이더 간 동작 불일치 |
| **P1** | 집필 후 길이 보정 재귀에 최대 재시도 횟수 도입 | 비용 폭주 리스크 |
| **P1** | 죽은 파일 정리: `core/settings.py`, `ui/views/sections.py`, `dashboard.py`, `idea.py` | 유지보수 혼선 방지 |
| **P2** | UI 리스트 위젯에 기존 페이지네이션 API 연결 | 대규모 프로젝트 성능 |
| **P2** | `MasterDiffService`가 `entity_parser`의 펜스 제거 로직 재사용 | 조용한 실패 방지 |
| **P2** | 로그 디렉터리 경로(`parents[2]`→`parents[1]`) 수정 | 잘못된 위치에 로그 생성 |
| **P3** | `main_window.py` 책임 분리 (Job 오케스트레이션 / DB 접근 / 프롬프트 조립을 별도 계층으로) | 장기적 유지보수성 |

---

## 10. 다음 버전을 위한 아이디어

1. **토큰 기반 컨텍스트 예산 매니저**: 문자 수 자르기 대신 프로바이더별 컨텍스트 한도를 설정에 반영해, 블록별 우선순위(예: PLAN CONTRACT > 직전 화 상태 > 참고 자료)에 따라 동적으로 배분.
2. **`entity_state_ledger`를 이름값대로 활용**: 화 집필 완료 시 요약/상태 추출과 별개로, AI에게 "이번 화에서 상태가 변한 인물/장소만" 추출시켜 `kind='character'`, `entity_key=인물명`으로 개별 기록 → 인물별 타임라인 조회 화면을 새로 만들 수 있는 기반이 됩니다.
3. **저장 시점 인덱싱**: `save_character`, `save_world`, `save_chapter_plan` 등 저장 메서드 안에서 `_index_doc()`을 함께 호출하도록 리팩터링하면, 별도의 "재색인" 버튼 없이도 항상 최신 상태의 FTS 인덱스를 유지할 수 있습니다.
4. **DB 마이그레이션 프레임워크**: `meta` 테이블에 스키마 버전을 기록하고, 순차 적용되는 마이그레이션 스크립트 목록을 두는 경량 구조(라이브러리 도입 없이도 50줄 내외로 구현 가능) 도입.
5. **가상 스크롤/지연 로딩 리스트**: 화수·플롯이 수천 개로 늘어나는 시나리오를 이미 상정한 앱이므로, `QListWidget`을 모델/뷰(`QAbstractListModel`) 기반으로 교체하고 `limit`/`offset`을 실제로 연결.
6. **CI 파이프라인**: `python -m compileall`과 `pytest`를 GitHub Actions 등으로 자동화해, 이번에 발견된 것과 같은 "죽은 호출 경로" 버그를 병합 전에 잡을 수 있는 안전망 마련.
7. **채팅에 실제 대화 이력 반영**: 최근 N턴을 `send_chat()`의 `messages` 배열에 포함시켜, 화면에 보이는 대화와 모델이 실제로 아는 맥락을 일치시키기.

---

*본 보고서는 정적 분석과 일부 모듈의 직접 실행 재현을 기반으로 작성되었습니다. PySide6 등 GUI 의존성은 이 환경에서 설치할 수 없어 UI 동작 자체를 실제 기동해 검증하지는 못했으며, 해당 부분은 코드 경로 추적을 통한 논리적 검증에 근거합니다.*
