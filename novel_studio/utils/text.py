def count_chars(text, include_spaces=False):
    return len(text) if include_spaces else len(''.join(text.split()))


def check_spelling(text):
    """맞춤법 검사 (pyhanspell 사용, 없으면 폴백).

    Returns:
        (corrected_text, error_count, errors): 교정문, 오류 수, 오류 목록.
        pyhanspell이 없으면 (None, 0, []) 반환.
    """
    try:
        from hanspell import spell_checker
    except Exception:
        return None, 0, []
    result = spell_checker.check(text)
    return result.checked, len(result.errors), list(result.errors)


_AI_MARK_PATTERNS = [
    # 코드펜스
    (r'```[\w+-]*\n?', ''),
    (r'```', ''),
    # 헤딩 기호
    (r'(?m)^#{1,6}\s*', ''),
    # 굵게/기울임
    (r'\*\*\*(.+?)\*\*\*', r'\1'),
    (r'\*\*(.+?)\*\*', r'\1'),
    (r'(?<!\w)\*(?!\s)(.+?)(?<!\s)\*(?!\w)', r'\1'),
    (r'__(.+?)__', r'\1'),
    # 취소선
    (r'~~(.+?)~~', r'\1'),
    # 수평선
    (r'(?m)^\s*([-*_])\1{2,}\s*$', ''),
    # 인용 기호
    (r'(?m)^\s*>\s?', ''),
    # AI 특유 장식 이모지/기호 줄
    (r'(?m)^[\U0001F300-\U0001FAFF✨⭐🌟📌📖🔥💡🎭📝❖◆◇■□▲△●○★☆※☞☜☝☟↔→←↑↓]+\s*', ''),
]


def strip_ai_marks(text):
    """AI 특유 기호(마크다운/장식) 제거. (원고 내용은 유지)"""
    import re
    out = text
    for pat, rep in _AI_MARK_PATTERNS:
        out = re.sub(pat, rep, out)
    # 연속 빈 줄 3개 이상 → 2개로
    out = re.sub(r'\n{3,}', '\n\n', out)
    return out.strip()

