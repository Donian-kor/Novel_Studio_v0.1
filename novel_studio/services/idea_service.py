from novel_studio.ai.prompts import idea_prompt
class IdeaService:
    def __init__(self,db,ai,project):self.db,self.ai,self.project=db,ai,project
    def generate(self):
        prev="\n".join(r["content"] for r in self.db.recent_ideas(10))
        r=self.ai.generate(idea_prompt(self.project.settings.get("genre",""),self.project.settings.get("mood",""),prev),temperature=.95,max_tokens=700); self.db.add_idea(r); return r
