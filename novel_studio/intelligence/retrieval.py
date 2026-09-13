class RetrievalEngine:
    def __init__(self, db): self.db=db
    def retrieve(self, chapter, query=''):
        chapter=int(chapter); sec=self.db.section_for_chapter(chapter)
        start,end=(sec['start_chapter'],sec['end_chapter']) if sec else (max(1,chapter-10),chapter+10)
        out={
            'chapter':self.db.chapter(chapter),'plan':self.db.chapter_plan(chapter),'section':sec,
            'section_memory':self.db.section_memory_for_chapter(chapter),
            'arc_memory':self.db.arc_memory_for_chapter(chapter),
            'recent_summaries':self.db.recent_summaries(chapter-1,5),
            'previous_state':self.db.latest_chapter_state(chapter-1),
            'characters':self.db.characters_relevant(chapter,40),
            'world':self.db.world_relevant(chapter,40),
            'foreshadowing':self.db.foreshadows_relevant(chapter,60),
            'timeline':self.db.timeline(start=start,end=end,limit=80),
            'events':self.db.major_events(start=start,end=end,limit=50),
            'entity_states':self.db.entity_states_recent(chapter,span=10,limit=60),
            'search':self.db.search(query,25) if query else []
        }
        return out
