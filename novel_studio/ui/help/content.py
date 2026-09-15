# -*- coding: utf-8 -*-
"""Novel Studio v1.5.1 내장 도움말."""

STYLE = """
body { font-family: 'Malgun Gothic'; font-size: 10pt; color: #E8E6E3; }
h1 { font-size: 20pt; color: #F5F3F0; }
h2 { font-size: 15pt; color: #D8C8A8; margin-top: 26px; border-bottom: 1px solid #555250; }
h3 { font-size: 12pt; color: #A8BCCF; margin-bottom: 4px; }
p, li, td, th { font-size: 10pt; color: #E8E6E3; line-height: 1.6; }
table { border-collapse: collapse; margin-top: 6px; margin-bottom: 10px; }
th { background-color: #4A4845; color: #F5F3F0; border: 1px solid #5E5B57; padding: 4px 8px; }
td { border: 1px solid #5E5B57; padding: 4px 8px; }
code { font-family: 'Consolas'; background-color: #3A3836; color: #EFD9A7; }
pre { font-family: 'Consolas'; background-color: #2E2D2C; border: 1px solid #5E5B57; padding: 8px; color: #E8E6E3; }
a { color: #9CC3E5; text-decoration: underline; }
b { color: #F5F3F0; }
"""

SEC_START = """
<h2 id="sec-start">1. 시작하기</h2>
<p>Novel Studio는 <b>기획 → 설정 → 스토리 → 원고 → 화 종료 상태 → 연속성 검사</b> 순서로 장편 웹소설을 관리합니다.</p>
<h3>새 프로젝트</h3>
<table>
<tr><th>항목</th><th>설명</th></tr>
<tr><td>작품명 / 장르 / 분위기</td><td>작품의 기본 정보입니다.</td></tr>
<tr><td>총 화수</td><td>목표 연재 분량입니다.</td></tr>
<tr><td>화당 목표 글자수</td><td>AI 집필 목표 분량입니다.</td></tr>
<tr><td>허용 오차</td><td>목표 글자수에서 허용할 범위입니다.</td></tr>
<tr><td>장기 스토리 구간</td><td>기본 50화 단위의 큰 서사 구간입니다.</td></tr>
<tr><td>세부 스토리 구간</td><td>기본 10화 단위로 장기 구간을 나눕니다.</td></tr>
</table>
<p>프로젝트 생성 후 <code>db/story.db</code>, <code>db/setting.db</code>, <code>db/manuscript.db</code>, <code>db/summary.db</code>가 생성됩니다. 실제 원고 본문은 <code>chapters/001.txt</code>와 같은 TXT 파일에 저장됩니다.</p>
"""

SEC_UI = """
<h2 id="sec-ui">2. 화면 둘러보기</h2>
<table>
<tr><th>영역</th><th>역할</th></tr>
<tr><td>상단 대시보드</td><td>작품명, 진행률, 전체 글자수, 활성 복선을 표시합니다.</td></tr>
<tr><td>좌측 메뉴</td><td><b>기획 / 설정 DB / 스토리 / 원고 / 화 종료 상태</b>를 전환합니다.</td></tr>
<tr><td>우측 상태 패널</td><td>현재 집필 화의 <b>직전 화 종료 상태</b>를 보여줍니다.</td></tr>
<tr><td>하단 바</td><td>자동 저장, AI 기호 정리, 전체 저장, AI 작품 비서를 제공합니다.</td></tr>
</table>
<p>AI 생성 중 다른 메뉴로 이동해도 작업 대상 화와 생성 버퍼는 UI 선택 상태와 분리되어 유지됩니다.</p>
"""

SEC_PLANNING = """
<h2 id="sec-planning">3. 기획</h2>
<p>작품 전체의 방향과 기준을 만듭니다.</p>
<ol>
<li>AI 아이디어 생성 또는 직접 입력</li>
<li>마스터 기획 생성</li>
<li>핵심 기준 추출 및 필요 시 잠금</li>
<li>전체 플롯 생성</li>
</ol>
<p>기획 내용은 AI의 상위 기준으로 사용됩니다. 생성 결과는 바로 확정하지 말고 직접 검토한 뒤 저장하는 것을 권장합니다.</p>
"""

