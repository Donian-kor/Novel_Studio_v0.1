from novel_studio.db.database import Database
from novel_studio.intelligence.retrieval import RetrievalEngine
from novel_studio.intelligence.diff import MasterDiffService

class FakeAI:
    def generate(self, prompt, **kwargs):
        if "변경점을" in prompt:
            return "```json\n[{\"type\":\"modify\",\"path\":\"x\",\"before\":\"a\",\"after\":\"b\",\"reason\":\"r\"}]\n```"
        return ""

def test_fts_indexes_saved_entities(tmp_path):
    db=Database(tmp_path/'novel.db')
    db.save_character({'name':'한청','role':'주인공','profile':'검을 든다'})
    db.save_plan('한청의 성장 이야기')
    hits=db.search('한청',20)
    assert any(label=='character' for label,_ in hits)
    db.close()

def test_retrieval_search_is_available(tmp_path):
    db=Database(tmp_path/'novel.db')
    db.ensure_chapters(3,5000)
    db.save_character({'name':'한청','role':'주인공'})
    r=RetrievalEngine(db).retrieve(1,'한청')
    assert r['search']
    db.close()

def test_entity_state_ledger_is_queryable(tmp_path):
    db=Database(tmp_path/'novel.db')
    db.save_character({'name':'한청','role':'주인공'})
    cid=db.conn.execute("SELECT id FROM characters WHERE name='한청'").fetchone()['id']
    db.save_entity_state('character','한청',3,'경지 상승','hash')
    row=db.latest_entity_state('character','한청',4)
    assert row['chapter_number']==3
    db.close()

def test_master_diff_parses_fenced_json(tmp_path):
    db=Database(tmp_path/'novel.db')
    out=MasterDiffService(db,FakeAI()).propose('old','new')
    assert len(out['changes'])==1
    db.close()


def test_delete_removes_search_index(tmp_path):
    db=Database(tmp_path/'novel.db')
    db.save_character({'name':'삭제인물','role':'조연'})
    assert db.search('삭제인물')
    db.delete_character('삭제인물')
    assert not db.search('삭제인물')
    db.close()
