from __future__ import annotations
from novel_studio.core.helpers import count_chars
class ContinuityService:
    def __init__(self,db,ai,context,pm): self.db=db; self.ai=ai; self.context=context; self.pm=pm
    def check(self,n,text):
        prompt=f'''다음 {n}화가 기존 컨텍스트와 충돌하는지 검사하라.\n컨텍스트:\n{self.context.build(n)}\n\n원고:\n{text}\n\n결과 형식:\n[문제 있음/없음]\n[시간]\n[장소]\n[인물]\n[경지]\n[소지품]\n[복선]\n[설정]\n[설명]'''
        return self.ai.generate(prompt,temperature=0.15,max_tokens=4500)
