class AIEngine:
    def __init__(self,providers,settings): self.providers,self.settings=providers,settings
    def generate(self,messages,*,temperature=None,top_p=None,max_tokens=None):
        if isinstance(messages,str): messages=[{'role':'user','content':messages}]
        cfg=self.settings.data['ai']; return self.providers.provider().chat(messages,temperature=float(temperature if temperature is not None else cfg['temperature']),top_p=float(top_p if top_p is not None else cfg['top_p']),max_tokens=int(max_tokens if max_tokens is not None else cfg['max_tokens']))
    def generate_stream(self,messages,*,temperature=None,top_p=None,max_tokens=None):
        """토큰 스트리밍 버전: 조각 문자열을 yield한다."""
        if isinstance(messages,str): messages=[{'role':'user','content':messages}]
        cfg=self.settings.data['ai']
        yield from self.providers.provider().chat_stream(messages,temperature=float(temperature if temperature is not None else cfg['temperature']),top_p=float(top_p if top_p is not None else cfg['top_p']),max_tokens=int(max_tokens if max_tokens is not None else cfg['max_tokens']))
