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
    def set_cancel_handler(self, cancel_check, abort_handler=None) -> None:
        """정지 버튼과 연결되는 취소 훅을 ProviderManager까지 전달한다."""
        self.providers.set_cancel_handler(cancel_check, abort_handler)
    def abort(self) -> None:
        """진행 중인 provider 응답을 닫아 I/O를 즉시 중단한다."""
        self.providers.abort()
    def cancelled_check(self):
        """현재 취소 요청 상태를 반환하는 함수(순차 생성 경계에서 사용)."""
        return self.providers.cancel_check
