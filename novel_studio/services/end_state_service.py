from __future__ import annotations
from hashlib import sha256
from novel_studio.ai.prompts import state
from novel_studio.utils.cancellation import JobCancelled

class EndStateService:
    """연속성 기록을 생성하고 저장하는 서비스. 실제 원고에서 다음 화에 필요한 종료 상태만 생성한다."""
    def __init__(self, db, ai):
        self.db, self.ai = db, ai

    def generate(self, chapter: int, text: str) -> str:
        chapter = int(chapter)
        text = str(text or "")
        if not text.strip():
            raise ValueError("연속성 기록을 생성할 원고가 없습니다.")
        check=getattr(self.ai,"cancelled_check",None)
        if callable(check) and check():
            raise JobCancelled()
        prev=self.db.chapter_state(chapter-1) if chapter>1 else None
        prev_state=(prev["state"] if prev else "") or ""
        prompt=state(chapter,text)
        if prev_state:
            prompt += "\n\n[직전 화 연속성 기록]\n" + prev_state[:9000]
        prompt += "\n\n반드시 [핵심 사건][인물 상태][현재 위치/시간][부상/경지/능력][획득 정보/아이템][관계 변화][미해결 사건][복선/떡밥][다음 화 연결]만 포함하고, 원고에 없는 사실은 추측하지 마라."
        result=str(self.ai.generate(prompt, temperature=0.15, max_tokens=5000) or "").strip()
        if not result:
            raise ValueError("연속성 기록 생성 결과가 비어 있습니다.")
        check=getattr(self.ai,"cancelled_check",None)
        if callable(check) and check():
            raise JobCancelled()
        digest=sha256(text.encode("utf-8")).hexdigest()
        self.db.save_chapter_state(chapter, "", result, digest, "완료")
        return result
