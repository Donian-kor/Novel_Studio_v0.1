from hashlib import sha256

class StateLedger:
    def __init__(self, db): self.db=db
    def record(self, kind, entity_key, chapter, state, source=''):
        h=sha256(((state or '')+(source or '')).encode('utf-8')).hexdigest()
        self.db.save_entity_state(kind,entity_key,int(chapter),state or '',h)
        return h
    def latest(self, kind, entity_key, before=None): return self.db.latest_entity_state(kind,entity_key,before)
