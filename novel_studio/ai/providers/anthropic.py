import json,urllib.request,urllib.error
from .base import AIProvider,ProviderError

TEST_TIMEOUT = 15
CHAT_TIMEOUT = 1800


class AnthropicProvider(AIProvider):
    def chat(self, messages, *, temperature, top_p, max_tokens, timeout=CHAT_TIMEOUT):
        key=self.config.get('api_key',''); model=self.config.get('model','')
        if not key or not model: raise ProviderError('Anthropic API Key와 모델을 설정하세요.')
        system='\n\n'.join(m['content'] for m in messages if m.get('role')=='system')
        msgs=[m for m in messages if m.get('role')!='system']
        body={'model':model,'max_tokens':max_tokens,'messages':msgs}
        if system: body['system']=system
        req=urllib.request.Request(self.config.get('base_url','https://api.anthropic.com').rstrip('/')+'/v1/messages',data=json.dumps(body,ensure_ascii=False).encode(),headers={'content-type':'application/json','x-api-key':key,'anthropic-version':'2023-06-01'},method='POST')
        try:
            with urllib.request.urlopen(req,timeout=timeout) as r:d=json.loads(r.read().decode())
            return ''.join(x.get('text','') for x in d.get('content',[]) if x.get('type')=='text')
        except urllib.error.HTTPError as e: raise ProviderError(f'Anthropic HTTP {e.code}: {e.read().decode(errors="ignore")}')
        except Exception as e: raise ProviderError(f'Anthropic 요청 실패: {e}')

    def quick_test(self):
        """짧은 타임아웃으로 연결 테스트를 수행한다."""
        return self.chat([{'role': 'user', 'content': 'Reply with exactly: 연결 테스트 성공'}],
                         temperature=.1, top_p=.9, max_tokens=32, timeout=TEST_TIMEOUT)
