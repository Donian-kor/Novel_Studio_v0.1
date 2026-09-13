"""entities.py 수정 스크립트 (1단계)"""
import pathlib

path = pathlib.Path(r"c:/Users/donian/Desktop/python/Novel_Studio/novel_studio/ui/views/entities.py")
content = path.read_text(encoding="utf-8")
lines = content.splitlines(True)

# 264번 라인 이스케이프 수정
for i, line in enumerate(lines):
    if i == 263 and "ROLE_HINT" in line and "\\n역할:" in line:
        lines[i] = line.replace("'\\\\n역할:'", "'\\n역할:'")
        print("264번 라인 이스케이프 수정 완료")
        break

# save_entry 추가
save_entry_code = """

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
lines.append(save_entry_code)
print("save_entry 추가 완료")

path.write_text("".join(lines), encoding="utf-8")
print("엔티티 파일 저장 완료")
