from abc import ABC, abstractmethod
class ProviderError(RuntimeError): pass
class AIProvider(ABC):
    def __init__(self, config): self.config=config
    @abstractmethod
    def chat(self, messages, *, temperature, top_p, max_tokens, timeout=None): ...
    def list_models(self): return []
    def quick_test(self):
        """짧은 타임아웃 연결 테스트 (기본 구현)."""
        return self.chat([{"role":"user","content":"Reply with exactly: 연결 테스트 성공"}],temperature=.1,top_p=.9,max_tokens=32,timeout=15)
    def test(self): return self.quick_test()
