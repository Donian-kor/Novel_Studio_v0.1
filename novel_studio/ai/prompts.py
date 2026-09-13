SECTIONS=['세계관','세력','장소','인물','시간축','복선','핵심 사건']
SPEC={'세계관':'세계의 층위, 역사, 법칙, 문화, 종족, 공간, 시간, 인과. 장르의 특성에 맞는 세계 법칙 중심.','세력':'목적, 지도자, 조직, 자원, 영역, 동맹/적대, 주요 인물, 장기 변화.','장소':'위치, 환경, 특징, 위험, 역사, 관련 세력/인물/사건.','인물':'외형, 성격, 말투, 가치관, 목표, 욕망, 약점, 능력, 비밀, 성장선, 최종 상태.','시간축':'화수와 세계관 시간을 연결하고 시간 도약 및 주요 사건 시점을 설계.','복선':'장기 복선의 첫 암시, 강화, 부분 공개, 진실 공개, 최종 회수.','핵심 사건':'초중후반 주요 사건과 인과관계, 전환점, 최종 사건.'}

# 장르 프리셋: 아이디어/기획 프롬프트에 장르 특화 지침을 주입한다.
GENRES = ['선협', '무협', '판타지', '로맨스', '현대', '스릴러', '호러', 'SF', '역사', '게임', '직접 입력']
GENRE_GUIDE = {
    '선협': '수련·경지·문파·비경·기연 중심. 약소→강대 성장 서사.',
    '무협': '문파·강호·의리·복수·비급 중심의 정통 무협.',
    '판타지': '마법·종족·길드·던전·용 중심 서양 판타지.',
    '로맨스': '남녀 주인공의 감정선·갈등·설렘·해피엔딩 중심.',
    '현대': '현대 한국 배경, 직장·학교·가족 등 일상+드라마.',
    '스릴러': '반전·긴장·추적·심리전 중심.',
    '호러': '공포·미스터리·오컬트 중심.',
    'SF': '미래 기술·우주·AI·디스토피아 중심.',
    '역사': '실제 역사 배경+픽션, 고증 분위기 유지.',
    '게임': '시스템창·레벨업·헌터물·회귀 중심.',
}

def _genre_line(meta):
    genre = meta.get('genre', '선협') or '선협'
    mood = meta.get('mood', '') or ''
    guide = GENRE_GUIDE.get(genre, '')
    extra = f' 장르 특성: {guide}' if guide else ''
    return f'장르:{genre}{extra} 분위기:{mood}'

