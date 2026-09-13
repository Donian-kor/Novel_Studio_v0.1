from pathlib import Path
from novel_studio.core.project import ProjectManager

def test_export_all_chapters_writes_merged_text(tmp_path):
    pm = ProjectManager()
    pm.create(tmp_path, '테스트 작품', '판타지', '무협', 3, 100, 10)
    pm.save_chapter(1, '첫 화 본문')
    pm.save_chapter(3, '셋째 화 본문')
    out = pm.export_all_chapters()
    assert out.exists() and out.parent.name == 'exports'
    text = out.read_text(encoding='utf-8')
    assert '제1화' in text and '첫 화 본문' in text
    assert '제2화' not in text
    assert '셋째 화 본문' in text

def test_export_all_chapters_raises_when_empty(tmp_path):
    import pytest
    pm = ProjectManager()
    pm.create(tmp_path, '빈 작품', '판타지', '무협', 2, 100, 10)
    with pytest.raises(RuntimeError):
        pm.export_all_chapters()
