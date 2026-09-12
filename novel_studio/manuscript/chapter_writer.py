from novel_studio.ai.prompts import write
class ChapterWriter:
    def __init__(self,db,ai,project,context): self.db,self.ai,self.project,self.context=db,ai,project,context
    def write(self,n,extra=''):
        target=int(self.project.settings['chapter_chars']); tol=int(self.project.settings['tolerance']); return self.ai.generate(write(self.context.build(n,extra),n,target,tol),temperature=.72,max_tokens=max(9000,target*2))
    def adjust(self,text,target,tol): return self.ai.generate(f'이 원고의 사건과 문체를 유지하며 {target-tol}~{target+tol}자로 자연스럽게 조정하라. 본문만 출력.\n{text}',temperature=.35,max_tokens=max(9000,target*2))
