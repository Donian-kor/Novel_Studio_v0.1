from __future__ import annotations
from novel_studio.ai.prompts import master_plot_prompt, story_section_prompt, chapter_plans_prompt
from novel_studio.ai.parsers import extract_section, parse_chapter_plans

class PlotManager:
    def __init__(self,db,ai): self.db,self.ai=db,ai
    @staticmethod
    def ranges(total,size): return [(s,min(s+size-1,total)) for s in range(1,total+1,size)]
    def generate_master_plot(self,master,contract,target):
        r=self.ai.generate(master_plot_prompt(master,contract,target),temperature=.62,max_tokens=10000); self.db.set_meta("master_plot",r); return r
    def generate_story_section(self,master_plot,contract,start,end,previous):
        r=self.ai.generate(story_section_prompt(master_plot,contract,start,end,previous),temperature=.62,max_tokens=8000)
        obj=extract_section(r,"구간 목표") or r[:600]; self.db.upsert_section(start,end,"생성완료",obj,r,""); return r
    def generate_chapter_plans(self,section_text,contract,context,start,end):
        r=self.ai.generate(chapter_plans_prompt(section_text,contract,context,start,end),temperature=.58,max_tokens=12000)
        plans=parse_chapter_plans(r)
        for n,t,b in plans:self.db.set_chapter_plan(n,t,b,"확정" if n<start else "초안")
        return r,len(plans)
