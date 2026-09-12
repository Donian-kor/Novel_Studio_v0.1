# Novel Studio v0.2

Python + PySide6 기반 로컬 AI 장편소설 집필 프로그램의 2차 프로토타입입니다.

## 주요 기능

- 프로젝트 생성/열기
- 실제 원고는 `chapters/001.txt` 같은 TXT 파일로 저장
- SQLite(`novel.db`)로 화/플롯/청크/AI 작업 상태 관리
- LM Studio OpenAI 호환 API 연결
- AI 마스터 기획 생성
- Plan Contract 추출 및 잠금
- 5화 단위(설정 가능) 청크 플롯 생성
- 전체 목표 화수까지 청크를 순차 생성하는 배치
- 완료된 청크의 Snapshot 저장
- 중단 후 미완료 청크부터 재개
- 화별 플롯 생성
- 이전 화 + 최근 상태 + 현재 청크를 조합하는 기본 Context Manager
- AI 이어쓰기
- AI 윤문
- 연속성 검사용 AI 호출
- 지정 범위 화 자동 집필(검토 전 단계의 실험 기능)

## 실행

1. LM Studio에서 Local Server를 시작합니다. 기본 주소는 `http://localhost:1234`입니다.
2. Python 3.11 이상을 권장합니다.
3. 아래 명령을 실행합니다.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 권장 첫 사용 순서

1. 새 작품 생성
2. `AI 기획` 탭에서 짧은 아이디어 입력
3. `AI 마스터 기획` 실행
4. `AI Contract 추출` 후 Plan Contract 확인/잠금
5. `전체 청크 자동 생성`으로 500화 플롯을 청크 단위로 생성
6. `청크 관리`에서 생성 결과를 확인
7. 원고 탭에서 화를 선택하고 화별 플롯/이어쓰기를 실행

## 데이터 구조

```text
프로젝트/
├─ novel.db
├─ project.json
├─ chapters/
├─ plans/
├─ snapshots/
├─ backups/
├─ exports/
└─ temp/
```

## v0.2의 범위와 한계

현재 청크 Snapshot은 플롯 결과의 구조화된 스냅샷과 원고 기반 경량 기록을 중심으로 합니다. 정식 인물/세계관/복선 엔티티 추출 및 자동 충돌 판정은 v0.3에서 확장하는 것을 전제로 합니다.

`범위 자동 집필`은 v0.2 실험 기능이며, 생성 결과를 자동으로 확정 저장합니다. 중요한 작품에서는 먼저 테스트 프로젝트로 검증하는 것을 권장합니다.
