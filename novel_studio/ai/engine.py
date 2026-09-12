from __future__ import annotations
from dataclasses import dataclass
from .lmstudio import LMStudioClient

@dataclass
class AIConfig:
    temperature: float = 0.72
    top_p: float = 0.90
    max_tokens: int = 9000

class AIEngine:
    def __init__(self, client: LMStudioClient, config: AIConfig | None = None):
        self.client = client
        self.config = config or AIConfig()

    def generate(self, prompt: str, system: str = "당신은 한국 장편 웹소설 전문 AI다.", *, temperature: float | None = None, top_p: float | None = None, max_tokens: int | None = None) -> str:
        return self.client.chat([
            {"role":"system","content":system},
            {"role":"user","content":prompt}
        ], temperature=self.config.temperature if temperature is None else temperature,
           top_p=self.config.top_p if top_p is None else top_p,
           max_tokens=self.config.max_tokens if max_tokens is None else max_tokens)
