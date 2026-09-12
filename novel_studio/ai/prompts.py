def idea_prompt(genre: str, mood: str, previous: str = "") -> str:
    return f"""한국 장편 웹소설을 위한 새로운 아이디어 시안 1개만 만들어라.\n장르: {genre}\n분위기: {mood}\n기존 아이디어와 발상이 겹치지 않게 하라.\n최근 시안:\n{previous}\n정확히 3줄. 제목, 번호, 해설 없이 출력하라."""


def master_prompt(idea: str, meta: dict) -> str:
    return f"""다음 아이디어를 {meta['target_chapters']}화 장편 웹소설의 마스터 기획으로 설계하라.\n목표 분량: 화당 {meta['chapter_chars']}자\n장르: {meta['genre']}\n분위기: {meta.get('mood','')}\n아이디어:\n{idea}\n\n다음 항목을 모두 포함하라.\n[작품 개요]\n[핵심 주제]\n[세계관]\n[수련체계]\n[주요 세력]\n[주요 장소]\n[주요 인물]\n[核心 사건]\n[시간축 방향]\n[주요 복선]\n[전체 이야기 구조]\n[예상 결말]\n\n500화까지 확장 가능한 장기 구조를 우선하고, 설정 간 인과관계를 맞춰라."""

SECTION_SPECS={
"세계관":"세계의 층위, 역사, 법칙, 문화, 종족, 공간, 시간, 인과, 천도/윤회 등을 구체화하라.",
"인물":"마스터 기획의 인물을 상세 프로필로 확장하라. 외형, 성격, 말투, 목표, 욕망, 약점, 비밀, 능력, 성장선, 최종 상태를 포함하라.",
"세력":"세력의 목적, 지도자, 조직, 자원, 영역, 적대/동맹, 주요 인물, 장기 변화와 주인공과의 관계를 설계하라.",
"장소":"주요 장소의 위치, 환경, 특징, 위험, 역사, 관련 세력·인물·사건을 설계하라.",
"수련체계":"경지, 능력, 수명, 돌파 조건, 병목, 전투력, 법칙과 기술의 일관된 체계를 설계하라.",
"시간축":"목표 화수까지 화수와 세계관 시간을 연결하고 시간 도약과 대형 사건의 시점을 설계하라.",
"복선":"장기 복선을 설계하고 첫 암시, 강화, 부분 공개, 진실 공개, 최종 회수를 연결하라.",
"핵심 사건":"초반·중반·후반의 대형 사건과 인과관계, 전환점, 최종 사건을 설계하라.",
}

def section_prompt(section, master, related, target):
    return f"""장편 웹소설 기획자다. [{section}] 영역을 작성하라.\n목표 화수: {target}\n마스터 기획:\n{master}\n관련 설정:\n{related}\n요청:\n{SECTION_SPECS.get(section,'해당 영역을 구체화하라.')}\n기존 확정 설정을 바꾸지 말고 부족한 부분만 확장하라."""


def contract_prompt(master, sections, target):
    return f"""다음 {target}화 작품 기획에서 장편 전체에서 절대 흔들리면 안 되는 핵심을 PLAN CONTRACT로 추출하라.\n\n[마스터]\n{master}\n\n[세부 설정]\n{sections}\n\n형식:\n[주인공 핵심]\n[세계 핵심 법칙]\n[핵심 비밀]\n[핵심 유물/장치]\n[최종 목표]\n[최종 적/대립]\n[최종 결말]\n[불변 규칙]\n[절대 변경 금지]\n짧고 검증 가능한 문장으로 작성하라."""


def master_plot_prompt(master, contract, target):
    return f"""{target}화 장편의 전체 마스터 플롯을 설계하라.\n\n[마스터]\n{master}\n[PLAN CONTRACT]\n{contract}\n\n5개 내외의 큰 부로 나누고 각 부에 기간/화수, 목표, 주인공 성장, 핵심 갈등, 주요 사건, 복선 진행, 중간 반전, 부 결말, 다음 부 연결을 작성하라. 개별 화 세부보다 전체 인과와 장기 흐름을 우선하라."""