SEC_ENTITIES = """
<h2 id="sec-entities">4. 설정 DB</h2>
<p>인물, 세력, 장소, 복선, 핵심 사건, 시간축 등 작품의 고정 설정을 관리합니다.</p>
<table>
<tr><th>기능</th><th>동작</th></tr>
<tr><td>+ 추가</td><td>현재 카테고리에 직접 레코드를 추가합니다.</td></tr>
<tr><td>AI로 생성/보완</td><td>저장된 마스터 기획을 근거로 항목을 생성하거나 보완합니다.</td></tr>
<tr><td>저장 / 삭제</td><td>선택 항목을 저장하거나 삭제합니다.</td></tr>
</table>
"""

SEC_STORY = """
<h2 id="sec-story">5. 스토리</h2>
<p><b>스토리 구간과 화별 플롯을 하나의 계층형 스토리 화면으로 통합</b>했습니다.</p>
<pre>장기 스토리 구간
  └─ 세부 스토리 구간
       └─ 화별 스토리(화 단위 연결 정보)</pre>
<h3>화면 사용법</h3>
<p>위쪽 왼쪽 목록에서 장기 구간을 선택하면 오른쪽 목록에 해당 장기 구간의 세부 구간만 표시됩니다. 세부 구간을 선택하면 아래 큰 편집 영역에 본문이 표시됩니다.</p>
<p>두 목록은 동시에 약 5행이 보이며 스크롤할 수 있습니다. 아래 편집 영역은 화면의 대부분을 사용해 장문 스토리를 검토·수정할 수 있습니다.</p>
<table>
<tr><th>기능</th><th>동작</th></tr>
<tr><td>AI 스토리 생성</td><td>전체 장기 구간을 순서대로 생성하고 각 장기 구간의 세부 구간도 생성합니다.</td></tr>
<tr><td>선택 구간 재생성</td><td>선택한 장기 또는 세부 구간만 교체 생성합니다.</td></tr>
<tr><td>전체 다시 생성</td><td>기존 스토리 내용을 새로 생성합니다.</td></tr>
<tr><td>저장</td><td>현재 선택한 스토리 내용을 즉시 저장합니다.</td></tr>
</table>
"""

SEC_MANUSCRIPT = """
<h2 id="sec-manuscript">6. 원고</h2>
<p>실제 웹소설 본문을 작성하는 화면입니다. 원고의 정본은 프로젝트의 <code>chapters/NNN.txt</code>입니다.</p>
<table>
<tr><th>기능</th><th>동작</th></tr>
<tr><td>AI 집필</td><td>현재 화를 시작할 때 화 번호를 고정하고, 기획·설정·스토리·직전 종료 상태를 선택해 집필합니다.</td></tr>
<tr><td>AI 문장 다듬기</td><td>현재 원고를 윤문합니다. AI가 안내문을 반환하면 원본을 복원합니다.</td></tr>
<tr><td>설정 충돌 검사</td><td>현재 원고와 저장된 설정/상태를 비교합니다.</td></tr>
<tr><td>저장</td><td>AI를 호출하지 않고 원고를 먼저 안전하게 저장합니다.</td></tr>
</table>
<h3>AI 작업 중 메뉴 이동</h3>
<p>AI 집필 중 메뉴를 이동해도 진행 중 원고가 사라지지 않습니다. 작업 대상 화가 고정되어 있으므로 다른 화를 열어도 생성 결과가 다른 화에 섞이지 않습니다.</p>
<h3>저장 안전성</h3>
<p>원고 저장은 AI 종료 상태 생성과 분리됩니다. 종료 상태 생성이 실패해도 원고 파일은 이미 저장된 상태로 유지됩니다.</p>
"""

