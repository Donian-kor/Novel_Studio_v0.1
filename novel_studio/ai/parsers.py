from __future__ import annotations
import re

def extract_section(text: str, header: str) -> str:
    m = re.search(rf"\[{re.escape(header)}\](.*?)(?=\n\[[^\n]+\]|\Z)", text, re.S)
    return m.group(1).strip() if m else ""

def parse_chapter_plans(text: str):
    blocks = re.split(r"(?=\[화 번호\])", text)
    result=[]
    for block in blocks:
        m=re.search(r"\[화 번호\]\s*[:：]?\s*(\d+)", block)
        if not m: continue
        n=int(m.group(1)); t=extract_section(block,"제목") or f"{n}화"
        result.append((n,t,block.strip()))
    return result
