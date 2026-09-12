from ._base import BaseView
from PySide6.QtWidgets import QListWidget, QPlainTextEdit, QPushButton, QComboBox, QInputDialog, QMessageBox


class EntitiesView(BaseView):
    """설정 DB: 인물/세력/장소/복선/핵심 사건/시간축을 여러 항목으로 관리."""

    CATS = ['인물', '세력', '장소', '복선', '핵심 사건', '시간축']
    ROLE_HINT = '인물 역할 예: 주인공 / 서브주인공 / 조연 / 엑스트라'

    def __init__(self, w):
        super().__init__(w)
        self.mount('entities.ui')
        self.w = w
        self.catCombo = self.ui.findChild(QComboBox, 'catCombo')
        self.catCombo.addItems(self.CATS)
        self.list = self.ui.findChild(QListWidget, 'list')
        self.detail = self.ui.findChild(QPlainTextEdit, 'detail')
        self.addBtn = self.ui.findChild(QPushButton, 'addBtn')
        self.aiBtn = self.ui.findChild(QPushButton, 'aiBtn')
        self.saveBtn = self.ui.findChild(QPushButton, 'saveBtn')
        self.delBtn = self.ui.findChild(QPushButton, 'delBtn')
        self.catCombo.currentTextChanged.connect(self.refresh)
        self.list.currentRowChanged.connect(self.show_selected)
        self.refresh()

    # -- 데이터 접근 -----------------------------------------------------
    def _rows(self):
        db = self.w.db
        cat = self.catCombo.currentText()
        if cat == '인물':
            return [('char', r['name'], r) for r in db.characters()]
        if cat in ('세력', '장소'):
            want = '세력' if cat == '세력' else '장소'
            return [('world', r['name'], r) for r in db.world_entities()
                    if (r['category'] or '') == want or not r['category']]
        if cat == '복선':
            return [('fore', r['code'], r) for r in db.foreshadows()]
        if cat == '핵심 사건':
            return [('major', r['title'], r) for r in db.major_events()]
        return [('time', f"{r['chapter_number'] or '-'}화 {r['title']}", r) for r in db.timeline()]

    def refresh(self):
        self._cache = self._rows()
        self.list.clear()
        for _, label, _ in self._cache:
            self.list.addItem(str(label))
        if self._cache:
            self.list.setCurrentRow(0)
        else:
            self.detail.setPlainText('항목이 없습니다. [+ 추가] 또는 [AI로 추가]를 눌러 만드세요.')

    def show_selected(self, i):
        if not getattr(self, '_cache', None) or not 0 <= i < len(self._cache):
            return
        _, _, row = self._cache[i]
        self.detail.setPlainText(self._fmt(row))

    def _fmt(self, r):
        return '\n'.join(f'{k}: {r[k]}' for k in r.keys() if k not in ('id',))

    # -- 추가 / 저장 / 삭제 -----------------------------------------------
    def add_entry(self):
        cat = self.catCombo.currentText()
        name, ok = QInputDialog.getText(self.w, f'{cat} 추가', '이름/제목을 입력하세요:')
        if not (ok and name.strip()):
            return
        name = name.strip()
        db = self.w.db
        if cat == '인물':
            role, _ = QInputDialog.getText(self.w, '역할', self.ROLE_HINT + '\n역할:')
            db.save_character({'name': name, 'role': role or '조연'})
        elif cat in ('세력', '장소'):
            db.save_world({'name': name, 'category': cat, 'description': '', 'rules': ''})
        elif cat == '복선':
            db.save_foreshadow({'code': name, 'title': name})
        elif cat == '핵심 사건':
            db.save_major_event({'title': name})
        else:
            db.save_timeline({'title': name, 'chapter_number': None})
        self.refresh()

    def save_entry(self):
        # 상세 텍스트를 그대로 파싱하지 않고, 이름 키 기준으로 상태 메모를 notes/profile에 저장
        if not getattr(self, '_cache', None):
            return
        i = self.list.currentRow()
        if not 0 <= i < len(self._cache):
            return
        kind, label, row = self._cache[i]
        text = self.detail.toPlainText()
        db = self.w.db
        if kind == 'char':
            db.save_character({**dict(row), 'profile': text})
        elif kind == 'world':
            db.save_world({**dict(row), 'description': text})
        elif kind == 'fore':
            db.save_foreshadow({**dict(row), 'notes': text})
        elif kind == 'major':
            db.save_major_event({**dict(row), 'description': text})
        else:
            db.execute("UPDATE timeline_events SET description=? WHERE id=?", (text, row['id']))
        QMessageBox.information(self.w, '저장', f'{label} 저장 완료')

    def delete_entry(self):
        if not getattr(self, '_cache', None):
            return
        i = self.list.currentRow()
        if not 0 <= i < len(self._cache):
            return
        kind, label, row = self._cache[i]
        if QMessageBox.question(self.w, '삭제', f'{label} 삭제할까요?') != QMessageBox.StandardButton.Yes:
            return
        db = self.w.db
        if kind == 'char':
            db.delete_character(label)
        elif kind == 'world':
            db.delete_world(label)
        elif kind == 'fore':
            db.delete_foreshadow(label)
        elif kind == 'major':
            db.delete_major_event(label)
        else:
            db.delete_timeline(row['id'])
        self.refresh()

