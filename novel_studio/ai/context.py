try:
    import tiktoken
except ImportError:  # optional dependency; character-based fallback keeps core usable
    tiktoken = None
from novel_studio.intelligence.retrieval import RetrievalEngine


class ContextManager:
    def __init__(self, db, project, settings):
        self.db = db
        self.project = project
        self.settings = settings
        self.retrieval = RetrievalEngine(db)
        self._tokenizer = None
        self._tokenizer_model = None

    def _get_tokenizer(self):
        """활성 모델에 맞는 tiktoken tokenizer를 반환합니다."""
        if self._tokenizer is not None and self._tokenizer_model == self._get_active_model():
            return self._tokenizer

        model = self._get_active_model()
        if tiktoken is None:
            self._tokenizer = False
            self._tokenizer_model = model
            return None
        try:
            # 모델별 인코딩 매핑
            if model.startswith('gpt-4') or model.startswith('gpt-3.5'):
                encoding = tiktoken.encoding_for_model(model)
            elif model.startswith('gpt-'):
                encoding = tiktoken.encoding_for_model('gpt-3.5-turbo')
            elif 'claude' in model.lower():
                # Claude는 GPT-4와 유사한 토크나이저 사용
                encoding = tiktoken.get_encoding('cl100k_base')
            elif 'gemini' in model.lower():
                # Gemini도 cl100k_base 사용
                encoding = tiktoken.get_encoding('cl100k_base')
            else:
                # 기본값: cl100k_base (GPT-4/3.5 호환)
                encoding = tiktoken.get_encoding('cl100k_base')
        except Exception:
            # 폴백: cl100k_base
            encoding = tiktoken.get_encoding('cl100k_base')

        self._tokenizer = encoding
        self._tokenizer_model = model
        return encoding

    def _get_active_model(self):
        """현재 활성화된 모델명을 반환합니다."""
        try:
            active_provider = self.settings.data.get('active_provider', 'lmstudio')
            provider_config = self.settings.data.get('providers', {}).get(active_provider, {})
            model = provider_config.get('model', '')
            return model
        except Exception:
            return 'gpt-3.5-turbo'

    def count_tokens(self, text: str) -> int:
        """텍스트의 정확한 토큰 수를 반환합니다."""
        if not text:
            return 0
        try:
            tokenizer = self._get_tokenizer()
            if tokenizer is None:
                return max(1, len(text) // 2)
            return len(tokenizer.encode(text))
        except Exception:
            # 폴백: 근사치
            return max(1, len(text) // 2)

    def build(self, chapter=None, extra=''):
        b = []
        c = self.db.get_contract()
        plan = self.db.get_plan()
        mp = self.db.get_meta('master_plot', '')
        if c and c['content']:
            b.append('[PLAN CONTRACT]\n' + c['content'][:8000])
        if plan:
            b.append('[MASTER PLAN]\n' + plan[:9000])
        if mp:
            b.append('[MASTER PLOT]\n' + mp[:9000])
        if chapter:
            r = self.retrieval.retrieve(chapter, extra)
            p = r['plan']
            sec = r['section']
            if p:
                b.append(f'[CURRENT CHAPTER STORY {chapter}]\n' + (p['content'] or '')[:8000])
            if sec:
                b.append('[CURRENT LONG STORY SECTION]\n' + sec['content'][:9000])
            sub = self.db.story_subsection_for_chapter(chapter) if hasattr(self.db, 'story_subsection_for_chapter') else None
            if sub:
                b.append('[CURRENT SUB STORY SECTION]\n' + (sub['content'] or '')[:6500])
            prev = r['previous_state']
            if prev:
                b.append(f"[PREVIOUS CHAPTER END STATE {prev['chapter_number']}]\n" + (prev['state'] or '')[:9000])
            recent = int(self.settings.data['ai'].get('end_state_recent_chapters', 5))
            for row in (r.get('recent_states') or [])[:recent]:
                if prev and int(row['chapter_number']) == int(prev['chapter_number']):
                    continue
                b.append(f"[RECENT END STATE {row['chapter_number']}]\n" + (row['state'] or '')[:5000])
            if chapter > 1:
                prev_text = self.project.load_chapter(chapter - 1)
                tail = int(self.settings.data['ai']['previous_tail_chars'])
                if prev_text:
                    b.append('[PREVIOUS TAIL]\n' + prev_text[-tail:])
            if r['timeline']:
                b.append('[LOCAL TIMELINE]\n' + '\n'.join(f"- {x['chapter_number']}화 {x['title']}: {x['description']}" for x in r['timeline'][:30]))
            if r['events']:
                b.append('[LOCAL EVENTS]\n' + '\n'.join(f"- {x['start_chapter']}~{x['end_chapter'] or x['start_chapter']}화 {x['title']}: {x['description']}" for x in r['events'][:20]))
            if r.get('search'):
                b.append('[DB SEARCH EVIDENCE]\n' + '\n'.join(f"- {label}: {row.get('content', '')}" for label, row in r['search']))
            chars, worlds, fs = r['characters'], r['world'], r['foreshadowing']
        else:
            chars = self.db.characters(limit=40)
            worlds = self.db.world_entities(limit=40)
            fs = self.db.foreshadows(limit=60, active_only=True)
        if chars:
            b.append('[RELEVANT CHARACTERS]\n' + '\n'.join(f"- {x['name']}: {x['role']} / {x['personality']} / 목표={x['goal']}" for x in chars))
        if worlds:
            b.append('[RELEVANT WORLD]\n' + '\n'.join(f"- {x['name']} ({x['category']}): {(x['description'] or '')[:400]}" for x in worlds))
        if fs:
            b.append('[RELEVANT FORESHADOWING]\n' + '\n'.join(f"- {x['code']} {x['title']} / 상태={x['status']} / 회수={x['reveal_chapter']}" for x in fs))
        if extra:
            b.append('[USER REQUEST]\n' + extra)
        return '\n\n'.join(self._fit_budget(b))

    def _fit_budget(self, b):
        """토큰 예산을 넘으면 저우선순위 블록부터 제거한다.

        - 블록 순서가 곧 우선순위(PLAN CONTRACT > 마스터 기획/플롯 > 직전 상태 > 참고 자료)이므로
          앞에서부터 누적 배분하고, 예산을 넘기는 블록부터 버린다.
        - 첫 블록(PLAN CONTRACT 등 최상위 기준)과 [USER REQUEST]는 항상 유지한다.
        - 토큰 수는 tiktoken으로 정확하게 계산한다.
        """
        try:
            budget = int(self.settings.data['ai'].get('context_budget_tokens', 60000) or 60000)
        except Exception:
            budget = 60000
        if budget <= 0 or not b:
            return b
        keep = [b[0]]
        used = self.count_tokens(b[0])
        for blk in b[1:]:
            need = self.count_tokens(blk)
            if blk.startswith('[USER REQUEST]'):
                keep.append(blk)
                used += need
                continue
            if used + need <= budget:
                keep.append(blk)
                used += need
        return keep