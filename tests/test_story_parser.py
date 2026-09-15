from novel_studio.utils.story_parser import parse_chapter_stories

def test_parse_chapter_stories():
    raw="""### 제1화
제목: 첫 장
첫 내용
### 제2화
제목: 둘째 장
둘째 내용
"""
    assert parse_chapter_stories(raw,1,2)==[(1,"첫 장","첫 내용"),(2,"둘째 장","둘째 내용")]
