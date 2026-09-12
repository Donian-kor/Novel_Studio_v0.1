# Novel Studio v0.4

Python + PySide6 기반 장편 웹소설 집필 프로그램 프로토타입.

## 핵심
- TXT 원고 저장
- SQLite 프로젝트 관리
- LM Studio(OpenAI 호환 API) 연결 설정 UI
- 아이디어 1개 생성/재생성
- AI 마스터 기획
- 세계관/인물/세력/장소/수련체계/시간축/복선/핵심 사건별 AI 생성
- Plan Contract
- 스토리 구간(기본 5화) 단위 생성
- 화별 개별 플롯
- AI 채팅: 현재 화 컨텍스트 자동 포함
- AI 1화 집필 / 윤문 / 연속성 검사
- 실시간 원고 글자 수 표시

## 구조
`main.py`는 실행 진입점만 담당하고 기능별로 `core/db/ai/services/ui` 모듈을 분리했다.

## 실행
Windows에서 `run_windows.bat` 실행 또는:

```text
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python main.py
```

LM Studio Local Server 기본 주소는 `http://localhost:1234`.
