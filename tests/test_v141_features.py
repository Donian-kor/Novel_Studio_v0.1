import json
from novel_studio.db.database import Database, CURRENT_SCHEMA_VERSION, MIGRATIONS
from novel_studio.intelligence.retrieval import RetrievalEngine
from novel_studio.intelligence.ledger import StateLedger
from novel_studio.memory.memory_manager import MemoryManager
from novel_studio.ai.context import ContextManager


class FakeAI:
    """요약/상태 프롬프트는 빈 응답, 엔티티 추출 프롬프트는 고정 JSON을 반환."""
    def __init__(self, entity_json=''): self.entity_json = entity_json
    def generate(self, prompt, *, temperature=None, top_p=None, max_tokens=None):
        if '상태가 실제로 변한' in prompt: return self.entity_json
        return ''


def test_retrieval_supplies_entity_states(tmp_path):
    db = Database(tmp_path / 'novel.db')
    db.save_entity_state('character', '한청', 3, '경지 상승', 'h')
    r = RetrievalEngine(db).retrieve(4)
    assert any(x['entity_key'] == '한청' and x['chapter_number'] == 3 for x in r['entity_states'])
    db.close()

def test_entity_timeline_is_ordered(tmp_path):
    db = Database(tmp_path / 'novel.db')
    for n, s in [(5, 'B'), (2, 'A'), (8, 'C')]:
        db.save_entity_state('character', '한청', n, s, 'h')
    rows = db.entity_timeline('character', '한청')
    assert [r['chapter_number'] for r in rows] == [2, 5, 8]
    db.close()

def test_memory_manager_extracts_changed_entities(tmp_path):
    db = Database(tmp_path / 'novel.db')
    db.ensure_chapters(3, 100)
    ai = FakeAI(entity_json=json.dumps([
        {'kind': '인물', 'name': '한청', 'change': '경지 상승'},
        {'kind': '장소', 'name': '북맹산', 'change': '문파가 점거'},
    ], ensure_ascii=False))
    mm = MemoryManager(db, ai, StateLedger(db))
    mm.update(1, '한청이 북맹산에 도착했다. 경지가 상승했다.')
    assert db.latest_entity_state('character', '한청')['chapter_number'] == 1
    assert db.latest_entity_state('world', '북맹산')['chapter_number'] == 1
    # 같은 원고로 재호출하면 재추출하지 않는다(source_hash 생략 로직)
    before = db.conn.execute("SELECT COUNT(*) FROM entity_state_ledger").fetchone()[0]
    mm.update(1, '한청이 북맹산에 도착했다. 경지가 상승했다.')
    after = db.conn.execute("SELECT COUNT(*) FROM entity_state_ledger").fetchone()[0]
    assert before == after
    db.close()

def test_schema_migrations_run_sequentially(tmp_path):
    db = Database(tmp_path / 'novel.db')
    db.execute("UPDATE schema_meta SET version=2")
    db._migrate_schema()
    row = db.conn.execute("SELECT version FROM schema_meta").fetchone()
    assert int(row['version']) == CURRENT_SCHEMA_VERSION
    idx = db.conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_entity_state_updated'").fetchone()
    assert idx is not None
    db.close()

def test_migration_registry_is_monotonic():
    assert sorted(MIGRATIONS) == list(range(2, CURRENT_SCHEMA_VERSION + 1))

def test_context_budget_keeps_high_priority_blocks(tmp_path):
    db = Database(tmp_path / 'novel.db')
    db.save_plan('계획' * 5000)          # [MASTER PLAN]
    db.set_meta('master_plot', '플롯' * 5000)  # [MASTER PLOT]
    class S:
        data = {'ai': {'previous_tail_chars': 100, 'context_budget_tokens': 300}}
    class P:
        def load_chapter(self, n): return '이전 화 본문'
    cm = ContextManager(db, P(), S())
    out = cm.build(chapter=2, extra='집필 부탁')
    assert '[MASTER PLAN]' in out        # 최우선 블록은 항상 유지
    assert '[USER REQUEST]' in out       # 사용자 요청은 항상 유지
    assert '[MASTER PLOT]' not in out    # 예산 초과로 하위 블록 제거
    db.close()
