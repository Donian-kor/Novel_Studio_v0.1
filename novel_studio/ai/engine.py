from __future__ import annotations
from novel_studio.ai.lmstudio import LMStudioClient
class AIEngine:
    def __init__(self, client: LMStudioClient): self.client=client
    def generate(self, prompt, system='당신은 장편 웹소설 전문 AI다.', temperature=0.7, max_tokens=6000):
        return self.client.chat([{'role':'system','content':system},{'role':'user','content':prompt}],temperature,max_tokens)
