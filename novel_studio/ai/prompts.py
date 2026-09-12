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
def chapter_plans(section_text,contract,start,end,state): return f"{start}~{end}화의 개별 플롯을 만들어라. 구간:{section_text}\nCONTRACT:{contract}\n상태:{state}\n각 화마다 [화 번호][제목][목표][시작 상황][핵심 사건][갈등][전환점][인물 변화][세계관 정보][복선][복선 회수][엔딩][다음 화 연결]을 빠짐없이 작성하라."
def write(ctx,ch,target,tol): return f"제{ch}화 본문을 작성하라. 목표 {target}자, 허용 {target-tol}~{target+tol}자. 대사는 위아래 한 줄씩 띄운다. 본문만 출력한다.\n{ctx}"
def summary(ch,text): return f"제{ch}화 원고를 다음 화 집필용 기억으로 압축하라. [핵심 사건][인물 상태][경지/능력][위치][시간][소지품][관계][신규 복선][진행/회수 복선][미해결 사건]\n{text}"
def state(ch,text): return f"제{ch}화 원고에서 실제로 변한 상태만 추출하라. 추측 금지. [주인공 상태][인물 상태 변화][경지][위치][시간][소지품][관계][신규 복선][진행 복선][회수 복선][미해결 사건]\n{text}"
def chat_system(ctx): return f"당신은 작품 전용 AI 비서다. 확정된 작품 데이터와 검색 근거를 우선한다. 자료에 없으면 확인 불가라고 답한다.\n{ctx}"
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
