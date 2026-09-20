from __future__ import annotations

from novel_studio.ai import prompts


def test_genre_line_is_defined() -> None:
    """_genre_line이 정의되어 있어야 한다.

    v1.5.x 리팩토링에서 정의가 삭제된 채 idea()/master()의 호출부만 남아
    'NameError: name \\'_genre_line\\' is not defined' 오류(작업 오류 창)가 발생했다.
    """
    assert callable(prompts._genre_line)


def test_genre_line_injects_preset_guide() -> None:
    """장르 프리셋이 있으면 특성 문구가 아이디어/기획 프롬프트에 주입된다."""
    meta = {"genre": "선협", "mood": "진중", "target_chapters": 100, "chapter_chars": 5000}
    idea = prompts.idea(meta, "이전 시안")
    master = prompts.master("아이디어 원문", meta)
    assert "장르:선협" in idea
    assert prompts.GENRE_GUIDE["선협"] in idea
    assert "분위기:진중" in idea
    assert "장르:선협" in master
    assert prompts.GENRE_GUIDE["선협"] in master


def test_genre_line_skips_guide_for_custom_genre() -> None:
    """GENRE_GUIDE에 없는 장르('직접 입력' 등)는 특성 문구 없이 장르만 주입된다."""
    meta = {"genre": "직접 입력", "mood": "밝음", "target_chapters": 100, "chapter_chars": 5000}
    idea = prompts.idea(meta, "")
    assert "장르:직접 입력" in idea
    assert "장르 특성" not in idea
    assert "분위기:밝음" in idea


def test_genre_line_handles_missing_or_blank_values() -> None:
    """설정 키가 없거나 값이 None/빈 문자열이어도 예외 없이 기본 장르로 동작한다."""
    assert prompts._genre_line({}).startswith("장르:선협")
    assert prompts._genre_line({}).endswith("분위기:")
    assert prompts._genre_line({"genre": None, "mood": None}).startswith("장르:선협")
    assert "장르:선협" in prompts.idea({"genre": "", "mood": ""}, "")