def idea(meta,previous): return f"한국 장편 웹소설의 새로운 아이디어 시안 1개만 만들어라. {_genre_line(meta)}. 기존 시안과 겹치지 않게. 최근 시안:{previous}. 정확히 3줄, 제목/번호/해설 없이."
def master(seed,meta): return f"""다음 아이디어를 {meta['target_chapters']}화 장편으로 기획하라. 화당 목표:{meta['chapter_chars']}자. {_genre_line(meta)}\n아이디어:{seed}\n[작품 개요][핵심 주제][주인공][세계관 개요][주요 세력][주요 장소][주요 인물][인물 성장][핵심 사건][시간축 방향][주요 복선][전체 이야기 구조][예상 결말]."""
def section(name,master_text,target,existing=''): return f"[{name}]을 장편 작품용 상세 설정으로 작성하라. 목표 {target}화. 마스터:{master_text}\n기존 초안:{existing}\n필수:{SPEC[name]} 기존 설정과 충돌하면 임의로 바꾸지 말고 보완하라."
def contract(master_text,sections,target): return f"{target}화 작품의 장기 불변 기준인 PLAN CONTRACT를 추출하라. 마스터:{master_text}\n세부:{sections}\n[주인공 핵심][세계 핵심 법칙][핵심 비밀][핵심 유물/장치][최종 목표][최종 대립][최종 결말][불변 규칙][절대 변경 금지] 형식."
def master_plot(master_text,contract,target): return f"{target}화 전체 마스터 플롯을 5개 내외의 큰 부로 설계하라. 마스터:{master_text}\nCONTRACT:{contract}\n각 부에 화수 범위, 목표, 성장, 갈등, 핵심 사건, 복선 진행, 반전, 결말, 다음 부 연결. 개별 화 상세는 만들지 않는다."
def section_plan(master_plot_text,contract,start,end,previous): return f"{start}~{end}화 스토리 구간을 하나의 연결된 흐름으로 설계하라. 마스터:{master_plot_text}\nCONTRACT:{contract}\n직전 상태:{previous}\n[구간 목표][구간 시작 상태][핵심 사건 흐름][주요 인물 변화][세계 변화][복선 진행][구간 반전][구간 종료 상태][다음 구간 연결점]."
def chapter_plans(section_text,contract,start,end,state):
    return f"""{start}~{end}화의 개별 플롯을 만들어라.
구간:{section_text}
CONTRACT:{contract}
상태:{state}

출력 규칙(매우 중요):
- 반드시 {start}화부터 {end}화까지 모든 화를 순서대로 정확히 1개씩 작성한다.
- 각 화의 첫 줄은 반드시 `### 제N화` 형식이다. N은 실제 화 번호이다.
- 둘째 줄은 반드시 `제목: 제목내용` 형식이다.
- 화 사이에는 빈 줄을 둔다.
- 설명/서론/마무리/코드블록을 출력하지 않는다.
- 각 화마다 [목표][시작 상황][핵심 사건][갈등][전환점][인물 변화][세계관 정보][복선][복선 회수][엔딩][다음 화 연결]을 빠짐없이 작성한다.

첫 헤더 예시: ### 제{start}화
제목: ..."""
def write(ctx,ch,target,tol): return f"제{ch}화 본문을 작성하라. 목표 {target}자, 허용 {target-tol}~{target+tol}자. 대사는 위아래 한 줄씩 띄운다. 본문만 출력한다.\n{ctx}"
def summary(ch,text): return f"제{ch}화 원고를 다음 화 집필용 기억으로 압축하라. [핵심 사건][인물 상태][경지/능력][위치][시간][소지품][관계][신규 복선][진행/회수 복선][미해결 사건]\n{text}"
def state(ch,text): return f"제{ch}화 원고에서 실제로 변한 상태만 추출하라. 추측 금지. [주인공 상태][인물 상태 변화][경지][위치][시간][소지품][관계][신규 복선][진행 복선][회수 복선][미해결 사건]\n{text}"
def section_memory(start,end,summaries,states):
    return f"""{start}~{end}화 스토리 구간의 장기 기억을 압축하라.
원고 전체를 재작성하지 말고 다음 구간 상태만 남긴다.
[구간 목표][핵심 사건][인물 상태 변화][경지/능력 변화][세력 변화][장소/시간 변화][복선 진행/회수][미해결 문제][다음 구간 연결점]
사실에 없는 내용은 추측하지 않는다.
[화별 요약]
{summaries[:14000]}
[화별 상태]
{states[:14000]}
"""

def arc_memory(start,end,section_memories):
    return f"""{start}~{end}화 아크의 장기 기억을 압축하라. 아래 구간 기억만 근거로 작성한다.
[아크 목표][핵심 전개][주인공/주요 인물 변화][세력/세계 변화][중요 복선][회수된 복선][남은 미해결][아크 결말 상태][다음 아크 연결]
추측 금지. 작품 상태를 대표하는 변경점 중심으로 짧고 정확하게 작성한다.
[구간 기억]
{section_memories[:18000]}
"""
def chat_system(ctx): return f"당신은 작품 전용 AI 비서다. 확정된 작품 데이터와 검색 근거를 우선한다. 자료에 없으면 확인 불가라고 답한다.\n{ctx}"
def entity_extract(ch,text):
    """화별 '상태가 변한' 인물/세력/장소만 원장에 기록하도록 추출을 요청한다."""
    return f"""제{ch}화 원고를 읽고 상태가 실제로 변한 인물/세력/장소만 추출하라.
추측 금지. 변화가 없으면 빈 배열 []만 출력한다.
반드시 JSON 배열만 출력한다. 마크다운, 설명, 코드블록 금지.
형식 예시: [{{"kind":"인물","name":"이름","change":"이번 화에서의 상태 변화 요약"}}]
kind는 인물/세력/장소 중 하나다. name은 작품 설정 DB의 기존 명칭과 일치시킨다.

[제{ch}화 원고]
{text[:12000]}
"""


