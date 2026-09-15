from __future__ import annotations
import re

_CHAPTER = re.compile(r"(?:^|\n)###\s*제(\d+)화\s*\n(?:제목\s*:\s*(.*?))?\n(.*?)(?=(?:\n###\s*제\d+화\b)|\Z)", re.S)

def parse_chapter_stories(raw: str, start: int, end: int):
    out=[]
    for m in _CHAPTER.finditer(str(raw or "")):
        n=int(m.group(1))
        if int(start) <= n <= int(end):
            out.append((n,(m.group(2) or "").strip(),(m.group(3) or "").strip()))
    return out
