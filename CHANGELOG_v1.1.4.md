# Novel Studio v1.1.4 변경사항

## 글자수 표시 중복 수정

### 문제
- 메인 화면 하단과 원고 화면 하단에 현재 화 글자수가 중복 표시됨.
- `main_window.py::update_count()`가 두 개의 `countLabel`을 동시에 갱신함.

### 수정
- 메인 화면 하단의 `countLabel` 제거.
- 원고 화면(`ManuscriptPage`)의 `countLabel`만 유지.
- `update_count()`에서 원고 화면의 글자수 표시만 갱신하도록 변경.
- 메인 대시보드의 `총 글자수 / 화당 목표 글자수` 표시는 기존대로 유지.
- 도움말의 하단 바 설명을 최신 UI에 맞게 수정.

## 검증
- Python compileall 통과
- main_window.ui / main_window_ui.py의 메인 `countLabel` 제거 확인
- 원고 화면 `countLabel` 1개 유지 확인
