from ._base import BaseView
class DashboardView(BaseView):
    def __init__(self,w): super().__init__(w); self.mount('dashboard.ui'); self.w=w; self.summaryLabel=self.ui.findChild(__import__('PySide6.QtWidgets',fromlist=['QLabel']).QLabel,'summaryLabel')
    def refresh(self):
        p=self.w.pm.settings; rows=self.w.db.chapters(); done=sum(1 for r in rows if r['status'] in ('작성완료','확정','윤문완료')); total=int(p.get('target_chapters',500)); chars=sum(r['char_count'] for r in rows); self.summaryLabel.setText(f"작품: {p.get('title','')}\n\n현재 작업: {self.w.current}화 / {total}화\n완료: {done}화 ({done/max(1,total)*100:.1f}%)\n총 글자수: {chars:,}자\n화당 목표: {int(p.get('chapter_chars',5000)):,}자\n활성 복선: {len([x for x in self.w.db.foreshadows() if x['status']!='회수'])}")
