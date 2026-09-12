from __future__ import annotations
from novel_studio.ai.prompts import master_prompt, section_prompt, contract_prompt

SECTIONS=["세계관","수련체계","세력","장소","인물","시간축","복선","핵심 사건"]

class MasterPlanner:
    def __init__(self,db,ai,project): self.db,self.ai,self.project=db,ai,project
    def create_master(self,idea):
        r=self.ai.generate(master_prompt(idea,self.project.settings),temperature=.72,max_tokens=9000)
        self.db.set_meta("idea",idea); self.db.set_meta("master_plan",r); return r
    def generate_section(self,section,master,related=""):
        r=self.ai.generate(section_prompt(section,master,related,self.project.settings.get("target_chapters","500")),temperature=.68,max_tokens=8000)
        self.db.set_meta("section_"+section,r); return r
    def extract_contract(self,master,sections):
        r=self.ai.generate(contract_prompt(master,sections,int(self.project.settings.get("target_chapters","500"))),temperature=.22,max_tokens=5000)
        self.db.save_contract(r,False); return r
