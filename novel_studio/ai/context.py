from __future__ import annotations
from novel_studio.core.helpers import count_chars

class ContextManager:
    def __init__(self, db, project): self.db,self.project=db,project
    def build(self, chapter: int | None=None) -> str:
        blocks=[]
        c=self.db.contract()
        if c and c["content"]: blocks.append("[PLAN CONTRACT]\n"+c["content"][:9000])
        for key,title,limit in [("master_plan","MASTER PLAN",7000),("master_plot","MASTER PLOT",9000)]:
            v=self.db.get_meta(key,"")
            if v: blocks.append(f"[{title}]\n"+v[:limit])
        if chapter is None: return "\n\n".join(blocks)
        p=self.db.chapter_plan(chapter)
        if p: blocks.append(f"[CURRENT CHAPTER PLAN {chapter}]\n"+p["content"][:9000])
        for s in self.db.sections():
            if s["start_chapter"]<=chapter<=s["end_chapter"]:
                blocks.append(f"[CURRENT STORY SECTION {s['start_chapter']}~{s['end_chapter']}]\n"+(s["content"] or "")[:7000])
                if s["snapshot"]: blocks.append("[CURRENT SECTION SNAPSHOT]\n"+s["snapshot"][:6000])
                break
        snap=self.db.snapshot(f"chapter:{max(1,chapter-1)}")
        if snap: blocks.append("[LATEST STATE]\n"+snap["content"][:7000])
        recent=int(self.project.settings.get("memory_recent_chapters","4"))
        for n in range(max(1,chapter-recent),chapter):
            s=self.db.summary(n)
            if s: blocks.append(f"[SUMMARY {n}]\n{s['summary'][:3000]}")
        if chapter>1:
            prev=self.project.load_chapter(chapter-1)
            if prev:
                tail=int(self.project.settings.get("previous_tail_chars","1500")); blocks.append("[PREVIOUS CHAPTER TAIL]\n"+prev[-tail:])
        chars=self.db.characters()
        if chars: blocks.append("[CHARACTERS]\n"+"\n".join(f"- {r['name']}: {r['role']} / {r['personality']} / 목표={r['goal']}" for r in chars[:30]))
        worlds=self.db.worlds()
        if worlds: blocks.append("[WORLD]\n"+"\n".join(f"- {r['name']} ({r['category']}): {r['description'][:350]}" for r in worlds[:35]))
        fs=[r for r in self.db.foreshadows() if r["status"]!="회수"]
        if fs: blocks.append("[ACTIVE FORESHADOWING]\n"+"\n".join(f"- {r['code']} {r['title']}: 상태={r['status']}, 회수={r['reveal_chapter']}" for r in fs[:50]))
        return "\n\n".join(blocks)
    @staticmethod
    def estimate(text:str)->int: return count_chars(text)