def story_section_prompt(master_plot, contract, start, end, previous):
    return f"""{start}화~{end}화의 '스토리 구간'을 설계하라.\n[마스터 플롯]\n{master_plot}\n[PLAN CONTRACT]\n{contract}\n[직전 구간 상태]\n{previous}\n\n[구간 목표]\n[구간 시작 상태]\n[핵심 사건 흐름]\n[주요 인물 변화]\n[세계 변화]\n[복선 진행]\n[구간 반전]\n[구간 종료 상태]\n[다음 구간 연결점]\n단편 모음이 아니라 하나의 연결된 흐름으로 설계하라."""


def chapter_plans_prompt(section_text, contract, context, start, end):
    return f"""스토리 구간 {start}~{end}화의 개별 화 플롯을 작성하라.\n[구간]\n{section_text}\n[PLAN CONTRACT]\n{contract}\n[현재 기억]\n{context}\n\n각 화마다 반드시:\n[화 번호] 숫자\n[제목]\n[목표]\n[시작 상황]\n[핵심 사건]\n[갈등]\n[전환점]\n[인물 변화]\n[세계관 정보]\n[복선]\n[복선 회수]\n[엔딩]\n[다음 화 연결]\n을 포함하라. 해당 범위의 모든 화를 빠짐없이 작성하라."""


def chapter_write_prompt(context, chapter, target, tolerance):
    low, high = target-tolerance, target+tolerance
    return f"""현재 소설의 {chapter}화를 집필하라. 아래 컨텍스트와 화별 플롯을 엄격히 따른다.\n목표 분량: {target}자, 허용 범위: {low}~{high}자.\n대사는 위아래 한 줄씩 띄우고 소설 본문만 출력하라. 설명문/메타 발언/마크다운 제목은 출력하지 마라.\n\n{context}"""


def summary_prompt(chapter, text):
    return f"""제{chapter}화 원고를 다음 화 집필에 사용할 수 있도록 압축하라. 문학적 줄거리와 함께 상태 변화를 구조적으로 포함하라.\n[핵심 사건]\n[인물 상태 변화]\n[경지/능력 변화]\n[위치 변화]\n[시간 경과]\n[소지품 변화]\n[관계 변화]\n[신규 복선]\n[진행/회수 복선]\n[미해결 사건]\n\n원고:\n{text}"""


def state_extract_prompt(chapter, text, current):
    return f"""제{chapter}화 원고에서 작품 상태에 실제로 영향을 준 변경만 추출하라. 추측하지 말고 원고에 근거가 있는 정보만 작성하라.\n현재 상태:\n{current}\n원고:\n{text}\n\n[주인공 상태]\n[인물 상태 변화]\n[경지]\n[위치]\n[시간]\n[소지품]\n[관계]\n[신규 복선]\n[진행 복선]\n[회수 복선]\n[미해결 사건]"""


def continuity_prompt(context, chapter, text):
    return f"""제{chapter}화가 기존 설정과 연속성을 위반하는지 검사하라. 반드시 근거를 제시하라.\n[기존 컨텍스트]\n{context}\n[검사할 원고]\n{text}\n\n[시간]\n[장소]\n[경지]\n[인물]\n[부상]\n[소지품]\n[인물 지식]\n[세계관]\n[사건 순서]\n[복선]\n각 항목을 정상/주의/오류로 판단하라."""


def chat_system(context):
    return f"""당신은 이 작품의 전속 한국 웹소설 작가다. 작품의 확정 설정을 지키고 사용자의 요청에 자연스럽게 대응하라. 현재 작품 컨텍스트:\n{context}\n원고 밖의 메타 설명은 최소화하라."""
