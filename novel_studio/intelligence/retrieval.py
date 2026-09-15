class RetrievalEngine:
    def __init__(self, db):
        self.db = db

    def retrieve(self, chapter, query=''):
        chapter = int(chapter)
        sec = self.db.section_for_chapter(chapter)
        start, end = ((sec['start_chapter'], sec['end_chapter']) if sec
                      else (max(1, chapter - 10), chapter + 10))
        return {
            'chapter': self.db.chapter(chapter),
            'plan': self.db.chapter_story(chapter),
            'section': sec,
            'previous_state': self.db.latest_chapter_state(chapter - 1),
            'recent_states': self.db.chapter_states(start=max(1, chapter - 5), end=chapter - 1, limit=5),
            'characters': self.db.characters_relevant(chapter, 40),
            'world': self.db.world_relevant(chapter, 40),
            'foreshadowing': self.db.foreshadows_relevant(chapter, 60),
            'timeline': self.db.timeline(start=start, end=end, limit=80),
            'events': self.db.major_events(start=start, end=end, limit=50),
            'entity_states': [],
            'search': self.db.search(query, 25) if query else [],
        }
