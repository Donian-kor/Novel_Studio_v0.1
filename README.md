# Novel Studio v0.1

Python/PySide6 기반 로컬 AI 소설 집필 프로그램 프로토타입.

## 주요 기능
- 작품 프로젝트 생성/열기
- 화 목록과 TXT 원고 편집/저장
- LM Studio OpenAI 호환 API 연결
- AI 기획 생성
- 5화 단위 Chunk 플롯 생성
- 화별 플롯 작성
- 직전 화 기반 이어쓰기
- AI 결과 미리보기 후 원고 적용
- SQLite 프로젝트 DB
- 작품 폴더 자동 생성

## 실행

1. Python 3.11 이상 권장
2. 터미널에서 프로젝트 폴더로 이동
3. `python -m venv .venv`
4. Windows: `.venv\\Scripts\\activate`
5. `pip install -r requirements.txt`
6. `python main.py`

## LM Studio
LM Studio Developer 탭에서 서버를 켜고 기본 주소 `http://localhost:1234`를 사용합니다.
앱의 [AI 설정]에서 서버 주소와 모델을 확인한 후 연결 테스트를 실행하세요.

## 현재 버전의 범위
- 기획 → 청크 플롯 → 화 집필의 기본 흐름을 구현
- 고급 연속성/복선 자동 추출은 다음 버전에서 확장할 구조로 설계
