import json,urllib.request,urllib.error
from .base import AIProvider,ProviderError

TEST_TIMEOUT = 15
CHAT_TIMEOUT = 1800


class GeminiProvider(AIProvider):
    def chat(self, messages, *, temperature, top_p, max_tokens, timeout=CHAT_TIMEOUT):
        key=self.config.get('api_key',''); model=self.config.get('model','')
        if not key or not model: raise ProviderError('Gemini API Key와 모델을 설정하세요.')
        system='\n\n'.join(m['content'] for m in messages if m.get('role')=='system')
        contents=[]
        for m in messages:
            if m.get('role')=='system': continue
            role='model' if m.get('role')=='assistant' else 'user'; contents.append({'role':role,'parts':[{'text':m.get('content','')}]})
        body={'contents':contents,'generationConfig':{'temperature':temperature,'topP':top_p,'maxOutputTokens':max_tokens}}
        if system: body['systemInstruction']={'parts':[{'text':system}]}
        url=self.config.get('base_url','https://generativelanguage.googleapis.com/v1beta').rstrip('/')+f'/models/{model}:generateContent?key={key}'
        req=urllib.request.Request(url,data=json.dumps(body,ensure_ascii=False).encode(),headers={'Content-Type':'application/json'},method='POST')
        try:
            with urllib.request.urlopen(req,timeout=timeout) as r:d=json.loads(r.read().decode())
            return ''.join(p.get('text','') for c in d.get('candidates',[]) for p in c.get('content',{}).get('parts',[]) if p.get('text'))
        except urllib.error.HTTPError as e: raise ProviderError(f'Gemini HTTP {e.code}: {e.read().decode(errors="ignore")}')
        except Exception as e: raise ProviderError(f'Gemini 요청 실패: {e}')

    def quick_test(self):
        """짧은 타임아웃으로 연결 테스트를 수행한다."""
        return self.chat([{'role': 'user', 'content': 'Reply with exactly: 연결 테스트 성공'}],
                         temperature=.1, top_p=.9, max_tokens=32, timeout=TEST_TIMEOUT)