def continuity(ch,text,ctx): return f"제{ch}화 원고를 아래 확정 설정/기억과 대조하여 연속성 오류만 보고하라. 추측 금지, 근거 없는 지적 금지. [모순/오류][누락 확인 필요][특이사항 없음 여부]\n[참고 자료]\n{ctx}\n\n[검사 대상 원고]\n{text}"
def entity_extra(kind, name, context_text):
    """설정 DB 단일 항목 AI 생성용 프롬프트."""
    guide = {
        '인물': '이름/역할(주인공·서브·조연)/외형/성격/말투/목표/약점/비밀/성장선 순서로 작성.',
        '세력': '목적/지도자/조직/자원/영역/동맹·적대/주요 인물 순서로 작성.',
        '장소': '위치/환경/특징/위험/역사/관련 인물·사건 순서로 작성.',
        '복선': '첫 암시/강화/부분 공개/진실 공개/최종 회수 순서로 작성.',
        '핵심 사건': '배경/전개/결과/여파/연관 인물·복선 순서로 작성.',
        '시간축': '화수/세계관 시점/장소/사건/참여자 순서로 작성.',
    }.get(kind, '핵심 내용을 구조적으로 작성.')
    return (f'다음 설정 항목을 장편 웹소설용으로 구체적으로 작성하라. 종류:{kind} / 이름:{name}. '
            f'{guide}\n[작품 맥락]\n{context_text[:6000]}')


def repair_chapter_plans(raw_text, start, end, missing):
    return f"""아래 AI 응답에서 누락된 화별 플롯만 보완하라.
요청 범위: {start}~{end}화
누락 화: {', '.join(map(str, missing))}화

출력 규칙:
- 누락된 화만 작성한다.
- 각 화 첫 줄은 반드시 `### 제N화`이다.
- 둘째 줄은 반드시 `제목: 제목내용`이다.
- 각 화에는 목표/시작 상황/핵심 사건/갈등/전환점/인물 변화/세계관 정보/복선/복선 회수/엔딩/다음 화 연결을 포함한다.
- 코드블록과 서론/마무리 설명은 금지한다.

기존 응답:
{raw_text}
"""


def entity_catalog_prompt(kind, master_plan, target_chapters=500):
    """마스터 기획을 설정 DB 항목으로 구조화해 반환하도록 요청한다."""
    guide = {
        '인물': {
            'required': '주인공(남주), 여주, 조연(필요하면 1~5명)',
            'schema': '{{"name":"", "role":"남주|여주|조연|기타", "profile":"", "personality":"", "speech_style":"", "goal":"", "secret":"", "arc":""}}'
        },
        '세력': {'required':'작품의 주요 세력 3~10개','schema':'{{"name":"", "category":"세력", "description":"", "rules":""}}'},
        '장소': {'required':'주요 장소 5~15개','schema':'{{"name":"", "category":"장소", "description":"", "rules":""}}'},
        '복선': {'required':'핵심 복선 3~12개','schema':'{{"code":"F001", "title":"", "first_chapter":1, "reveal_chapter":0, "status":"활성", "public_info":"", "author_truth":"", "related_characters":"", "notes":""}}'},
        '핵심 사건': {'required':'중요 사건 5~15개','schema':'{{"title":"", "start_chapter":1, "end_chapter":1, "description":"", "consequence":"", "status":"계획"}}'},
        '시간축': {'required':'작품 이해에 필요한 시간축 사건 5~20개','schema':'{{"chapter_number":1, "story_date":"", "title":"", "description":"", "location":"", "participants":""}}'},
    }[kind]
    return f"""마스터 기획을 읽고 설정 DB의 [{kind}] 항목을 추출·보완하라.
목표: {guide['required']}
반드시 JSON 배열만 출력하라. 마크다운, 설명, 코드블록 금지.
각 원소 형식 예시: {guide['schema']}
없는 정보는 빈 문자열 또는 0/null로 둔다. 마스터 기획에 명시되지 않은 고유명사는 최소한으로만 보완한다.
총 {int(target_chapters)}화 장편 기준이다.

[마스터 기획]
{master_plan[:18000]}
"""
