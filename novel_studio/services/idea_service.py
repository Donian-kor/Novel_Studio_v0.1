from novel_studio.ai.prompts import idea as idea_prompt

class IdeaService:
    def __init__(self, db, ai, project):
        self.db, self.ai, self.project = db, ai, project

    def generate(self):
        previous = '\n'.join(r['content'] for r in self.db.recent_ideas(10))
        text = self.ai.generate(idea_prompt(self.project.settings, previous), temperature=.9, max_tokens=800)
        self.db.add_idea(text)
        return text
