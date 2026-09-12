from __future__ import annotations
import json, urllib.request, urllib.error
class LMStudioClient:
    def __init__(self, base_url='http://localhost:1234', model=''):
        self.base_url=base_url.rstrip('/')
        self.model=model
    def list_models(self):
        req=urllib.request.Request(self.base_url+'/v1/models',headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=10) as r: return json.loads(r.read().decode('utf-8')).get('data',[])
    def chat(self,messages,temperature=0.7,max_tokens=6000,model=None):
        payload={'model':model or self.model,'messages':messages,'temperature':temperature,'max_tokens':max_tokens}
        req=urllib.request.Request(self.base_url+'/v1/chat/completions',data=json.dumps(payload,ensure_ascii=False).encode('utf-8'),headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=600) as r:
            data=json.loads(r.read().decode('utf-8'))
        try: return data['choices'][0]['message']['content']
        except Exception as e: raise RuntimeError(f'LM Studio 응답 형식 오류: {e}')
