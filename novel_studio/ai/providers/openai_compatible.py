import json
import urllib.request
import urllib.error
from .base import AIProvider, ProviderError
from novel_studio.jobs.worker import JobCancelled

TEST_TIMEOUT = 15
CHAT_TIMEOUT = 1800


class OpenAICompatibleProvider(AIProvider):
    def __init__(self, config, cancel_check=None, abort_handler=None):
        super().__init__(config, cancel_check=cancel_check, abort_handler=abort_handler)

    def _base(self): 
        return str(self.config.get('base_url', '')).rstrip('/')
    
    def _headers(self):
        h = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        k = self.config.get('api_key', '')
        if k:
            h['Authorization'] = 'Bearer ' + k
        return h
    
    def list_models(self):
        try:
            req = urllib.request.Request(self._base() + '/models', headers=self._headers())
            with urllib.request.urlopen(req, timeout=20) as r:
                d = json.loads(r.read().decode())
            return [str(x.get('id')) for x in d.get('data', []) if x.get('id')]
        except Exception as e:
            raise ProviderError(f'모델 목록 조회 실패: {e}')
    
    def _chat_impl(self, messages, *, temperature, top_p, max_tokens, timeout=None):
        """실제 채팅 구현 (재시도 로직은 베이스 클래스에서 처리)"""
        model = self.config.get('model', '')
        if not model:
            models = self.list_models()
            model = models[0] if models else ''
        if not model:
            raise ProviderError('사용할 모델을 설정하세요.')
        
        body = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
            'top_p': top_p,
            'max_tokens': max_tokens,
            'stream': False
        }
        
        req = urllib.request.Request(
            self._base() + '/chat/completions',
            data=json.dumps(body, ensure_ascii=False).encode(),
            headers=self._headers(),
            method='POST'
        )
        
        with self._open_response(urllib.request.urlopen(req, timeout=timeout)) as r:
            d = json.loads(self._read_json(r).decode())

        return d['choices'][0]['message']['content']
    
    def _chat_stream_impl(self, messages, *, temperature, top_p, max_tokens, timeout=None):
        """실제 스트리밍 구현 (재시도는 베이스 클래스에서 처리)"""
        model = self.config.get('model', '')
        if not model:
            models = self.list_models()
            model = models[0] if models else ''
        if not model:
            raise ProviderError('사용할 모델을 설정하세요.')
        
        body = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
            'top_p': top_p,
            'max_tokens': max_tokens,
            'stream': True
        }
        
        req = urllib.request.Request(
            self._base() + '/chat/completions',
            data=json.dumps(body, ensure_ascii=False).encode(),
            headers=self._headers(),
            method='POST'
        )
        
        with self._open_response(urllib.request.urlopen(req, timeout=timeout)) as r:
            while True:
                try:
                    line = self._readline_cancelable(r).decode('utf-8', errors='ignore')
                except JobCancelled:
                    raise
                except Exception as e:
                    if self._interrupted():
                        raise JobCancelled() from e
                    raise
                if not line:
                    break
                line = line.strip()
                if not line.startswith('data:'):
                    continue
                data = line[5:].strip()
                if data == '[DONE]':
                    break
                try:
                    d = json.loads(data)
                    delta = d['choices'][0].get('delta', {}).get('content')
                    if delta:
                        yield delta
                except Exception:
                    continue

    def chat(self, messages, *, temperature, top_p, max_tokens, timeout=None):
        # 재시도 로직은 베이스 클래스의 _retry_decorator가 처리
        return super().chat(messages, temperature=temperature, top_p=top_p, max_tokens=max_tokens, timeout=timeout)

    def chat_stream(self, messages, *, temperature, top_p, max_tokens, timeout=None):
        return super().chat_stream(messages, temperature=temperature, top_p=top_p, max_tokens=max_tokens, timeout=timeout)

    def quick_test(self):
        """짧은 타임아웃으로 연결 테스트를 수행한다.

        - 모델란이 비어 있으면 /models 에서 첫 번째 모델을 자동 선택하고
          self.config['model']에 기록한다 (대화상자에서 읽어갈 수 있게).
        - 모델란이 채워져 있으면 목록 조회 없이 바로 chat만 시도한다
          (LM Studio가 /models 를 비정상 반환해도 chat은 되는 경우 대응).
        """
        try:
            model = (self.config.get('model') or '').strip()
            if not model:
                models = self.list_models()
                if not models:
                    raise ProviderError('서버에 로드된 모델이 없습니다. LM Studio에서 모델을 먼저 Load 하세요.')
                model = models[0]
                self.config['model'] = model
            return self.chat(
                [{'role': 'user', 'content': 'Reply with exactly: 연결 테스트 성공'}],
                temperature=.1, top_p=.9, max_tokens=32, timeout=15,
            )
        except ProviderError:
            raise


class LMStudioProvider(OpenAICompatibleProvider):
    def __init__(self, config, cancel_check=None, abort_handler=None):
        cfg = dict(config or {})
        # Base URL이 비어 있으면 LM Studio 기본값으로 대체한다.
        # (build_unsaved 등에서 '' 가 넘어오면 기본 localhost를 덮어써 버리는 문제 방지)
        if not (cfg.get('base_url') or '').strip():
            cfg['base_url'] = 'http://localhost:1234/v1'
        super().__init__(cfg, cancel_check=cancel_check, abort_handler=abort_handler)