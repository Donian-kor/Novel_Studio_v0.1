from __future__ import annotations
import re
from novel_studio.ai.prompts import master_plot_prompt, chapter_plan_prompt
class PlotService:
    def __init__(self,db,ai,context): self.db=db; self.ai=ai; self.context=context
    def split_ranges(self,total,chunk=5): return [(s,min(s+chunk-1,total)) for s in range(1,total+1,chunk)]
    def make_story_section(self,master,contract,start,end):
        prompt=master_plot_prompt(master,contract,f'스토리 구간 {start}~{end}화',start,end)
        content=self.ai.generate(prompt,temperature=0.7,max_tokens=7000)
        objective=self._extract(content,'구간 목표') or content[:600]
        self.db.upsert_story_section(start,end,'완료',objective,content,'')
        return content
    def make_chapter_plans(self,start,end,context_text):
        content=self.ai.generate(chapter_plan_prompt(context_text,start,end),temperature=0.65,max_tokens=9000)
        blocks=re.split(r'(?=\[화 번호\])',content)
        saved=0
        for block in blocks:
            m=re.search(r'\[화 번호\]\s*[:：]?\s*(\d+)',block)
            if not m: continue
            n=int(m.group(1)); title=self._extract(block,'제목'); self.db.set_chapter_plan(n,title,block.strip()); saved+=1
        return content,saved
    def _extract(self,text,label):
        m=re.search(rf'\[{re.escape(label)}\]\s*[:：]?\s*(.+?)(?:\n|$)',text); return m.group(1).strip() if m else ''
