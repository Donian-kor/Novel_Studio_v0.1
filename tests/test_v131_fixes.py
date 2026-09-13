from novel_studio.db.database import Database
from novel_studio.plot.plot_manager import PlotManager
from novel_studio.plot.parser import parse_chapter_plans

class FakeAI:
    def generate(self, prompt, **kwargs):
        return "### 제1화\n제목: 시작\n본문\n\n### 제2화\n제목: 전개\n본문\n"

class FakeProject:
    settings = {'target_chapters': 2, 'section_size': 1}

def test_parser_contract_is_tuple_based():
    plans = parse_chapter_plans('### 제1화\n제목: 시작\n본문')
    assert plans == [(1, '시작', '제목: 시작\n본문')]

def test_hierarchical_plots_saves_tuple_results(tmp_path):
    db = Database(tmp_path / 'novel.db')
    db.ensure_chapters(2, 5000)
    db.save_contract('기준', False)
    db.set_meta('master_plot', '전체 플롯')
    pm = PlotManager(db, FakeAI(), FakeProject())
    results = pm.generate_hierarchical_plans(2)
    assert results == [(1, 2, 2)]
    rows = db.chapter_plans()
    assert [r['chapter_number'] for r in rows] == [1, 2]
    db.close()
