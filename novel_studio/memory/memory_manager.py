from hashlib import sha256
from novel_studio.ai.prompts import summary, state, section_memory, arc_memory


class MemoryManager:
    """화→구간→아크로 계층화된 장기 기억을 관리한다."""
    def __init__(self, db, ai, ledger=None): self.db, self.ai, self.ledger = db, ai, ledger

    def update(self, n, text, previous=''):
        previous_state = previous or ''
        if not previous_state and n > 1:
            row = self.db.chapter_state(n - 1)
            if row: previous_state = row['state'] or ''

        sm = self.ai.generate(summary(n, text), temperature=.25, max_tokens=4500)
        state_prompt = state(n, text)
        if previous_state:
            state_prompt += '\n\n[직전 확정 상태 - 변경점 파악용]\n' + previous_state[:8000]
        st = self.ai.generate(state_prompt, temperature=.15, max_tokens=5000)
        source_hash = sha256(text.encode('utf-8')).hexdigest()
        self.db.save_summary(n, sm, st)
        self.db.save_chapter_state(n, sm, st, source_hash)
        self.db.save_snapshot(f'chapter:{n}', sm)
        self.db.save_snapshot(f'state:{n}', st)
        if self.ledger: self.ledger.record('chapter', str(n), n, st, text)

        # 구간/아크의 끝 화에서만 상위 기억을 갱신하여 AI 호출을 제한한다.
        sec = self.db.section_for_chapter(n)
        if sec and int(sec['end_chapter']) == int(n):
            self.update_section_memory(sec['start_chapter'], sec['end_chapter'])
            total = self.db.chapter_count() or int(sec['end_chapter'])
            for arc_no, a_start, a_end in self.db.arc_bounds(total, 5):
                if a_end == n:
                    self.update_arc_memory(arc_no, a_start, a_end)
        return sm, st

    def update_section_memory(self, s, e):
        sums = self.db.summaries(start=s, end=e)
        states = self.db.chapter_states(start=s, end=e)
        summaries_text='\n'.join(f"[{r['chapter_number']}화] {r['summary']}" for r in sums)
        states_text='\n'.join(f"[{r['chapter_number']}화] {r['state']}" for r in states)
        out=self.ai.generate(section_memory(s,e,summaries_text,states_text), temperature=.20, max_tokens=5000)
        source=sha256((summaries_text+'\n'+states_text).encode('utf-8')).hexdigest()
        self.db.save_section_memory(s,e,out,source)
        # 기존 스토리 구간의 사람이 보는 snapshot도 동기화한다.
        sec=self.db.section(s,e)
        if sec: self.db.save_section(s,e,sec['status'],sec['content'],out)
        return out

    def update_arc_memory(self, arc_no, s, e):
        secs=self.db.section_memories(s,e)
        text='\n'.join(f"[{r['start_chapter']}~{r['end_chapter']}화] {r['content']}" for r in secs)
        if not text:
            # 구간 기억이 아직 없으면 화별 상태를 최소 근거로 만든다.
            states=self.db.chapter_states(start=s,end=e)
            text='\n'.join(f"[{r['chapter_number']}화] {r['state']}" for r in states)
        out=self.ai.generate(arc_memory(s,e,text), temperature=.18, max_tokens=6000)
        source=sha256(text.encode('utf-8')).hexdigest()
        self.db.save_arc_memory(arc_no,s,e,out,source)
        self.db.save_snapshot(f'arc:{arc_no}',out)
        return out

    def section_snapshot(self, s, e, text):
        return self.ai.generate(
            f'{s}~{e}화 종료 상태를 다음 구조로 추출하라: [사건][인물][경지][위치][시간][소지품][관계][복선][미해결][다음 연결].\n{text}',
            temperature=.2, max_tokens=5000,
        )
