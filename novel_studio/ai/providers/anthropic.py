import json
import urllib.request
import urllib.error
from .base import AIProvider, ProviderError

TEST_TIMEOUT = 15
CHAT_TIMEOUT = 1800


class AnthropicProvider(AIProvider):
    def _chat_impl(self, messages, *, temperature, top_p, max_tokens, timeout=None):
        key = self.config.get('api_key', '')
        model = self.config.get('model', '')
        if not key or not model:
            raise ProviderError('Anthropic API Key와 모델을 설정하세요.')
        
        system = '\n\n'.join(m['content'] for m in messages if m.get('role') == 'system')
        msgs = [m for m in messages if m.get('role') != 'system']
        
        body = {
            'model': model,
            'max_tokens': max_tokens,
            'messages': msgs,
            'temperature': temperature,
            'top_p': top_p
        }
        if system:
            body['system'] = system
        
        req = urllib.request.Request(
            self.config.get('base_url', 'https://api.anthropic.com').rstrip('/') + '/v1/messages',
            data=json.dumps(body, ensure_ascii=False).encode(),
            headers={
                'content-type': 'application/json',
                'x-api-key': key,
                'anthropic-version': '2023-06-01'
            },
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode())
        
        return ''.join(x.get('text', '') for x in d.get('content', []) if x.get('type') == 'text')
    
    def _chat_stream_impl(self, messages, *, temperature, top_p, max_tokens, timeout=None):
        key = self.config.get('api_key', '')
        model = self.config.get('model', '')
        if not key or not model:
            raise ProviderError('Anthropic API Key와 모델을 설정하세요.')
        
        system = '\n\n'.join(m['content'] for m in messages if m.get('role') == 'system')
        msgs = [m for m in messages if m.get('role') != 'system']
        
        body = {
            'model': model,
            'max_tokens': max_tokens,
            'messages': msgs,
            'temperature': temperature,
            'stream': True
        }
        if system:
            body['system'] = system
        
        req = urllib.request.Request(
            self.config.get('base_url', 'https://api.anthropic.com').rstrip('/') + '/v1/messages',
            data=json.dumps(body, ensure_ascii=False).encode(),
            headers={
                'content-type': 'application/json',
                'accept': 'text/event-stream',
                'x-api-key': key,
                'anthropic-version': '2023-06-01'
            },
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=timeout) as r:
            for raw in r:
                line = raw.decode('utf-8', errors='ignore').strip()
                if not line.startswith('data:'):
                    continue
                try:
                    data = json.loads(line[5:].strip())
                except Exception:
                    continue
                delta = data.get('delta', {})
                text = delta.get('text')
                if text:
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