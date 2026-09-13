from novel_studio.intelligence.retrieval import RetrievalEngine

class ContextManager:
    def __init__(self,db,project,settings): self.db,self.project,self.settings=db,project,settings; self.retrieval=RetrievalEngine(db)
    def build(self,chapter=None,extra=''):
        b=[]; c=self.db.get_contract(); plan=self.db.get_plan(); mp=self.db.get_meta('master_plot','')
        if c and c['content']: b.append('[PLAN CONTRACT]\n'+c['content'][:8000])
        if plan: b.append('[MASTER PLAN]\n'+plan[:9000])
        if mp: b.append('[MASTER PLOT]\n'+mp[:9000])
        if chapter:
            r=self.retrieval.retrieve(chapter,extra); p=r['plan']; sec=r['section']
            if p:b.append(f'[CHAPTER PLAN {chapter}]\n'+p['content'][:8000])
            if sec:b.append('[CURRENT STORY SECTION]\n'+sec['content'][:6000]+'\n[SECTION SNAPSHOT]\n'+(sec['snapshot'] or '')[:4500])
            for key,label,lim in [('section_memory','SECTION MEMORY',6500),('arc_memory','ARC MEMORY',7000)]:
                row=r[key]
                if row:b.append(f'[{label}]\n'+(row['content'] or '')[:lim])
            recent=int(self.settings.data['ai'].get('memory_recent_chapters',5))
            for row in r['recent_summaries'][:recent]:b.append(f"[SUMMARY {row['chapter_number']}]\n"+(row['summary'] or '')[:3000])
            prev=r['previous_state']
            if prev:b.append(f"[LATEST CONFIRMED STATE {prev['chapter_number']}]\n"+(prev['state'] or '')[:9000])
            if chapter>1:
                prev_text=self.project.load_chapter(chapter-1); tail=int(self.settings.data['ai']['previous_tail_chars'])
                if prev_text:b.append('[PREVIOUS TAIL]\n'+prev_text[-tail:])
            if r['timeline']:b.append('[LOCAL TIMELINE]\n'+'\n'.join(f"- {x['chapter_number']}화 {x['title']}: {x['description']}" for x in r['timeline'][:30]))
            if r['events']:b.append('[LOCAL EVENTS]\n'+'\n'.join(f"- {x['start_chapter']}~{x['end_chapter'] or x['start_chapter']}화 {x['title']}: {x['description']}" for x in r['events'][:20]))
            if r.get('entity_states'):
                b.append('[ENTITY STATE LEDGER]\n'+'\n'.join(f"- {x['kind']}:{x['entity_key']} / {x['chapter_number']}화 / {(x['state'] or '')[:1600]}" for x in r['entity_states'][:40]))
            if r.get('search'):
                b.append('[DB SEARCH EVIDENCE]\n'+'\n'.join(f"- {label}: {row.get('content','')}" for label,row in r['search']))
            chars,worlds,fs=r['characters'],r['world'],r['foreshadowing']
        else: chars=self.db.characters(limit=40); worlds=self.db.world_entities(limit=40); fs=self.db.foreshadows(limit=60,active_only=True)
        if chars:b.append('[RELEVANT CHARACTERS]\n'+'\n'.join(f"- {x['name']}: {x['role']} / {x['personality']} / 목표={x['goal']}" for x in chars))
        if worlds:b.append('[RELEVANT WORLD]\n'+'\n'.join(f"- {x['name']} ({x['category']}): {(x['description'] or '')[:400]}" for x in worlds))
        if fs:b.append('[RELEVANT FORESHADOWING]\n'+'\n'.join(f"- {x['code']} {x['title']} / 상태={x['status']} / 회수={x['reveal_chapter']}" for x in fs))
        if extra:b.append('[USER REQUEST]\n'+extra)
        return '\n\n'.join(self._fit_budget(b))

    def _fit_budget(self,b):
        """토큰 예산을 넘으면 저우선순위 블록부터 제거한다.

        - 블록 순서가 곧 우선순위(PLAN CONTRACT > 마스터 기획/플롯 > 직전 상태 > 참고 자료)이므로
          앞에서부터 누적 배분하고, 예산을 넘기는 블록부터 버린다.
        - 첫 블록(PLAN CONTRACT 등 최상위 기준)과 [USER REQUEST]는 항상 유지한다.
        - 토큰 수는 한영 혼합 텍스트 기준 근사값(토큰≈글자/2.2)으로 계산한다.
        """
        try: budget=int(self.settings.data['ai'].get('context_budget_tokens',60000) or 60000)
        except Exception: budget=60000
        if budget<=0 or not b: return b
        keep=[b[0]]; used=len(b[0])/2.2
        for blk in b[1:]:
            need=len(blk)/2.2
            if blk.startswith('[USER REQUEST]'):
                keep.append(blk); used+=need; continue
            if used+need<=budget: keep.append(blk); used+=need
        return keep
