from __future__ import annotations
from novel_studio.core.helpers import count_chars

class ContextManager:
    def __init__(self, db, pm): self.db=db; self.pm=pm
    def build(self, chapter=None, include_previous=True, include_recent=4):
        parts=[]
        contract=self.db.contract()
        if contract and contract['content']: parts.append('[PLAN CONTRACT]\n'+contract['content'])
        master=self.db.get_meta('master_plan','')
        if master: parts.append('[MASTER PLAN]\n'+master[:12000])
        if chapter:
            plan=self.db.chapter_plan(chapter)
            if plan: parts.append(f'[CHAPTER {chapter} PLAN]\n'+plan['content'])
            state=self.db.snapshot(f'chapter:{max(chapter-1,0)}')
            if state: parts.append('[RECENT STATE]\n'+state['content'][:8000])
            for n in range(max(1,chapter-include_recent),chapter):
                s=self.db.summary(n)
                if s: parts.append(f'[SUMMARY {n}]\n'+s['summary'][:2500])
            if include_previous and chapter>1:
                txt=self.pm.load_chapter(chapter-1)
                if txt: parts.append('[PREVIOUS CHAPTER TAIL]\n'+txt[-2500:])
        return '\n\n'.join(parts)
    def count(self,text): return count_chars(text)
