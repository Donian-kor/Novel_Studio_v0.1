import re

def parse_chapter_plans(text):
    hits=list(re.finditer(r'(?:^|\n)\s*(?:\[\s*화\s*번호\s*\]|제)\s*0*(\d{1,4})\s*화?',text,re.I))
    out=[]
    if not hits: return out
    for i,m in enumerate(hits):
        n=int(m.group(1)); body=text[m.end():hits[i+1].start() if i+1<len(hits) else len(text)].strip()
        title=''
        tm=re.search(r'\[\s*제목\s*\]\s*:?\s*(.+)',body)
        if not tm: tm=re.search(r'^\s*제목\s*:?\s*(.+)$',body,re.M)
        if tm:title=tm.group(1).strip()
        out.append((n,title,body))
    return out
