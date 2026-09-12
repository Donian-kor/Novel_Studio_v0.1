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
        c=self.db.get_contract(); secs=[r for r in self.db.sections() if not (r['end_chapter']<s or r['start_chapter']>e)]; text='\n\n'.join(r['content'] for r in secs); state='\n'.join(r['snapshot'] for r in secs); return self.ai.generate(chapter_plans(text,c['content'] if c else '',s,e,state),temperature=.55,max_tokens=16000)
