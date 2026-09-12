from __future__ import annotations

def idea_prompt(seed_context='', recent=''):
    return f'''당신은 한국 장편 웹소설 아이디어 기획자다.\n장르/분위기: {seed_context}\n최근에 이미 제시했던 아이디어(겹치지 않게):\n{recent}\n\n새로운 소설 아이디어 시안 1개만 제시하라. 정확히 3줄로 작성하라. 제목이나 해설은 붙이지 말라.''' 

def master_plan_prompt(idea, meta):
    return f'''짧은 아이디어를 장편 웹소설 기획으로 확장하라.\n총 화수: {meta['target_chapters']}\n화당 목표 글자 수: {meta['chapter_chars']}자\n장르: {meta['genre']}\n\n아이디어:\n{idea}\n\n다음 항목을 구조적으로 작성하라.\n[작품 개요]\n[핵심 주제]\n[세계관]\n[수련체계]\n[주요 세력]\n[주요 장소]\n[주요 인물]\n[핵심 사건]\n[시간축]\n[복선]\n[전체 이야기 구조]\n[예상 결말]\n문장보다 정보 구조를 명확하게 하라.'''

def section_generate(section, context):
    specs={
    '세계관':'세계의 구조, 역사, 법칙, 문화, 지역을 구체화하라.',
    '인물':'마스터 기획의 인물을 바탕으로 인물의 상세 프로필, 목표, 성격, 말투, 비밀, 장기 성장과 관계를 구체화하라.',
    '세력':'주요 세력의 목적, 지도자, 성향, 자원, 영역, 관계, 장기 변화를 구체화하라.',
    '장소':'주요 장소의 위치, 특징, 위험, 역사, 관련 인물과 사건을 구체화하라.',
    '수련체계':'경지, 능력, 돌파 조건, 병목, 수명, 전투력 규칙을 체계화하라.',
    '시간축':'500화 전체에서 시간 경과의 큰 흐름과 주요 전환점을 설계하라.',
    '복선':'최초 암시부터 최종 회수까지 연결되는 장기 복선을 설계하라.',
    '핵심 사건':'초반, 중반, 후반, 종막의 대형 사건과 인과관계를 설계하라.'}
    return f'''장편 웹소설 설정 담당 AI다.\n작품 자료:\n{context}\n\n요청 영역: {section}\n{specs.get(section, '해당 영역을 구체화하라.')}\n기존 설정과 충돌하지 않게 작성하고, 바로 저장할 수 있는 구조화된 텍스트로 출력하라.'''

def contract_prompt(master, sections):
    return f'''다음 작품 기획에서 1화부터 {sections.get('target',500)}화까지 절대 잊거나 임의 변경하면 안 되는 핵심만 추출하라.\n\n마스터 기획:\n{master}\n\n보강 설정:\n{sections}\n\n다음 형식으로 작성하라:\n[주인공 핵심]\n[세계 핵심 법칙]\n[핵심 비밀]\n[핵심 유물/장치]\n[최종 목표]\n[최종 적/대립]\n[최종 결말]\n[절대 변경 금지]'''

def master_plot_prompt(master, contract, section_name, start, end):
    return f'''장편 소설의 전체 설계를 바탕으로 {section_name}의 화별 마스터 플롯을 설계하라.\n범위: {start}~{end}화\n\n마스터 기획:\n{master}\n\nPlan Contract:\n{contract}\n\n각 화의 세부 내용보다 먼저 구간 전체의 흐름, 인물 성장, 갈등, 주요 반전, 복선 진행, 구간 종료점을 중심으로 설계하라.'''

def chapter_plan_prompt(context, start, end):
    return f'''다음 스토리 구간을 {start}화부터 {end}화까지 개별 화 플롯으로 세분화하라.\n\n자료:\n{context}\n\n각 화는 반드시 같은 형식으로 작성하라:\n[화 번호]\n[제목]\n[목표]\n[시작 상황]\n[핵심 사건]\n[갈등]\n[전환점]\n[인물 변화]\n[복선]\n[복선 회수]\n[엔딩]\n[다음 화 연결]\n'''

def write_chapter_prompt(context, chapter_no, target_chars, previous_tail=''):
    return f'''한국 장편 웹소설의 본문을 집필하라. 대상 화: {chapter_no}화. 목표 분량: 약 {target_chars}자.\n\n반드시 제공된 플롯과 설정을 우선한다. 대사는 위아래 한 줄씩 띄운다. 설명보다 장면과 행동으로 보여준다. 같은 표현을 반복하지 않는다. 본문 외 설명은 출력하지 않는다.\n\n컨텍스트:\n{context}\n\n직전 화 마지막 부분:\n{previous_tail}\n'''

def chat_system(context):
    return f'''당신은 이 작품 전용 AI 작가다. 사용자의 지시를 수행하되 확정 설정(CANON), Plan Contract, 현재 화 플롯, 현재 상태를 우선한다. 설정을 임의로 변경하지 않는다. 현재 작품 컨텍스트:\n{context}'''