SEC_END_STATE = """
<h2 id="sec-end-state">7. 화 종료 상태</h2>
<p>화 종료 상태는 <b>실제 원고에서 다음 화에 꼭 필요한 변화만 추린 연결 정보</b>입니다. 별도의 스냅샷 시스템이 아닙니다.</p>
<table>
<tr><th>항목</th><th>예시</th></tr>
<tr><td>핵심 사건</td><td>이번 화에서 실제로 발생한 주요 사건</td></tr>
<tr><td>인물 상태</td><td>부상, 행동, 감정, 관계 변화</td></tr>
<tr><td>현재 위치/시간</td><td>화 종료 시점의 장소와 시간</td></tr>
<tr><td>부상/경지/능력</td><td>실제 변화만 기록</td></tr>
<tr><td>획득 정보/아이템</td><td>다음 화에서 이어질 정보</td></tr>
<tr><td>미해결 사건 / 복선</td><td>후속 화로 넘어가는 요소</td></tr>
<tr><td>다음 화 연결</td><td>다음 화 시작에 필요한 직접 연결점</td></tr>
</table>
<p>우측 상태 패널에서 원고를 작성할 때는 현재 화가 아니라 <b>직전 화(N-1)의 종료 상태</b>가 표시됩니다. 예를 들어 398화를 쓰면 397화 종료 상태를 봅니다.</p>
<h3>자동 생성 설정</h3>
<p>AI 설정에서 <b>원고 저장 후 AI로 화 종료 상태 자동 생성</b>을 켤 수 있습니다. 기본값은 꺼짐이며, 꺼져 있으면 저장은 오직 로컬 파일/DB 저장만 수행합니다.</p>
"""

SEC_CONTINUITY = """
<h2 id="sec-continuity">8. 연속성 검사</h2>
<p>연속성 검사는 별도 기억 시스템이 아니라 <b>작품의 실제 데이터가 서로 맞는지 검증하는 기능</b>입니다.</p>
<p>검사 기준에는 현재 원고, 직전 화 종료 상태, 관련 설정 DB, 현재 스토리, 시간축, 사건, 인물 상태 등이 포함됩니다.</p>
<p><b>자동 수정은 하지 않습니다.</b> 문제 후보를 보여주고 사용자가 원고나 설정을 직접 수정하도록 설계되어 있습니다.</p>
"""

SEC_CHAT = """
<h2 id="sec-chat">9. AI 작품 비서</h2>
<p>현재 작품 DB와 현재 작업 화 컨텍스트를 참고해 질문에 답합니다. 대화 내용은 프로젝트 데이터에 저장됩니다.</p>
<p>AI 답변보다 작품 DB에 기록된 설정·스토리·종료 상태를 우선 확인하는 보조 도구로 사용하는 것이 좋습니다.</p>
"""

SEC_STORAGE = """
<h2 id="sec-storage">10. 저장 구조</h2>
<table>
<tr><th>파일</th><th>역할</th></tr>
<tr><td><code>db/story.db</code></td><td>기획, 전체 플롯, 장기/세부 스토리, 화별 스토리</td></tr>
<tr><td><code>db/setting.db</code></td><td>인물, 세계관, 세력, 복선, 시간축, 상태 원장</td></tr>
<tr><td><code>db/manuscript.db</code></td><td>화 메타데이터와 채팅 기록</td></tr>
<tr><td><code>db/summary.db</code></td><td>화 종료 상태와 연속성 검사 결과</td></tr>
<tr><td><code>chapters/NNN.txt</code></td><td>실제 원고 본문 정본</td></tr>
</table>
<p>기존 프로젝트를 열면 예전 <code>novel.db</code>의 필요한 데이터를 새 4개 DB로 한 번 이관합니다. 기존 파일은 삭제하지 않습니다.</p>
<p><b>스냅샷 기능은 v1.5.0에서 사용자 기능으로 제거되었습니다.</b> 과거 스냅샷 데이터는 새 기능에서 사용하지 않습니다.</p>
"""

SEC_PROJECT = """
<h2 id="sec-project">11. 프로젝트 관리</h2>
<p>메뉴바의 <b>프로젝트</b> 메뉴에서 새 프로젝트, 프로젝트 열기, 프로젝트 설정, 전체 원고 내보내기를 사용할 수 있습니다.</p>
<p>프로젝트 설정에서는 총 화수와 목표 글자수뿐 아니라 <b>장기 스토리 구간</b>과 <b>세부 스토리 구간</b> 크기를 변경할 수 있습니다.</p>
"""

