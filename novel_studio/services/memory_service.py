from __future__ import annotations
from novel_studio.core.helpers import count_chars
class MemoryService:
    def __init__(self,db,ai,context): self.db=db; self.ai=ai; self.context=context
    def make_summary(self,n,text):
        prompt=f'''다음은 {n}화 원고다. 다음 화를 위해 핵심 사건, 인물 상태 변화, 시간/장소, 경지, 소지품, 복선, 미해결 사건을 구조적으로 요약하라.\n{text}'''
        out=self.ai.generate(prompt,temperature=0.25,max_tokens=3500)
        self.db.save_summary(n,out,out)
        self.db.set_snapshot(f'chapter:{n}',out)
        return out
