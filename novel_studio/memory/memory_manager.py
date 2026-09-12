from novel_studio.ai.prompts import summary,state
class MemoryManager:
    def __init__(self,db,ai): self.db,self.ai=db,ai
    def update(self,n,text,previous=''):
        sm=self.ai.generate(summary(n,text),temperature=.25,max_tokens=4500); st=self.ai.generate(state(n,text),temperature=.15,max_tokens=5000); self.db.save_summary(n,sm,st); self.db.save_snapshot(f'chapter:{n}',sm); self.db.save_snapshot(f'state:{n}',st); return sm,st
    def section_snapshot(self,s,e,text): return self.ai.generate(f'{s}~{e}화 종료 상태를 다음 구조로 추출하라: [사건][인물][경지][위치][시간][소지품][관계][복선][미해결][다음 연결].\n{text}',temperature=.2,max_tokens=5000)
