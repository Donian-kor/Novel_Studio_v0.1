# Novel Studio v1.1.4

장편 웹소설의 **기획 → 설정 DB → 스토리 구간 → 화별 플롯 → 원고 → 기억/연속성**을 하나의 프로젝트에서 관리하는 Python + PySide6 기반 집필 도구입니다.

## v1.1.4 변경사항

- 메인 화면 하단의 중복된 현재/목표 글자수 표시 제거
- 현재 화 글자수는 원고 화면 하단에서만 표시
- 메인 대시보드의 총 글자수/화당 목표 글자수 표시는 유지

## 핵심 기능

- AI 아이디어 생성 및 확정
- AI 마스터 기획 생성 / 직접 수정 / 저장
- 핵심 기준(Plan Contract) 추출·잠금
- AI 전체 플롯 생성 / 직접 수정 / 저장
- 설정 DB 관리
  - 인물
  - 세력
  - 장소
  - 복선
  - 핵심 사건
  - 시간축
- **마스터 기획 → 설정 DB AI 자동 추가/갱신**
  - 남주 / 여주 / 조연 등 인물 추출
  - 세력 / 장소 / 복선 / 핵심 사건 / 시간축 추출
- 스토리 구간 AI 생성 / 상태 스냅샷 / 직접 수정 / 저장
- 화별 플롯 범위 생성 / 전체 생성 / 선택 개선 / 직접 수정 / 저장
- 화별 플롯 AI 응답 파싱 및 형식 오류 방어
- 원고 AI 집필 / 윤문 / 설정 충돌 검사 / 직접 수정 / 저장
- 기억·상태 스냅샷 및 연속성 관리
- AI 작품 비서
- LM Studio / OpenAI / Anthropic / Gemini / OpenAI Compatible 지원
- **설정 DB / 화별 플롯 / 원고 화면의 분할바(QSplitter)**
- 자동 저장 / 전체 저장 / AI 기호 삭제

## 권장 작업 순서

```text
아이디어
  ↓
마스터 기획
  ↓
설정 DB 자동 추가/보완
  ↓
핵심 기준(Plan Contract)
  ↓
전체 플롯
  ↓
스토리 구간
  ↓
화별 플롯
  ↓
원고 집필
  ↓
기억·연속성 갱신
```

각 단계의 결과는 다음 단계의 AI 컨텍스트로 사용되며, 사용자가 직접 수정한 내용도 저장 후 이후 작업에서 사용할 수 있습니다.

## 데이터 저장 구조

```text
프로젝트/
├─ project.json        # 작품/프로젝트 설정
├─ novel.db            # 기획·설정·플롯·기억·채팅 등 SQLite 데이터
├─ chapters/
│  ├─ 001.txt          # 1화 원고
│  ├─ 002.txt
│  └─ ...
├─ backups/
├─ exports/
└─ temp/
```

## 실행

### Windows

```bat
run_windows.bat
```

### 수동 실행

```powershell
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## AI 설정

AI 설정에서 제공자, Base URL, 모델, API Key를 지정합니다.

LM Studio 같은 로컬 서버를 사용할 경우:

1. LM Studio에서 로컬 서버를 실행합니다.
2. Novel Studio의 [AI 설정]에서 OpenAI Compatible 계열 설정을 지정합니다.
3. [연결 테스트]로 통신을 확인합니다.
4. 이후 AI 생성 기능을 사용합니다.

API Key는 프로젝트 코드에 직접 하드코딩하지 않는 것을 권장합니다.

## UI 편집

Qt Designer 화면 파일은 다음 위치에 있습니다.

```text
novel_studio/ui/forms/*.ui
```

주요 화면:

- `planning.ui`
- `entities.ui`
- `ranges.ui`
- `plots.ui`
- `manuscript.ui`
- `memory.ui`

### 패널 분할

다음 화면은 가운데 분할바를 드래그하여 목록/편집 영역의 폭을 조절할 수 있습니다.

- 설정 DB
- 화별 플롯
- 원고

설정 DB와 화별 플롯의 분할 위치는 프로그램 설정에 저장됩니다.

## 도움말

프로그램 실행 후 **도움말 → 사용법 (F1)**에서 현재 버전의 내장 도움말을 확인할 수 있습니다.

내장 도움말에는 실제 UI 기준으로 다음 내용이 포함됩니다.

- 전체 제작 흐름
- 각 화면의 버튼과 실제 동작
- 마스터 기획과 설정 DB 연동
- 스토리 구간 / 화별 플롯 / 원고 저장 방법
- 분할바 사용법
- AI 오류 대응
- FAQ

## 테스트

기본 문법 검사는 다음으로 수행할 수 있습니다.

```powershell
python -m compileall novel_studio main.py
```

화별 플롯 파서 테스트:

```powershell
python -m unittest tests/test_parser.py
```

## 버전

**v1.1.2**

이번 버전은 기능 변경에 맞춰 내장 도움말과 GitHub용 README를 실제 프로그램 동작 기준으로 정비한 버전입니다.
