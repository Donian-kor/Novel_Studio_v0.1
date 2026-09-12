from __future__ import annotations
from novel_studio.ai.prompts import section_generate, contract_prompt, master_plan_prompt

class SectionService:
    def __init__(self, db, ai, pm): self.db=db; self.ai=ai; self.pm=pm
    def master_plan(self, idea, meta):
        result=self.ai.generate(master_plan_prompt(idea,meta),temperature=0.75,max_tokens=8000)
        self.db.set_meta('master_plan',result); return result
    def generate_section(self, section, context): return self.ai.generate(section_generate(section,context),temperature=0.7,max_tokens=7000)
    def make_contract(self, master, sections, target):
        result=self.ai.generate(contract_prompt(master,sections|{'target':target}),temperature=0.25,max_tokens=4500)
        self.db.save_contract(result,False); return result
