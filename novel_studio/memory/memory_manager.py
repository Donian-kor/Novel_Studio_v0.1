from __future__ import annotations
from novel_studio.ai.prompts import summary_prompt, state_extract_prompt

class MemoryManager:
    def __init__(self,db,ai,context=None): self.db,self.ai,self.context=db,ai,context
    def summarize(self,chapter,text):
        r=self.ai.generate(summary_prompt(chapter,text),temperature=.25,max_tokens=4500); self.db.save_summary(chapter,r,r); self.db.save_snapshot(f"chapter:{chapter}",r); return r
    def extract_state(self,chapter,text,current=""):
        r=self.ai.generate(state_extract_prompt(chapter,text,current),temperature=.20,max_tokens=5000); self.db.save_snapshot(f"state:{chapter}",r); return r
    def section_snapshot(self,start,end,text):
        prompt=f"{start}~{end}화의 다음 구간 전달용 상태를 구조화하라. [주인공 상태][주요 인물 변화][경지][위치][시간][소지품][관계][신규 복선][진행 복선][회수 복선][미해결 사건][다음 구간 필수 연결]\n{text}"
        r=self.ai.generate(prompt,temperature=.20,max_tokens=5000); self.db.save_snapshot(f"section:{start}-{end}",r); return r
