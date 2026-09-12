from __future__ import annotations
from novel_studio.ai.prompts import continuity_prompt
class ContinuityChecker:
    def __init__(self,db,ai,context):self.db,self.ai,self.context=db,ai,context
    def check(self,chapter,text):
        r=self.ai.generate(continuity_prompt(self.context.build(chapter),chapter,text),temperature=.15,max_tokens=5500); self.db.set_meta(f"continuity_{chapter}",r); return r
