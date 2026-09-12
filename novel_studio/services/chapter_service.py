from __future__ import annotations
from novel_studio.ai.prompts import write_chapter_prompt
from novel_studio.core.helpers import count_chars
class ChapterService:
    def __init__(self,db,ai,context,pm): self.db=db; self.ai=ai; self.context=context; self.pm=pm
    def write(self,n,target_chars):
        ctx=self.context.build(n)
        prev=self.pm.load_chapter(n-1) if n>1 else ''
        prompt=write_chapter_prompt(ctx,n,target_chars,prev[-2000:])
        return self.ai.generate(prompt,temperature=0.72,max_tokens=max(3000,int(target_chars*1.7)))
    def revise_length(self,text,target_chars,tolerance):
        return text
    def save(self,n,text,title=''):
        self.pm.save_chapter(n,text); self.db.set_chapter_meta(n,title or f'{n}화','집필완료',count_chars(text),self.pm.settings.get('chapter_chars',5000))
