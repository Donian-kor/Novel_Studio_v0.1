from ._base import BaseView
from PySide6.QtWidgets import (QComboBox, QListWidget, QPlainTextEdit, QPushButton,
                               QLineEdit, QInputDialog, QMessageBox)


class EntitiesView(BaseView):
    """설정 DB 뷰: 카테고리(인물/세력/장소/복선/핵심사건/시간축) + 엔트리 목록 + 상세 편집.

    좌측 카테고리 콤보 → 가운데 엔트리 리스트 → 우측 상세 텍스트.
    기존의 단일 텍스트 설정(section_contents)과 달리, 필요한 만큼
    여러 엔트리를 추가/삭제할 수 있다.
    """

    CATS = ['인물', '세력', '장소', '복선', '핵심 사건', '시간축']

    def __init__(self, w):
        super().__init__(w)
        self.mount('entities.ui')
        self.w = w
        self.catCombo = self.ui.findChild(QComboBox, 'catCombo')
        self.catCombo.addItems(self.CATS)
        self.entryList = self.ui.findChild(QListWidget, 'entryList')
        self.detail = self.ui.findChild(QPlainTextEdit, 'detail')
        self.nameEdit = self.ui.findChild(QLineEdit, 'nameEdit')
        self.generateBtn = self.ui.findChild(QPushButton, 'generateBtn')
        self.addBtn = self.ui.findChild(QPushButton, 'addBtn')
        self.delBtn = self.ui.findChild(QPushButton, 'delBtn')
        self.saveBtn = self.ui.findChild(QPushButton, 'saveBtn')
        self.catCombo.currentTextChanged.connect(self.refresh)
        self.entryList.currentRowChanged.connect(self.show_selected)
        self.addBtn.clicked.connect(self.add_entry)
        self.delBtn.clicked.connect(self.delete_entry)
        self.saveBtn.clicked.connect(self.save_entry)
        self.generateBtn.clicked.connect(self.ai_generate)
        self._rows = []

    # -- 데이터 접근 -------------------------------------------------
    def _load_rows(self, cat):
        db = self.w.db
        if cat == '인물':
            return [('character', r['name'], r) for r in db.characters()]
        if cat == '세력':
            return [('world', r['name'], r)
                    for r in db.world_entities() if (r['category'] or '') == '세력']
        if cat == '장소':
            return [('world', r['name'], r)
                    for r in db.world_entities() if (r['category'] or '') != '세력']
        if cat == '복선':
            return [('foreshadow', r['code'] or r['title'], r) for r in db.foreshadows()]
        if cat == '핵심 사건':
            return [('major', r['title'], r) for r in db.major_events()]
        return [('timeline', r['title'] or f"#{r['id']}", r) for r in db.timeline()]

    @staticmethod
    def _fmt(kind, row):
        try:
            if kind == 'character':
                return (f"[이름] {row['name']}\n[역할] {row['role']}\n"
                        f"[성격] {row['personality']}\n[말투] {row['speech_style']}\n"
                        f"[외형/배경] {row['profile']}\n[목표] {row['goal']}\n"
                        f"[비밀] {row['secret']}\n[성장선] {row['arc']}")
            if kind == 'world':
                return (f"[이름] {row['name']}\n[분류] {row['category']}\n"
                        f"[설명] {row['description']}\n[규칙/특징] {row['rules']}")
            if kind == 'foreshadow':
                return (f"[코드] {row['code']}\n[제목] {row['title']}\n"
                        f"[첫 등장] {row['first_chapter']}화 / [최근] {row['latest_chapter']}화 / "
                        f"[회수 예정] {row['reveal_chapter']}화\n[상태] {row['status']}\n"
                        f"[공개 정보] {row['public_info']}\n"
                        f"[작가 진실] {row['author_truth']}\n"
                        f"[관련 인물] {row['related_characters']}\n[메모] {row['notes']}")
            if kind == 'major':
                return (f"[제목] {row['title']}\n"
                        f"[구간] {row['start_chapter']}~{row['end_chapter']}화\n"
                        f"[내용] {row['description']}\n[결과/여파] {row['consequence']}\n"
                        f"[상태] {row['status']}")
            return (f"[제목] {row['title']}\n[화수] {row['chapter_number']}화 / "
                    f"[날짜] {row['story_date']}\n[장소] {row['location']}\n"
                    f"[참여자] {row['participants']}\n[내용] {row['description']}")
        except Exception:
            return str(dict(row))

    @property
    def category(self):
        return self.catCombo.currentText()

    # -- UI 동작 -----------------------------------------------------
    def refresh(self, _cat=None):
        cat = self.category
        self._rows = self._load_rows(cat)
        self.entryList.clear()
        for _kind, label, _row in self._rows:
            self.entryList.addItem(str(label or '(무제)'))
        self.detail.clear()
        self.nameEdit.clear()

    def selected(self):
        i = self.entryList.currentRow()
        return self._rows[i] if 0 <= i < len(self._rows) else None

    def show_selected(self, _row=-1):
        sel = self.selected()
        if not sel:
            return
        kind, _label, row = sel
        try:
            key = row['name'] if kind in ('character', 'world') else (
                row['code'] if kind == 'foreshadow' else row['title'])
        except Exception:
            key = ''
        self.nameEdit.setText(str(key or ''))
        self.detail.setPlainText(self._fmt(kind, row))

    def current_text(self):
        return self.detail.toPlainText()

    def set_entry_text(self, _key, text):
        self.detail.setPlainText(text)

    # -- CRUD ---------------------------------------------------------
    def add_entry(self):
        cat = self.category
        name, ok = QInputDialog.getText(self.w, f'{cat} 추가', '이름/제목을 입력하세요:')
        if not (ok and name.strip()):
            return
        name = name.strip()
        db = self.w.db
        try:
            if cat == '인물':
                role, ok2 = QInputDialog.getText(self.w, '역할',
                                                 '역할 (주인공/서브주인공/조연/엑스트라):')
                db.save_character({'name': name, 'role': (role or '조연').strip()})
            elif cat in ('세력', '장소'):
                db.save_world({'name': name, 'category': cat})
            elif cat == '복선':
                db.save_foreshadow({'code': name, 'title': name})
            elif cat == '핵심 사건':
                db.save_major_event({'title': name})
            else:
                db.save_timeline({'title': name, 'chapter_number': None})
        except Exception as e:
            QMessageBox.critical(self.w, '추가 실패', str(e))
            return
        self.refresh()

    def delete_entry(self):
        sel = self.selected()
        if not sel:
            return
        kind, label, row = sel
        if QMessageBox.question(self.w, '삭제', f'「{label}」 항목을 삭제할까요?') \
                != QMessageBox.StandardButton.Yes:
            return
        db = self.w.db
        try:
            if kind == 'character':
                db.delete_character(row['name'])
            elif kind == 'world':
                db.delete_world(row['name'])
            elif kind == 'foreshadow':
                db.delete_foreshadow(row['code'] or row['title'])
            elif kind == 'major':
                db.delete_major_event(row['title'])
            else:
                db.delete_timeline(row['id'])
        except Exception as e:
            QMessageBox.critical(self.w, '삭제 실패', str(e))
            return
        self.refresh()

    def save_entry(self):
        sel = self.selected()
        if not sel:
            QMessageBox.information(self.w, '저장', '목록에서 항목을 먼저 선택하세요.')
            return
        kind, label, row = sel
        text = self.detail.toPlainText()
        name = self.nameEdit.text().strip() or label
        db = self.w.db
        d = dict(row)
        try:
            if kind == 'character':
                d.update({'name': name, 'profile': text})
                db.save_character(d)
            elif kind == 'world':
                d.update({'name': name, 'description': text})
                db.save_world(d)
            elif kind == 'foreshadow':
                d.update({'code': name, 'notes': text})
                db.save_foreshadow(d)
            elif kind == 'major':
                d.update({'title': name, 'description': text})
                db.save_major_event(d)
            else:
                db.execute("UPDATE timeline_events SET title=?, description=? WHERE id=?",
                           (name, text, row['id']))
        except Exception as e:
            QMessageBox.critical(self.w, '저장 실패', str(e))
            return
        QMessageBox.information(self.w, '저장', '저장 완료')
        self.refresh()

    # -- AI 생성/보완 --------------------------------------------------
    def ai_generate(self):
        cat = self.category
        name = self.nameEdit.text().strip()
        if not name:
            QMessageBox.information(self.w, '이름 필요',
                                    '이름/제목을 입력한 뒤 [AI로 생성/보완]을 누르세요.')
            return
        from novel_studio.ai.prompts import entity_extra
        ctx = self._context()
        self.w._run(f'{cat}「{name}」 AI 생성/보완 중...',
                    lambda: self.w.ai.generate(entity_extra(cat, name, ctx),
                                               temperature=.4, max_tokens=12000),
                    lambda t: self._store_generated(cat, name, t))

    def _context(self):
        parts = []
        idea = self.w.db.get_meta('idea', '')
        if idea:
            parts.append('[아이디어]\n' + idea)
        plan = self.w.db.get_plan()
        if plan:
            parts.append('[마스터 기획]\n' + plan)
        parts.append(self._existing_summary())
        return '\n\n'.join(parts)[:6000]

    def _existing_summary(self):
        db = self.w.db
        out = []
        chars = db.characters()
        if chars:
            out.append('[기존 인물]\n' + '\n'.join(f"- {c['name']}: {c['role']}" for c in chars[:20]))
        worlds = db.world_entities()
        if worlds:
            out.append('[기존 세력/장소]\n' + '\n'.join(
                f"- {x['name']} ({x['category']})" for x in worlds[:20]))
        events = db.major_events()
        if events:
            out.append('[기존 핵심 사건]\n' + '\n'.join(f"- {x['title']}" for x in events[:20]))
        return '\n'.join(out)

    def _store_generated(self, cat, name, content):
        db = self.w.db
        try:
            if cat == '인물':
                db.save_character({'name': name, 'role': '조연', 'profile': content})
            elif cat in ('세력', '장소'):
                db.save_world({'name': name, 'category': cat, 'description': content})
            elif cat == '복선':
                db.save_foreshadow({'code': name, 'title': name, 'notes': content})
            elif cat == '핵심 사건':
                db.save_major_event({'title': name, 'description': content})
            else:
                db.save_timeline({'title': name, 'description': content, 'chapter_number': None})
        except Exception as e:
            QMessageBox.critical(self.w, '저장 실패', str(e))
            return
        QMessageBox.information(self.w, 'AI 생성', f'「{name}」 저장 완료')
        self.refresh()
