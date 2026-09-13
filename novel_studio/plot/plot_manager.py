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
