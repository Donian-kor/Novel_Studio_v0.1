from PySide6.QtWidgets import (QDialog, QMessageBox, QVBoxLayout, QWidget,
                               QFormLayout, QLineEdit, QComboBox, QSpinBox,
                               QPushButton, QLabel, QHBoxLayout, QColorDialog,
                               QFontComboBox, QSlider)
from PySide6.QtCore import Qt
from novel_studio.ui.loader import load_ui
class AISettingsDialog(QDialog):
    def __init__(self,providers,settings,parent=None):
        super().__init__(parent)
        ui=load_ui('ai_settings.ui')
        lay=QVBoxLayout(self)
        lay.setContentsMargins(0,0,0,0)
        lay.addWidget(ui)
        self.ui=ui
        self.pm,self.settings=providers,settings
        for n in ['provider','urlEdit','modelEdit','keyEdit','testBtn','saveBtn','fontEdit','fontSpin','fontSizeValue','textColor','bgColor']:
            setattr(self,n,ui.findChild(QWidget,n))
        self.ids=list(providers.IDS)
        self.provider.addItems([providers.IDS[x] for x in self.ids])
        self._load_editor_controls()
        self.provider.currentIndexChanged.connect(self.load_provider)
        self.load_provider(self.ids.index(settings.data['active_provider']))
        self.testBtn.clicked.connect(self.test)
        self.saveBtn.clicked.connect(self.save)
        self.fontSpin.valueChanged.connect(lambda v: self.fontSizeValue.setText(f'{v} pt'))
        self.textColor.clicked.connect(lambda: self._pick_color(self.textColor))
        self.bgColor.clicked.connect(lambda: self._pick_color(self.bgColor))
        self.resize(780,740)
    def load_provider(self,i):
        if not self.ids:return
        pid=self.ids[i]; c=self.pm.config(pid); self.urlEdit.setText(c.get('base_url','')); self.modelEdit.setText(c.get('model','')); self.keyEdit.setText(c.get('api_key',''))

    def _load_editor_controls(self):
        editor=self.settings.data.get('editor', {})
        family=str(editor.get('font_family','Malgun Gothic'))
        self.fontEdit.setCurrentFont(__import__('PySide6.QtGui', fromlist=['QFont']).QFont(family))
        self.fontSpin.setValue(int(editor.get('font_size',18)))
        self._set_color_button(self.textColor, str(editor.get('text_color','#E8E6E3')))
        self._set_color_button(self.bgColor, str(editor.get('bg_color','#2B2B2B')))
        self.fontSizeValue.setText(f'{self.fontSpin.value()} pt')

    def _set_color_button(self, button, value):
        from PySide6.QtGui import QColor
        c=QColor(value)
        if not c.isValid():
            c=QColor('#E8E6E3' if button is self.textColor else '#2B2B2B')
        button.setText(c.name().upper())
        button.setStyleSheet(f'QPushButton{{background:{c.name()}; color:{"#000000" if c.lightness() > 160 else "#FFFFFF"}; border:1px solid #777; padding:6px 10px;}}')

    def _pick_color(self, button):
        from PySide6.QtGui import QColor
        color=QColor(button.text())
        picked=QColorDialog.getColor(color, self, '색상 선택', QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if picked.isValid():
            self._set_color_button(button, picked)
    def save(self):
        pid=self.ids[self.provider.currentIndex()]
        self.pm.save_provider(pid,self.urlEdit.text().strip(),self.modelEdit.text().strip(),self.keyEdit.text().strip())
        self.pm.set_active(pid)
        self.settings.data['editor'].update({
            'font_family': self.fontEdit.currentFont().family(),
            'font_size': self.fontSpin.value(),
            'text_color': self.textColor.text().strip().upper() or '#E8E6E3',
            'bg_color': self.bgColor.text().strip().upper() or '#2B2B2B'
        })
        self.settings.save()
        self.accept()
    def test(self):
        """연결 테스트: 먼저 테스트하고 성공 시에만 저장한다.

        - 모델란이 비어 있으면 서버의 모델 목록에서 자동 선택해 modelEdit에 채운다
        - quick_test()는 15초 짧은 타임아웃 사용
        - 테스트 실패 시 설정이 저장되지 않음
        """
        try:
            pid = self.ids[self.provider.currentIndex()]
            base_url = self.urlEdit.text().strip()
            model = self.modelEdit.text().strip()
            api_key = self.keyEdit.text().strip()
            # 저장 전에 임시 프로바이더로 테스트
            tmp = self.pm.build_unsaved(pid, base_url, model, api_key)
            tester = getattr(tmp, 'quick_test', None)
            if callable(tester):
                result = tester()
            else:
                result = tmp.test()
            # 자동 감지된 모델이 있으면 입력란에 반영
            detected = (tmp.config.get('model') or '').strip()
            if detected and not model:
                self.modelEdit.setText(detected)
                model = detected
            # 성공 시에만 저장
            self.pm.save_provider(pid, base_url, model, api_key)
            self.pm.set_active(pid)
            shown = f"연결 성공 (모델: {model or '자동'})\n\n{result}" if result else f"연결 성공 (모델: {model or '자동'})"
            QMessageBox.information(self, '연결 테스트', shown)
        except Exception as e:
            QMessageBox.critical(self, '연결 실패', str(e))


class ProjectSettingsDialog(QDialog):
    """요청 1-3: 현재 프로젝트 설정(작품명/장르/분위기/화수/글자수/오차/구간) 편집."""

    def __init__(self, pm, parent=None):
        super().__init__(parent)
        self.pm = pm
        s = pm.settings
        self.setWindowTitle('프로젝트 설정')
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.titleEdit = QLineEdit(str(s.get('title', '')))
        self.genreEdit = QComboBox(); self.genreEdit.setEditable(True)
        from novel_studio.ai.prompts import GENRES
        self.genreEdit.addItems([g for g in GENRES if g != '직접 입력'])
        self.genreEdit.setCurrentText(str(s.get('genre', '') or '선협'))
        self.moodEdit = QLineEdit(str(s.get('mood', '')))
        self.totalSpin = QSpinBox(); self.totalSpin.setRange(1, 5000)
        self.totalSpin.setValue(int(s.get('target_chapters', 500)))
        self.charSpin = QSpinBox(); self.charSpin.setRange(500, 30000)
        self.charSpin.setValue(int(s.get('chapter_chars', 5000)))
        self.tolSpin = QSpinBox(); self.tolSpin.setRange(0, 5000)
        self.tolSpin.setValue(int(s.get('tolerance', 300)))
        self.sectionSpin = QSpinBox(); self.sectionSpin.setRange(1, 50)
        self.sectionSpin.setValue(int(s.get('section_size', 5)))
        form.addRow('작품명', self.titleEdit)
        form.addRow('장르', self.genreEdit)
        form.addRow('분위기', self.moodEdit)
        form.addRow('총 화수', self.totalSpin)
        form.addRow('화당 목표 글자수', self.charSpin)
        form.addRow('허용 오차 (±글자수)', self.tolSpin)
        form.addRow('스토리 구간 크기 (화)', self.sectionSpin)
        lay.addLayout(form)
        help_ = QLabel('허용 오차: AI 집필 시 목표 글자수 ± 범위 (예: 5000±300 → 4700~5300자).\n'
                       '스토리 구간 크기: 한 구간에 묶을 화 수 (예: 5 → 1~5화, 6~10화 …).')
        help_.setWordWrap(True)
        lay.addWidget(help_)
        row = QHBoxLayout()
        save = QPushButton('저장'); save.clicked.connect(self.accept_changes)
        cancel = QPushButton('취소'); cancel.clicked.connect(self.reject)
        row.addWidget(save); row.addWidget(cancel)
        lay.addLayout(row)
        self.resize(500, 470)

    def accept_changes(self):
        vals = {
            'title': self.titleEdit.text().strip() or '새 작품',
            'genre': self.genreEdit.currentText().strip() or '선협',
            'mood': self.moodEdit.text().strip(),
            'target_chapters': self.totalSpin.value(),
            'chapter_chars': self.charSpin.value(),
            'tolerance': self.tolSpin.value(),
            'section_size': self.sectionSpin.value(),
        }
        self.pm.save_settings(vals)
        self.accept()
