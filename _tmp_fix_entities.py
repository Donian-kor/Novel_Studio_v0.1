"""entities.py 수정 스크립트"""
import pathlib

path = pathlib.Path(r"c:/Users/donian/Desktop/python/Novel_Studio/novel_studio/ui/views/entities.py")
content = path.read_text(encoding="utf-8")
lines = content.splitlines(True)

for i, line in enumerate(lines):
    if i == 263 and "ROLE_HINT" in line and "\\n역할:" in line:
        lines[i] = line.replace("'\\\\n역할:'", "'\\n역할:'")
        print("264번 라인 이스케이프 수정 완료")
        break

output = "".join(lines)
output += """

    def save_entry(self, quiet=False):
        if not getattr(self, '_cache', None):
            return False

        cat = self.catCombo.currentText()
        db = self.w.db
        saved_count = 0

        try:
            for i, (kind, label, row) in enumerate(self._cache):
                if self.nameEdit:
                    row['name'] = self.nameEdit.text().strip()

                if i == self._selected_index:
                    for key, widget in self._field_widgets.items():
                        if isinstance(widget, QSpinBox):
                            row[key] = widget.value() if widget.value() else None
                        elif isinstance(widget, QTextEdit):
                            row[key] = widget.toPlainText()
                        else:
                            row[key] = widget.text()

                if kind == 'char':
                    if not row.get('name'):
                        continue
                    old = row.get('_old_name', row['name'])
                    if old and old != row['name']:
                        db.delete_character(old)
                    db.save_character(row)
                    saved_count += 1
                elif kind == 'world':
                    if not row.get('name'):
                        continue
                    old = row.get('_old_name', row['name'])
                    if old and old != row['name']:
                        db.delete_world(old)
                    db.save_world(row)
                    saved_count += 1
                elif kind == 'fore':
                    code = row.get('code') or row.get('title')
                    if not code:
                        continue
                    old = row.get('_old_code', row.get('code'))
                    if old and old != code:
                        db.delete_foreshadow(old)
                    db.save_foreshadow(row)
                    saved_count += 1
                elif kind == 'major':
                    title = row.get('title')
                    if not title:
                        continue
                    old = row.get('_old_title', row.get('title'))
                    if old and old != title:
                        db.delete_major_event(old)
                    db.save_major_event(row)
                    saved_count += 1
                else:
                    row_id = row.get('id')
                    if not row_id:
                        continue
                    db.execute(
                        'UPDATE timeline_events SET title=?, description=?, chapter_number=?, story_date=?, location=?, participants=? WHERE id=?',
                        (
                            row.get('title', ''),
                            row.get('description', ''),
                            row.get('chapter_number'),
                            row.get('story_date', ''),
                            row.get('location', ''),
                            row.get('participants', ''),
                            row_id,
                        )
                    )
                    saved_count += 1

            self.refresh()

            if not quiet:
                QMessageBox.information(self.w, '저장 완료', f'현재 카테고리의 {saved_count}개 항목을 저장했습니다.')
            return True

        except Exception as e:
            QMessageBox.critical(self.w, '저장 실패', f'설정 DB 저장 중 오류가 발생했습니다.\\n{e}')
            return False
"""
output += """

    def delete_entry(self):
        if not getattr(self, '_cache', None):
            return
        i = self.list.currentRow()
        if not (0 <= i < len(self._cache)):
            return
        kind, label, row = self._cache[i]
        if QMessageBox.question(self.w, '삭제', f'{label} 삭제할까요?') != QMessageBox.StandardButton.Yes:
            return

        db = self.w.db
        if kind == 'char':
            db.delete_character(row['name'])
        elif kind == 'world':
            db.delete_world(row['name'])
        elif kind == 'fore':
            db.delete_foreshadow(row['code'])
        elif kind == 'major':
            db.delete_major_event(row['title'])
        else:
            db.delete_timeline(row['id'])

        self.refresh()

    def _master(self):
        t = self.w.db.get_plan()
        if not t.strip():
            QMessageBox.warning(self.w, '마스터 기획 필요', '먼저 [기획]에서 마스터 기획을 생성하거나 저장하세요.')
            return ''
        return t

    def ai_generate(self):
        cat = self.catCombo.currentText()
        master = self._master()
        if not master:
            return
        total = int(self.w.pm.settings.get('target_chapters', 500) or 500)
        self.w._run(
            f'마스터 기획에서 {cat} 자동 추출/보완 중...',
            lambda: self.w.ai.generate(entity_catalog_prompt(cat, master, total), temperature=.35, max_tokens=12000),
            lambda t: self._store_catalog(cat, t)
        )

    def _store_catalog(self, cat, text):
        items = parse_entity_catalog(text)
        if not items:
            QMessageBox.warning(self.w, 'AI 결과 오류', '마스터 기획에서 설정 항목을 추출하지 못했습니다. AI 응답 형식을 확인하세요.')
            return

        db = self.w.db
        count = 0
        for x in items:
            try:
                if cat == '인물' and x.get('name'):
                    role = x.get('role') or '조연'
                    db.save_character({
                        'name': x['name'],
                        'role': role,
                        'profile': x.get('profile', ''),
                        'personality': x.get('personality', ''),
                        'speech_style': x.get('speech_style', ''),
                        'goal': x.get('goal', ''),
                        'secret': x.get('secret', ''),
                        'arc': x.get('arc', ''),
                    })
                    count += 1
                elif cat in ('세력', '장소') and x.get('name'):
                    db.save_world({
                        'name': x['name'],
                        'category': cat,
                        'description': x.get('description', ''),
                        'rules': x.get('rules', ''),
                    })
                    count += 1
                elif cat == '복선' and (x.get('code') or x.get('title')):
                    code = x.get('code') or f"F{count + 1:03d}"
                    db.save_foreshadow({
                        'code': code,
                        'title': x.get('title') or code,
                        'first_chapter': x.get('first_chapter') or None,
                        'reveal_chapter': x.get('reveal_chapter') or None,
                        'status': x.get('status') or '활성',
                        'public_info': x.get('public_info', ''),
                        'author_truth': x.get('author_truth', ''),
                        'related_characters': x.get('related_characters', ''),
                        'notes': x.get('notes', ''),
                    })
                    count += 1
                elif cat == '핵심 사건' and x.get('title'):
                    db.save_major_event({
                        'title': x['title'],
                        'start_chapter': x.get('start_chapter') or None,
                        'end_chapter': x.get('end_chapter') or None,
                        'description': x.get('description', ''),
                        'consequence': x.get('consequence', ''),
                        'status': x.get('status') or '계획',
                    })
                    count += 1
                elif cat == '시간축' and x.get('title'):
                    db.save_timeline({
                        'chapter_number': x.get('chapter_number') or None,
                        'story_date': x.get('story_date', ''),
                        'title': x['title'],
                        'description': x.get('description', ''),
                        'location': x.get('location', ''),
                        'participants': x.get('participants', ''),
                    })
                    count += 1
            except Exception:
                continue

        self.refresh()
        QMessageBox.information(self.w, 'AI 자동 추가', f'마스터 기획에서 {count}개 항목을 추가/갱신했습니다.')
"""

if not output.strip().endswith("\n"):
    output += "\n"

print("모든 메서드 추가 완료")
