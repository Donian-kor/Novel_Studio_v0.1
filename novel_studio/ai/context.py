class ContextManager:
    def __init__(self,db,project,settings): self.db,self.project,self.settings=db,project,settings
    def build(self,chapter=None,extra=''):
        b=[]; c=self.db.get_contract()
        if c and c['content']: b.append('[PLAN CONTRACT]\n'+c['content'][:8000])
        if self.db.get_plan(): b.append('[MASTER PLAN]\n'+self.db.get_plan()[:9000])
        if self.db.get_meta('master_plot',''): b.append('[MASTER PLOT]\n'+self.db.get_meta('master_plot')[:9000])
        if chapter:
            p=self.db.chapter_plan(chapter)
            if p:b.append(f'[CHAPTER PLAN {chapter}]\n'+p['content'][:8000])
            sec=next((s for s in self.db.sections() if s['start_chapter']<=chapter<=s['end_chapter']),None)
            if sec:b.append('[CURRENT STORY SECTION]\n'+sec['content'][:7000]+'\n[SNAPSHOT]\n'+(sec['snapshot'] or '')[:5000])
            for n in range(max(1,chapter-int(self.settings.data['ai']['memory_recent_chapters'])),chapter):
                s=self.db.summary(n)
                if s:b.append(f'[SUMMARY {n}]\n'+s['summary'][:3000])
            if chapter>1:
                prev=self.project.load_chapter(chapter-1); tail=int(self.settings.data['ai']['previous_tail_chars'])
                if prev:b.append('[PREVIOUS TAIL]\n'+prev[-tail:])
        chars=self.db.characters()
        if chars:b.append('[CHARACTERS]\n'+'\n'.join(f"- {x['name']}: {x['role']} / {x['personality']} / 목표={x['goal']}" for x in chars[:50]))
        worlds=self.db.world_entities()
        if worlds:b.append('[WORLD]\n'+'\n'.join(f"- {x['name']} ({x['category']}): {x['description'][:400]}" for x in worlds[:60]))
        fs=[x for x in self.db.foreshadows() if x['status']!='회수']
        if fs:b.append('[ACTIVE FORESHADOWING]\n'+'\n'.join(f"- {x['code']} {x['title']} / 회수:{x['reveal_chapter']}" for x in fs[:80]))
        if extra:b.append('[USER REQUEST]\n'+extra)
        return '\n\n'.join(b)
