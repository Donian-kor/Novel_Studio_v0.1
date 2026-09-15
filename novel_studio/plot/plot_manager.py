from novel_studio.ai.prompts import master_plot, section_plan, chapter_stories
from novel_studio.utils.cancellation import JobCancelled


class PlotManager:
    def __init__(self, db, ai, project):
        self.db, self.ai, self.project = db, ai, project

    def generate_master(self):
        c = self.db.get_contract()
        out = self.ai.generate(
            master_plot(self.db.get_plan(), c['content'] if c else '', self.project.settings['target_chapters']),
            temperature=.62, max_tokens=12000
        )
        self.db.set_meta('master_plot', out)
        return out

    def ranges(self):
        size = int(self.project.settings.get('section_size', 10))
        total = int(self.project.settings['target_chapters'])
        return [(s, min(s + size - 1, total)) for s in range(1, total + 1, size)]

    def long_ranges(self):
        size = max(1, int(self.project.settings.get('long_story_size', 50)))
        total = int(self.project.settings['target_chapters'])
        return [(s, min(s + size - 1, total)) for s in range(1, total + 1, size)]

    def sub_ranges(self, start, end):
        size = max(1, int(self.project.settings.get('sub_story_size', 10)))
        return [(s, min(s + size - 1, end)) for s in range(int(start), int(end) + 1, size)]

    def generate_story_section(self, s, e, previous=''):
        c = self.db.get_contract()
        return self.ai.generate(
            section_plan(self.db.get_meta('master_plot', ''), c['content'] if c else '', s, e, previous),
            temperature=.60, max_tokens=12000
        )

    def generate_substory_section(self, s, e, parent_content='', previous=''):
        c = self.db.get_contract()
        context = (parent_content or '')[:12000]
        if previous:
            context += '\n\n[직전 세부 구간]\n' + previous[:6000]
        return self.ai.generate(
            section_plan(self.db.get_meta('master_plot', ''), c['content'] if c else '', s, e, context),
            temperature=.55, max_tokens=8000
        )


    def generate_chapter_stories(self, start, end, sub_content="", previous=""):
        contract = self.db.get_contract()
        raw = self.ai.generate(chapter_stories(sub_content, contract['content'] if contract else '', int(start), int(end), previous), temperature=.58, max_tokens=12000)
        return raw
    def ranges_by_size(self, size=25):
        total = int(self.project.settings['target_chapters']); size = max(1, int(size))
        return [(s, min(s + size - 1, total)) for s in range(1, total + 1, size)]

    def audit_long_form(self, size=50, progress=None, cancelled_check=None):
        findings = []
        ranges = self.ranges_by_size(size)
        total = len(ranges)
        for idx, (s0, e0) in enumerate(ranges):
            if cancelled_check and cancelled_check():
                raise JobCancelled()
            if progress:
                progress(idx + 1, total, f'{s0}~{e0}화', '')
            source_parts = []
            for row in self.db.sections_overlapping(s0, e0):
                source_parts.append(f"[스토리 {row['start_chapter']}~{row['end_chapter']}화]\n{row['content']}")
            for row in self.db.chapter_states(start=s0, end=e0):
                source_parts.append(f"[종료 상태 {row['chapter_number']}화]\n{row['state']}")
            for chapter in range(s0, e0 + 1):
                text = self.project.load_chapter(chapter)
                if text:
                    source_parts.append(f"[본문 {chapter}화]\n{text}")
            source = '\n\n'.join(source_parts)[:32000]
            out = self.ai.generate(
                f'{s0}~{e0}화 설정/복선/시간축 연속성 문제만 검사하라. 추측 금지.\n{source}',
                temperature=.1, max_tokens=5000
            )
            self.db.add_continuity(e0, '정밀', '구간', out)
            findings.append(f'[{s0}~{e0}]\n{out}')
            if progress:
                progress(idx + 1, total, f'{s0}~{e0}화', out)
        return '\n\n'.join(findings)
