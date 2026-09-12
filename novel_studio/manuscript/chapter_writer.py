from __future__ import annotations
from novel_studio.ai.prompts import chapter_write_prompt
from novel_studio.core.helpers import count_chars

class ChapterWriter:
    def __init__(self,db,ai,context,project): self.db,self.ai,self.context,self.project=db,ai,context,project
    def write(self,chapter):
        target=int(self.project.settings.get("chapter_chars","5000")); tol=int(self.project.settings.get("tolerance","300"));
        return self.ai.generate(chapter_write_prompt(self.context.build(chapter),chapter,target,tol),temperature=.72,max_tokens=max(5000,int(target*2)))
    def adjust_length(self,text,target,tol):
        n=count_chars(text); low,high=target-tol,target+tol
        if low<=n<=high:return text
        action="확장" if n<low else "축약"
        p=f"다음 소설 원고를 사건과 문체를 유지하며 자연스럽게 {action}하라. 현재 {n}자, 목표 {target}자, 허용 {low}~{high}자. 본문만 출력하라.\n\n{text}"
        return self.ai.generate(p,temperature=.35,max_tokens=max(5000,int(target*1.9)))
