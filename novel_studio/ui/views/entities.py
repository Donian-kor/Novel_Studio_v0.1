from ._base import BaseView
from PySide6.QtWidgets import (
    QListWidget, QPushButton, QComboBox, QInputDialog, QMessageBox,
    QSplitter, QLineEdit, QTextEdit, QStackedWidget, QSpinBox, QWidget
)
from PySide6.QtCore import Qt, QSettings
from novel_studio.ai.prompts import entity_catalog_prompt
from novel_studio.utils.entity_parser import parse_entity_catalog


class EntitiesView(BaseView):
    CATS = ['인물', '세력', '장소', '복선', '핵심 사건', '시간축']
    ROLE_HINT = '인물 역할 예: 남주 / 여주 / 조연 / 엑스트라'

    PAGES = {
        '인물': 'characterPage',
        '세력': 'factionPage',
        '장소': 'locationPage',
        '복선': 'foreshadowPage',
        '핵심 사건': 'majorEventPage',
        '시간축': 'timelinePage',
    }

    FIELD_WIDGETS = {
        '인물': [
            ('name', 'characterNameEdit'),
            ('role', 'characterRoleEdit'),
            ('profile', 'characterProfileEdit'),
            ('personality', 'characterPersonalityEdit'),
            ('speech_style', 'characterSpeechStyleEdit'),
            ('goal', 'characterGoalEdit'),
            ('secret', 'characterSecretEdit'),
            ('arc', 'characterArcEdit'),
        ],
        '세력': [
            ('name', 'factionNameEdit'),
            ('category', 'factionCategoryEdit'),
            ('description', 'factionDescriptionEdit'),
            ('rules', 'factionRulesEdit'),
        ],
        '장소': [
            ('name', 'locationNameEdit'),
            ('category', 'locationCategoryEdit'),
            ('description', 'locationDescriptionEdit'),
            ('rules', 'locationRulesEdit'),
        ],
        '복선': [
            ('code', 'foreshadowCodeEdit'),
            ('title', 'foreshadowTitleEdit'),
            ('first_chapter', 'foreshadowFirstChapterSpin'),
            ('reveal_chapter', 'foreshadowRevealChapterSpin'),
            ('status', 'foreshadowStatusEdit'),
            ('public_info', 'foreshadowPublicInfoEdit'),
            ('author_truth', 'foreshadowAuthorTruthEdit'),
            ('related_characters', 'foreshadowRelatedCharactersEdit'),
            ('notes', 'foreshadowNotesEdit'),
        ],
        '핵심 사건': [
            ('title', 'majorTitleEdit'),
            ('start_chapter', 'majorStartChapterSpin'),
            ('end_chapter', 'majorEndChapterSpin'),
            ('description', 'majorDescriptionEdit'),
            ('consequence', 'majorConsequenceEdit'),
            ('status', 'majorStatusEdit'),
        ],
        '시간축': [
            ('chapter_number', 'timelineChapterSpin'),
            ('story_date', 'timelineStoryDateEdit'),
            ('title', 'timelineTitleEdit'),
            ('description', 'timelineDescriptionEdit'),
            ('location', 'timelineLocationEdit'),
            ('participants', 'timelineParticipantsEdit'),
        ],
    }

    def __init__(self, w):
        super().__init__(w)
        self.mount('entities.ui')
        self.w = w

        self.catCombo = self.ui.findChild(QComboBox, 'catCombo')
        self.catCombo.addItems(self.CATS)
        self.list = self.ui.findChild(QListWidget, 'entryList')
        self.nameEdit = self.ui.findChild(QLineEdit, 'nameEdit')
        self.addBtn = self.ui.findChild(QPushButton, 'addBtn')
        self.aiBtn = self.ui.findChild(QPushButton, 'generateBtn')
        self.saveBtn = self.ui.findChild(QPushButton, 'saveBtn')
        self.delBtn = self.ui.findChild(QPushButton, 'delBtn')
        self.formStack = self.ui.findChild(QStackedWidget, 'formStack')

        right = self.ui.findChild(QWidget, 'entitiesRight')
        self._install_splitter('entitiesSplitter', self.list, right or self.formStack, sizes=(360, 900))

        self.catCombo.currentTextChanged.connect(self._on_cat_changed)
        self.list.currentRowChanged.connect(self._on_selection_changed)
        self.addBtn.clicked.connect(self.add_entry)
        self.aiBtn.clicked.connect(self.ai_generate)
        self.saveBtn.clicked.connect(self.save_entry)
        self.delBtn.clicked.connect(self.delete_entry)

        self._cache = []
        self._field_widgets = {}
        self._selected_index = -1

        self._connect_field_signals()
        self._on_cat_changed(self.catCombo.currentText())

    def _install_splitter(self, name, left, right, sizes=(360, 900)):
        split = self.ui.findChild(QSplitter, name)
        if split is None:
            return
        split.setOrientation(Qt.Horizontal)
        split.setChildrenCollapsible(False)
        split.setHandleWidth(9)
        split.setStyleSheet('QSplitter::handle { background: #6a6a6a; } QSplitter::handle:hover { background: #9a9a9a; }')
        saved = QSettings('NovelStudio', 'NovelStudio').value(name + 'Sizes', None)
        if saved:
            try:
                split.setSizes([int(x) for x in saved])
            except Exception:
                split.setSizes(list(sizes))
        else:
            split.setSizes(list(sizes))
        split.splitterMoved.connect(
            lambda pos, index, n=name, sp=split:
            QSettings('NovelStudio', 'NovelStudio').setValue(n + 'Sizes', sp.sizes())
        )
        for w in (left, right):
            if w is not None:
                w.setMinimumWidth(120)
        self.splitter = split

    def _connect_field_signals(self):
        for _fields in self.FIELD_WIDGETS.values():
            for _key, object_name in _fields:
                widget = self.ui.findChild(QWidget, object_name)
                if widget is None:
                    continue
                if isinstance(widget, QTextEdit):
                    widget.textChanged.connect(self._on_field_changed)
                elif isinstance(widget, QSpinBox):
                    widget.valueChanged.connect(self._on_field_changed_int)
                else:
                    widget.textEdited.connect(self._on_field_changed)

    def _widgets_for_category(self, cat):
        widgets = {}
        for key, object_name in self.FIELD_WIDGETS.get(cat, []):
            widget = self.ui.findChild(QWidget, object_name)
            if widget is None:
                continue
            widget.setAccessibleName(key)
            widgets[key] = widget
        return widgets

    def _on_cat_changed(self, cat):
        self._cache = self._rows(cat)
        self.list.blockSignals(True)
        self.list.clear()
        for _, label, _ in self._cache:
            self.list.addItem(str(label))
        self.list.blockSignals(False)

        self._field_widgets = self._widgets_for_category(cat)
        page_name = self.PAGES.get(cat)
        if self.formStack is not None and page_name:
            page = self.ui.findChild(QWidget, page_name)
            if page is not None:
                self.formStack.setCurrentWidget(page)

        self._clear_form_values()
        if self.nameEdit:
            self.nameEdit.clear()

        self._selected_index = -1
        if self._cache:
            self.list.setCurrentRow(0)

    def _set_widget_value(self, widget, value):
        if widget is None:
            return
        blocked = widget.blockSignals(True)
        try:
            if isinstance(widget, QSpinBox):
                try:
                    widget.setValue(int(value) if value not in (None, '', 0) else 0)
                except (ValueError, TypeError):
                    widget.setValue(0)
            elif isinstance(widget, QTextEdit):
                widget.setPlainText(value or '')
            else:
                widget.setText(value or '')
        finally:
            widget.blockSignals(blocked)

    def _on_field_changed(self, value=None):
        w = self.sender()
        if w is None:
            return
        if value is None:
            if isinstance(w, QTextEdit):
                value = w.toPlainText()
            else:
                value = w.text()
        self._update_row_from_widget(w, value)

    def _on_field_changed_int(self, value):
        self._update_row_from_widget(self.sender(), value if value else None)

    def _update_row_from_widget(self, widget, value):
        if self._selected_index < 0 or self._selected_index >= len(self._cache):
            return
        _, _, row = self._cache[self._selected_index]
        field = widget.accessibleName() if widget else None
        if not field:
            return
        row[field] = value if value != '' else (None if isinstance(value, int) else '')

    def _on_selection_changed(self, i):
        self._selected_index = i
        if not self._cache or not (0 <= i < len(self._cache)):
            self._clear_form_values()
            if self.nameEdit:
                self.nameEdit.clear()
            return
        _, label, row = self._cache[i]
        if self.nameEdit:
            self.nameEdit.setText(self._display_name(row))
        self._fill_form(row)

    def _fill_form(self, row):
        for key, widget in self._field_widgets.items():
            self._set_widget_value(widget, row.get(key))

    def _clear_form_values(self):
        for widget in self._field_widgets.values():
            if isinstance(widget, QSpinBox):
                self._set_widget_value(widget, 0)
            elif isinstance(widget, QTextEdit):
                self._set_widget_value(widget, '')
            else:
                self._set_widget_value(widget, '')

    def _rows(self, cat):
        db = self.w.db
        if cat == '인물':
            return [('char', r['name'], {**dict(r), '_old_name': r['name']}) for r in db.characters()]
        if cat in ('세력', '장소'):
            return [('world', r['name'], {**dict(r), '_old_name': r['name']}) for r in db.world_entities(category=cat)]
        if cat == '복선':
            return [('fore', r['code'] or r['title'], {**dict(r), '_old_code': r['code']}) for r in db.foreshadows()]
        if cat == '핵심 사건':
            return [('major', r['title'], {**dict(r), '_old_title': r['title']}) for r in db.major_events()]
        return [('time', f"{r['chapter_number'] or '-'}화 {r['title']}", dict(r)) for r in db.timeline()]

    def _display_name(self, row):
        cat = self.catCombo.currentText()
        if cat == '복선':
            return row.get('code') or row.get('title') or ''
        if cat == '시간축':
            return row.get('title') or ''
        return row.get('name') or row.get('title') or ''

    def refresh(self):
        self._on_cat_changed(self.catCombo.currentText())

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
            db.save_world({'name': name, 'category': cat})
        elif cat == '복선':
            db.save_foreshadow({'code': name, 'title': name})
        elif cat == '핵심 사건':
            db.save_major_event({'title': name})
        else:
            db.save_timeline({'title': name, 'chapter_number': None})

        self.refresh()

    def save_entry(self, quiet=False):
        if not getattr(self, '_cache', None):
            return False

        if not (0 <= self._selected_index < len(self._cache)):
            return False

        cat = self.catCombo.currentText()
        db = self.w.db
        kind, label, row = self._cache[self._selected_index]

        try:
            if self.nameEdit and kind in ('char', 'world'):
                row['name'] = self.nameEdit.text().strip()
            for key, widget in self._field_widgets.items():
                if isinstance(widget, QSpinBox):
                    row[key] = widget.value() if widget.value() else None
                elif isinstance(widget, QTextEdit):
                    row[key] = widget.toPlainText()
                else:
                    row[key] = widget.text()

            if kind == 'char':
                if not row.get('name'):
                    return False
                old = row.get('_old_name', row['name'])
                if old and old != row['name']:
                    db.delete_character(old)
                db.save_character(row)
                saved_label = row['name']
            elif kind == 'world':
                if not row.get('name'):
                    return False
                old = row.get('_old_name', row['name'])
                if old and old != row['name']:
                    db.delete_world(old)
                db.save_world(row)
                saved_label = row['name']
            elif kind == 'fore':
                code = row.get('code') or row.get('title')
                if not code:
                    return False
                old = row.get('_old_code') or code
                if old and old != code:
                    db.delete_foreshadow(old)
                db.save_foreshadow(row)
                saved_label = code
            elif kind == 'major':
                title = row.get('title')
                if not title:
                    return False
                old = row.get('_old_title') or title
                if old and old != title:
                    db.delete_major_event(old)
                db.save_major_event(row)
                saved_label = title
            else:
                row_id = row.get('id')
                if not row_id:
                    return False
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
                saved_label = row.get('title', '')

            self.refresh()
            if not quiet:
                QMessageBox.information(self.w, '저장 완료', f'[{cat}] {saved_label} 항목을 저장했습니다.')
            return True

        except Exception as e:
            QMessageBox.critical(self.w, '저장 실패', f'설정 DB 저장 중 오류가 발생했습니다.\n{e}')
            return False

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
        total = int(self.w.pm.settings['target_chapters'])
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
