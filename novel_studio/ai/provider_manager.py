try: import keyring
except Exception: keyring=None
from .providers import LMStudioProvider,OpenAICompatibleProvider,AnthropicProvider,GeminiProvider
class ProviderManager:
    IDS={'lmstudio':'LM Studio','openai':'OpenAI','anthropic':'Anthropic','gemini':'Google Gemini','openai_compatible':'OpenAI Compatible'}
    SERVICE='NovelStudio'
    def __init__(self,settings): self.settings=settings
    def key(self,pid):
        if not keyring:return ''
        try:return keyring.get_password(self.SERVICE,pid) or ''
        except Exception:return ''
    def save_key(self,pid,value):
        if not keyring:
            if value: raise RuntimeError('keyring 패키지가 필요합니다.')
            return
        if value:keyring.set_password(self.SERVICE,pid,value)
        else:
            try:keyring.delete_password(self.SERVICE,pid)
            except Exception: pass
    def config(self,pid=None):
        pid=pid or self.settings.data['active_provider']; c=dict(self.settings.data['providers'].get(pid,{})); c['api_key']=self.key(pid); return c
    def _build(self, pid, cfg):
        if pid == 'lmstudio':
            return LMStudioProvider(cfg)
        if pid == 'anthropic':
            return AnthropicProvider(cfg)
        if pid == 'gemini':
            return GeminiProvider(cfg)
        return OpenAICompatibleProvider(cfg)
    def build_unsaved(self, pid, base_url, model, api_key):
        """설정을 저장하지 않고 임시 프로바이더를 생성한다.
        연결 테스트 등에서 실패 시 설정이 남지 않도록 하기 위함."""
        return self._build(pid, {'base_url': base_url, 'model': model, 'api_key': api_key})
    def provider(self, pid=None):
        pid = pid or self.settings.data['active_provider']
        return self._build(pid, self.config(pid))
    def set_active(self,pid): self.settings.data['active_provider']=pid; self.settings.save()
    def save_provider(self,pid,base_url,model,api_key):
        self.settings.data['providers'].setdefault(pid,{})['base_url']=base_url; self.settings.data['providers'][pid]['model']=model; self.settings.save(); self.save_key(pid,api_key)
