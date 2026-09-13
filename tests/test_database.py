import sqlite3
from pathlib import Path
from novel_studio.db.database import Database

def test_stats_and_range_queries(tmp_path):
    db = Database(tmp_path / 'novel.db')
    db.ensure_chapters(500, 5000)
    for n in (1, 250, 500):
        db.set_chapter_meta(n, f'{n}화', '작성완료', n, n+1, 5000)
    stats = db.chapter_stats()
    assert stats['total'] == 500
    assert stats['done'] == 3
    assert stats['total_chars'] == 751
    assert [r['number'] for r in db.chapter_range(249, 251)] == [249, 250, 251]
    db.close()

def test_targeted_context_queries_and_indexes(tmp_path):
    db = Database(tmp_path / 'novel.db')
    db.ensure_chapters(100, 5000)
    db.save_section(1, 10, '완료', 'A', 'S')
    db.save_section(11, 20, '완료', 'B', 'S')
    db.save_section(21, 30, '완료', 'C', 'S')
    assert db.section_for_chapter(15)['start_chapter'] == 11
    assert [r['start_chapter'] for r in db.sections_overlapping(9, 21)] == [1, 11, 21]
    for i in range(120):
        db.save_character({'name': f'인물{i}'})
        db.save_world({'name': f'세계{i}', 'category':'장소'})
        db.save_foreshadow({'code':f'F{i:03d}','title':f'복선{i}','status':'활성'})
        db.save_summary(i+1, f'요약{i}')
    assert len(db.characters(limit=50)) == 50
    assert len(db.world_entities(limit=60)) == 60
    assert len(db.foreshadows(limit=80, active_only=True)) == 80
    assert len(db.recent_summaries(120, 5)) == 5
    names = {r['name'] for r in db.characters(limit=50)}
    assert '인물0' in names
    index_names = {r['name'] for r in db.conn.execute("PRAGMA index_list('chapters')").fetchall()}
    assert 'idx_chapters_status' in index_names
    db.close()


def test_hierarchical_memory_storage(tmp_path):
    db = Database(tmp_path / 'novel.db')
    db.ensure_chapters(100, 5000)
    db.save_section(1, 10, '완료', 'section', 'legacy')
    db.save_summary(1, '요약1', '상태1')
    db.save_chapter_state(1, '요약1', '상태1', 'hash1')
    db.save_section_memory(1,10,'구간 기억','hash-s')
    assert db.section_memory_for_chapter(7)['content'] == '구간 기억'
    db.save_arc_memory(1,1,20,'아크 기억','hash-a')
    assert db.arc_memory_for_chapter(15)['content'] == '아크 기억'
    assert db.arc_bounds(100,5) == [(1,1,20),(2,21,40),(3,41,60),(4,61,80),(5,81,100)]
    idx = {r['name'] for r in db.conn.execute("PRAGMA index_list('section_memories')").fetchall()}
    assert 'idx_section_memories_start_end' in idx
    db.close()
