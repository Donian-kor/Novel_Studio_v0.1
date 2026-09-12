# Novel Studio v0.3

Python + PySide6 기반 로컬 AI 장편소설 집필 프로그램입니다.

## 핵심
- 원고는 `chapters/001.txt` 형식의 TXT 유지
- SQLite `novel.db`에 작품 기억/설정 저장
- LM Studio OpenAI 호환 API 사용
- 짧은 아이디어 → Master Plan → Plan Contract → 5화 Chunk → 화별 플롯 → 본문 집필
- Chunk Snapshot / Chapter Memory / 최근 4화 Sliding Memory
- 인물 / 세계관 / 시간축 / 복선 관리
- 연속성 검사
- 중단 지점부터 청크 재개
- 프로젝트 ZIP 백업

## 실행
Windows:
`run_windows.bat`

직접 실행:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

LM Studio에서 Local Server를 실행하고 기본 주소 `http://localhost:1234`를 사용합니다.

## 기존 v0.2 프로젝트
v0.3은 기존 `novel.db`를 열면 필요한 테이블을 `CREATE TABLE IF NOT EXISTS`로 보강합니다. 기존 원고/TXT/기존 플롯은 유지됩니다.
