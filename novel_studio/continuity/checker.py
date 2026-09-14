from novel_studio.ai.prompts import continuity
from novel_studio.jobs.worker import JobCancelled
from novel_studio.services.interfaces import ContinuityResult


class ContinuityChecker:
    def __init__(self, db, ai, context): self.db, self.ai, self.context = db, ai, context

    def check_chapter(self, chapter: int, text: str):
        """단일 화 연속성 검사. 취소 시 부분 결과 기록 없이 즉시 중단한다."""
        check = getattr(self.ai, "cancelled_check", None)
        if callable(check) and check():
            raise JobCancelled()
        out = self.ai.generate(continuity(chapter, text, self.context.build(chapter)), temperature=.15, max_tokens=6000)
        check = getattr(self.ai, "cancelled_check", None)
        if callable(check) and check():
            raise JobCancelled()
        self.db.add_continuity(chapter, '검사', '전체', out)
        return ContinuityResult(
            chapter=chapter, severity='info', category='전체',
            message=out, evidence='')

    def check(self, n, text):
        """하위 호환 별칭: check_chapter()와 동일하다."""
        return self.check_chapter(n, text)
