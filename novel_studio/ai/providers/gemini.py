import json
import urllib.request
import urllib.error
from .base import AIProvider, ProviderError
from novel_studio.utils.cancellation import JobCancelled

TEST_TIMEOUT = 15
CHAT_TIMEOUT = 1800


class GeminiProvider(AIProvider):
    def __init__(self, config, cancel_check=None, abort_handler=None):
        super().__init__(config, cancel_check=cancel_check, abort_handler=abort_handler)

    def _chat_impl(self, messages, *, temperature, top_p, max_tokens, timeout=None):
        key = self.config.get('api_key', '')
        model = self.config.get('model', '')
        if not key or not model:
            raise ProviderError('Gemini API Key와 모델을 설정하세요.')
        
        system = '\n\n'.join(m['content'] for m in messages if m.get('role') == 'system')
        contents = []
        for m in messages:
            if m.get('role') == 'system':
                continue
            role = 'model' if m.get('role') == 'assistant' else 'user'
            contents.append({'role': role, 'parts': [{'text': m.get('content', '')}]})
        
        body = {
            'contents': contents,
            'generationConfig': {
                'temperature': temperature,
                'topP': top_p,
                'maxOutputTokens': max_tokens
            }
        }
        if system:
            body['systemInstruction'] = {'parts': [{'text': system}]}
        
        url = self.config.get('base_url', 'https://generativelanguage.googleapis.com/v1beta').rstrip('/') + f'/models/{model}:generateContent?key={key}'
        req = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode(), headers={'Content-Type': 'application/json'}, method='POST')
        
        with self._open_response(self._check_urlopen(req, timeout)) as r:
            d = json.loads(self._read_json(r).decode())

        return ''.join(p.get('text', '') for c in d.get('candidates', []) for p in c.get('content', {}).get('parts', []) if p.get('text'))
    
    def _chat_stream_impl(self, messages, *, temperature, top_p, max_tokens, timeout=None):
        """Gemini 스트리밍 미구현. 전체를 한 번에 반환하는 폴백이다.

        실제 SSE 스트리밍이 필요하면 이 메서드를 재구현하거나,
        별도의 스트리밍 경로를 구현 후 super().chat_stream()을 호출하라.
        """
        text = self._chat_impl(messages, temperature=temperature, top_p=top_p, max_tokens=max_tokens, timeout=timeout)
        yield text

    def chat(self, messages, *, temperature, top_p, max_tokens, timeout=None):
        return super().chat(messages, temperature=temperature, top_p=top_p, max_tokens=max_tokens, timeout=timeout)

    def chat_stream(self, messages, *, temperature, top_p, max_tokens, timeout=None):
        return super().chat_stream(messages, temperature=temperature, top_p=top_p, max_tokens=max_tokens, timeout=timeout)

    def quick_test(self):
        """짧은 타임아웃으로 연결 테스트를 수행한다."""
        return self.chat(
            [{'role': 'user', 'content': 'Reply with exactly: 연결 테스트 성공'}],
            temperature=.1, top_p=.9, max_tokens=32, timeout=15
        )