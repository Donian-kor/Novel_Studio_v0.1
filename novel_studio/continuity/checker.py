from novel_studio.ai.prompts import continuity
class ContinuityChecker:
    def __init__(self,db,ai,context): self.db,self.ai,self.context=db,ai,context
    def check(self,n,text):
        out=self.ai.generate(continuity(n,text,self.context.build(n)),temperature=.15,max_tokens=6000); self.db.add_continuity(n,'검사','전체',out); return out
