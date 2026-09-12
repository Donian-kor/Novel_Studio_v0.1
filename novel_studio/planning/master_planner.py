from novel_studio.ai.prompts import master, section, contract, SECTIONS
class MasterPlanner:
    def __init__(self,db,ai,project): self.db,self.ai,self.project=db,ai,project
    def create_master(self,idea_text):
        out=self.ai.generate([{'role':'system','content':'장편 웹소설 마스터 기획자'},{'role':'user','content':master(idea_text,self.project.settings)}],temperature=.72,max_tokens=12000)
        self.db.save_plan(out); self.db.set_meta('idea',idea_text); return out
    def generate_section(self,name):
        out=self.ai.generate(section(name,self.db.get_plan(),self.project.settings['target_chapters'],self.db.section_content(name)),temperature=.68,max_tokens=9000)
        self.db.save_section_content(name,out,'초안'); return out
    def generate_all_sections(self,progress=None):
        results={}
        for name in SECTIONS:
            results[name]=self.generate_section(name)
            if progress: progress(name)
        return results
    def extract_contract(self):
        txt='\n\n'.join(f'[{s}]\n{self.db.section_content(s)}' for s in SECTIONS)
        out=self.ai.generate(contract(self.db.get_plan(),txt,self.project.settings['target_chapters']),temperature=.22,max_tokens=6000)
        self.db.save_contract(out,False); return out
