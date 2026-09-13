# Novel Studio v1.4.0

장편 웹소설의 기획·설정·플롯·원고·장기기억·연속성 관리를 지원하는 데스크톱 집필 도구입니다.

## v1.4.0 Stable Long-form Story Intelligence
- 복선 이력(`foreshadow_events`)
- 화별 엔티티 상태 원장(`entity_state_ledger`)
- 현재 화 중심 Retrieval Engine
- SQLite FTS5 통합 검색(저장 시 자동 인덱싱, 실패 시 LIKE fallback)
- Master 변경 Diff 제안 기록
- 화별 플롯 배치 추적 및 계층형 범위 생성
- 구간 단위 장편 연속성 정밀 검사
- CHANGELOG는 `CHANGELOG.md` 하나만 누적 관리

## 원칙
- 원고 본문은 파일, DB는 메타/상태/색인 역할
- AI에는 전체 작품 대신 현재 화에 관련된 상태를 우선 공급
- 기존 설정을 AI가 자동 삭제하지 않고 변경 제안으로 기록

## 실행
Windows: `run_windows.bat`
Python: `python main.py`

## 테스트
`python -m compileall novel_studio`
`PYTHONPATH=. pytest -q`