SEC_AI = """
<h2 id="sec-ai">12. AI 설정</h2>
<table>
<tr><th>항목</th><th>설명</th></tr>
<tr><td>제공자 / Base URL / 모델 / API 키</td><td>사용할 AI 서버 연결 정보입니다.</td></tr>
<tr><td>연결 테스트</td><td>실제 연결을 확인한 뒤 성공한 설정을 저장합니다.</td></tr>
<tr><td>편집기 글꼴/색상</td><td>원고 편집기의 표시 설정입니다.</td></tr>
<tr><td>원고 저장 후 AI로 종료 상태 자동 생성</td><td>켜면 원고 저장 완료 후 백그라운드에서 종료 상태를 생성합니다. 원고 저장 자체는 AI와 무관합니다.</td></tr>
</table>
"""

SEC_SHORTCUTS = """
<h2 id="sec-shortcuts">13. 단축키</h2>
<table>
<tr><th>키</th><th>기능</th></tr>
<tr><td>F1</td><td>사용법 열기</td></tr>
</table>
<p>AI 작업 취소는 상단 <b>정지</b> 버튼을 사용합니다.</p>
"""

SEC_FAQ = """
<h2 id="sec-faq">14. 자주 묻는 질문</h2>
<p><b>Q. 원고를 쓰다가 다른 메뉴로 이동하면 사라지나요?</b></p>
<p>아니요. 집필 대상 화와 생성 버퍼를 별도로 보존합니다. 생성 완료 시 대상 화의 원고를 자동 보존합니다.</p>
<p><b>Q. 저장할 때마다 AI를 호출하나요?</b></p>
<p>아니요. 원고 저장은 AI 없이 수행됩니다. 종료 상태 자동 생성 옵션을 켠 경우에만 저장 후 별도의 AI 작업이 시작됩니다.</p>
<p><b>Q. 종료 상태 생성에 실패하면 원고도 사라지나요?</b></p>
<p>아니요. 원고는 먼저 저장되므로 종료 상태 생성 실패와 원고 저장 실패는 분리됩니다.</p>
<p><b>Q. 왜 예전 스냅샷이 보이지 않나요?</b></p>
<p>v1.5.0에서는 스냅샷을 공식 상태 관리 방식에서 제거했습니다. 다음 화에 필요한 정보는 화 종료 상태로 전달합니다.</p>
<p><b>Q. 스토리와 화별 플롯은 어디에 있나요?</b></p>
<p>둘을 하나의 <b>스토리</b> 화면으로 통합했습니다. 장기 구간 → 세부 구간 → 화별 스토리 구조로 관리합니다.</p>
"""

SECTIONS = [
    ('sec-start', '1. 시작하기', SEC_START),
    ('sec-ui', '2. 화면 둘러보기', SEC_UI),
    ('sec-planning', '3. 기획', SEC_PLANNING),
    ('sec-entities', '4. 설정 DB', SEC_ENTITIES),
    ('sec-story', '5. 스토리', SEC_STORY),
    ('sec-manuscript', '6. 원고', SEC_MANUSCRIPT),
    ('sec-end-state', '7. 화 종료 상태', SEC_END_STATE),
    ('sec-continuity', '8. 연속성 검사', SEC_CONTINUITY),
    ('sec-chat', '9. AI 작품 비서', SEC_CHAT),
    ('sec-storage', '10. 저장 구조', SEC_STORAGE),
    ('sec-project', '11. 프로젝트 관리', SEC_PROJECT),
    ('sec-ai', '12. AI 설정', SEC_AI),
    ('sec-shortcuts', '13. 단축키', SEC_SHORTCUTS),
    ('sec-faq', '14. 자주 묻는 질문', SEC_FAQ),
]

_HEADER = """
<h1 id="top">Novel Studio v1.5.1 사용법</h1>
<p>장편 웹소설 집필을 위한 AI 보조 프로그램입니다.</p>
<pre>기획 → 설정 DB → 스토리 → 원고 → 화 종료 상태 → 다음 화 집필 / 연속성 검사</pre>
<p>작품의 실제 원고가 가장 중요한 정본이며, 화 종료 상태는 다음 화에 필요한 최소 연결 정보로 사용됩니다.</p>
"""


def get_sections() -> list[tuple[str, str]]:
    return [(title, anchor) for anchor, title, _ in SECTIONS]


def get_help_html() -> str:
    return ''.join([_HEADER] + [html for _, _, html in SECTIONS])


def get_style() -> str:
    return STYLE
