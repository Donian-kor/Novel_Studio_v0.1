"""AI 화별 플롯 응답을 DB 저장 단위로 변환하는 파서."""
from __future__ import annotations
import re

# 한 줄 단위로만 헤더를 인식한다. \s 대신 [ \t]를 사용해 다음 줄 내용이 섞이지 않게 한다.
_HEADER_PATTERNS = [
    re.compile(r"(?im)^[ \t]*(?:#{1,6}[ \t]*)?\[[ \t]*화[ \t]*번호[ \t]*\][ \t]*[:：\-]?[ \t]*0*(\d{1,4})[ \t]*화?[ \t]*$"),
    re.compile(r"(?im)^[ \t]*(?:#{1,6}[ \t]*)?제[ \t]*0*(\d{1,4})[ \t]*화[ \t]*(?:[\-–—:][ \t]*)?([^\r\n]*)$"),
    re.compile(r"(?im)^[ \t]*(?:#{1,6}[ \t]*)?0*(\d{1,4})[ \t]*화[ \t]*(?:[\.:\-–—][ \t]*)?([^\r\n]*)$"),
]


def _find_headers(text: str):
    candidates = []
    for pattern in _HEADER_PATTERNS:
        for m in pattern.finditer(text):
            title = (m.group(2) or "").strip() if m.lastindex >= 2 else ""
            candidates.append((m.start(), m.end(), int(m.group(1)), title))
    candidates.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    unique = []
    used_starts = set()
    for item in candidates:
        if item[0] in used_starts:
            continue
        used_starts.add(item[0])
        unique.append(item)
    return unique


def parse_chapter_plans(text: str):
    """다양한 AI 헤더 형식을 허용해 [(화번호, 제목, 본문)]으로 변환한다."""
    if not isinstance(text, str) or not text.strip():
        return []
    headers = _find_headers(text)
    if not headers:
        return []

    out = []
    seen = set()
    for i, (_, end, number, inline_title) in enumerate(headers):
        next_start = headers[i + 1][0] if i + 1 < len(headers) else len(text)
        body = text[end:next_start].strip()
        title = inline_title
        title_match = re.search(r"(?im)^[ \t]*\[[ \t]*제목[ \t]*\][ \t]*[:：\-]?[ \t]*(.+?)[ \t]*$", body)
        if not title_match:
            title_match = re.search(r"(?im)^[ \t]*제목[ \t]*[:：\-]?[ \t]*(.+?)[ \t]*$", body)
        if title_match:
            title = title_match.group(1).strip()
        if not body or number in seen:
            continue
        seen.add(number)
        out.append((number, title, body))
    return out


def validate_chapter_plans(plans, start: int, end: int):
    """요청 범위의 모든 화가 정확히 한 번씩 파싱되었는지 검사한다."""
    expected = set(range(int(start), int(end) + 1))
    actual = {int(n) for n, _, _ in plans if int(start) <= int(n) <= int(end)}
    return {
        "valid": actual == expected,
        "expected": expected,
        "actual": actual,
        "missing": sorted(expected - actual),
        "extra": sorted(actual - expected),
    }
