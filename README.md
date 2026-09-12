# Novel Studio Final v1.0

장편 웹소설용 Python + PySide6 + Qt Designer + SQLite + TXT 기반 프로그램.

## 시작 흐름
프로그램 실행 → **새 프로젝트 만들기 / 기존 프로젝트 불러오기 / AI·편집기 설정**.

## 제작 흐름
아이디어(직접 입력 또는 AI 1개 시안 생성/교체) → AI 마스터 기획 → 세계관/수련체계/세력/장소/인물/시간축/복선/핵심 사건 AI 생성·개선 → 핵심 기준(Plan Contract) → 전체 플롯 → 5화 기본 스토리 구간 생성 → 화별 플롯 → AI 작품 비서에서 `1화 써줘` → 목표 글자 수 보정 → 원고 확인/저장 → 기억·상태·연속성 갱신.

## 데이터
- 원고: `chapters/001.txt` 등 TXT
- 구조화 정보: `novel.db` SQLite
- 프로젝트 설정: `project.json`

## AI Provider
LM Studio / OpenAI / Anthropic / Google Gemini / OpenAI Compatible.
API Key는 keyring을 사용해 OS 보안 저장소에 저장하도록 설계.

## UI 유지보수
화면 레이아웃은 `novel_studio/ui/forms/*.ui`에 분리. Qt Designer에서 직접 수정 가능.

## 실행
Windows: `run_windows.bat`
수동: `py -3 -m venv .venv` → `.venv\Scripts\activate` → `pip install -r requirements.txt` → `python main.py`
