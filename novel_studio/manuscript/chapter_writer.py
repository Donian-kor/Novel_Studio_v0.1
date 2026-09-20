from novel_studio.ai.prompts import write

class ChapterWriter:
    def __init__(self, db, ai, project, context):
        self.db = db
        self.ai = ai
        self.project = project
        self.context = context

    def _max_tokens(self):
        cfg = getattr(self.ai, 'settings', None)
        if cfg is not None:
            try:
                return int(cfg.data['ai'].get('max_tokens', 0))
            except Exception:
                pass
        target = int(self.project.settings['chapter_chars'])
        return max(9000, target * 2)

    def write(self, n, extra=''):
        target = int(self.project.settings['chapter_chars'])
        tol = int(self.project.settings['tolerance'])
        return self.ai.generate(write(self.context.build(n, extra), n, target, tol), temperature=.72, max_tokens=self._max_tokens())

    def write_stream(self, n, extra=''):
        target = int(self.project.settings['chapter_chars'])
        tol = int(self.project.settings['tolerance'])
        return self.ai.generate_stream(write(self.context.build(n, extra), n, target, tol), temperature=.72, max_tokens=self._max_tokens())

    def adjust(self, text, target, tol):
        # 빈 원고로 AI 보정을 호출하면 "원고를 제공하지 않았다"는 거부 응답이
        # 생성되어 그대로 파일에 저장되는 악순환이 생긴다. 미리 차단한다.
        text = str(text or '')
        if not text.strip():
            raise ValueError('보정할 원고가 비어 있어 AI 분량 보정을 건너뜁니다.')
        return self.ai.generate(f'이 원고의 사건과 문체를 유지하며 {target-tol}~{target+tol}자로 자연스럽게 조정하라. 본문만 출력.\n{text}', temperature=.35, max_tokens=self._max_tokens())
