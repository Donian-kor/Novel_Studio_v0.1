from novel_studio.ai.prompts import master_plot, section_plan, chapter_plans
class PlotManager:
    def __init__(self,db,ai,project): self.db,self.ai,self.project=db,ai,project
    def generate_master(self):
        c=self.db.get_contract(); out=self.ai.generate(master_plot(self.db.get_plan(),c['content'] if c else '',self.project.settings['target_chapters']),temperature=.62,max_tokens=12000); self.db.set_meta('master_plot',out); return out
    def ranges(self):
        total=int(self.project.settings['target_chapters']); size=int(self.project.settings.get('section_size',5)); return [(s,min(s+size-1,total)) for s in range(1,total+1,size)]
    def generate_story_section(self,s,e,previous=''):
        c=self.db.get_contract(); return self.ai.generate(section_plan(self.db.get_meta('master_plot',''),c['content'] if c else '',s,e,previous),temperature=.60,max_tokens=10000)
    def generate_chapter_plans(self,s,e):
        c=self.db.get_contract(); secs=self.db.sections_overlapping(s,e); text='\n\n'.join(r['content'] for r in secs); state='\n'.join(r['snapshot'] for r in secs); return self.ai.generate(chapter_plans(text,c['content'] if c else '',s,e,state),temperature=.55,max_tokens=16000)
    
    def ranges(self):
        total=int(self.project.settings['target_chapters']); size=int(self.project.settings.get('section_size',5)); return [(s,min(s+size-1,total)) for s in range(1,total+1,size)]
    
    def ranges_by_size(self,size=25):
        total=int(self.project.settings['target_chapters']); size=max(1,int(size)); return [(s,min(s+size-1,total)) for s in range(1,total+1,size)]
    
    def generate_hierarchical_plans(self,chunk_size=25,progress=None):
        from novel_studio.plot.parser import parse_chapter_plans
        results=[]
        for s,e in self.ranges_by_size(chunk_size):
            self.db.set_plot_batch(s,e,'실행중')
            try:
                raw=self.generate_chapter_plans(s,e); plans=parse_chapter_plans(raw)
                expected=set(range(s,e+1)); actual={int(p[0]) for p in plans}
                if actual != expected:
                    missing=sorted(expected-actual); extra=sorted(actual-expected)
                    raise ValueError(f'{s}~{e}화 플롯 파싱 불완전: 누락={missing}, 범위 밖={extra}')
                for n,title,content in plans:self.db.save_chapter_plan(n,title,content,'초안')
                self.db.set_plot_batch(s,e,'완료'); results.append((s,e,len(plans)))
                if progress:progress(s,e,len(plans))
            except Exception:
                self.db.set_plot_batch(s,e,'실패'); raise
        return results
    
    def audit_long_form(self, size=50, progress=None, cancelled_check=None):
        """
        장편 연속성 검사 - 진행률 콜백과 취소 체크 지원
        
        Args:
            size: 한 번에 검사할 화 수 (기본 50화)
            progress: 진행률 콜백 함수 (current, total, current_range_str, result_text) -> None
            cancelled_check: 취소 여부 확인 함수 () -> bool
        
        Returns:
            전체 결과 텍스트
        """
        findings = []
        ranges = self.ranges_by_size(size)
        total = len(ranges)
        
        for idx, (s0, e0) in enumerate(ranges):
            # 취소 체크
            if cancelled_check and cancelled_check():
                break
            
            # 진행률 알림
            if progress:
                progress(idx + 1, total, f'{s0}~{e0}화', '')
            
            secs = self.db.sections_overlapping(s0, e0)
            source = '\n'.join(r['content'] for r in secs)[:22000]
            
            out = self.ai.generate(
                f'{s0}~{e0}화 설정/복선/시간축 연속성 문제만 검사하라. 추측 금지.\n{source}',
                temperature=.1, max_tokens=5000
            )
            
            self.db.add_continuity(e0, '정밀', '구간', out)
            findings.append(f'[{s0}~{e0}]\n{out}')
            
            # 진행률 알림 (결과 포함)
            if progress:
                progress(idx + 1, total, f'{s0}~{e0}화', out)
        
        return '\n\n'.join(findings)