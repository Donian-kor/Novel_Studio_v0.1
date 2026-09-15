from PySide6.QtWidgets import (QDialog, QMessageBox, QVBoxLayout, QWidget,
                               QFormLayout, QLineEdit, QComboBox, QSpinBox,
                               QPushButton, QLabel, QHBoxLayout, QColorDialog,
                               QFontComboBox, QSlider)
from PySide6.QtCore import Qt, QThread, Signal
from pathlib import Path
from novel_studio.ui.loader import load_ui
# 조회 중인 모델 목록 스레드 참조. 다이얼로그가 먼저 닫혀 GC돼도
# 실행 중인 QThread가 파괴되지 않도록 모듈 레벨에서 유지한다.
_RUNNING_MODEL_THREADS=[]
# 연결 테스트 스레드 참조 (위와 동일한 목적)
_RUNNING_TEST_THREADS=[]

class _ModelListThread(QThread):
    """모델 목록을 백그라운드에서 조회한다 (설정창 오픈 블로킹 방지).

    AI 서버가 꺼져 있으면 list_models()가 접속 대기/타임아웃으로 수 초 걸린다.
    UI 스레드에서 직접 호출하면 설정창이 그 시간만큼 늦게 열리므로,
    조회만 스레드로 돌리고 결과는 시그널로 돌려받는다.
    """
    got_models = Signal(int, list)  # (요청 세대, 모델 목록)

    def __init__(self,pm,pid,cfg,gen,parent=None):
        super().__init__(parent)
        self._pm,self._pid,self._cfg,self._gen=pm,pid,cfg,gen

    def run(self):
        models=[]
        try:
            models=self._pm._build(self._pid,self._cfg).list_models()
        except Exception:
            pass  # 서버 꺼짐 등 조회 실패 → 빈 목록 (편집 가능한 콤보 유지)
        self.got_models.emit(self._gen,models or [])

class _TestThread(QThread):
    """연결 테스트를 백그라운드에서 수행한다 (연결 테스트 클릭 시 UI 프리즈 방지).

    quick_test()는 서버의 실제 응답(텍스트 생성)까지 기다린다. LM Studio가
    꺼져 있으면 접속 실패 판정에도 수 초가 걸리고, 켜져 있어도 응답 생성
    시간만큼 대기하므로 UI 스레드에서 직접 호출하면 설정창이 그 시간만큼
    멈춘다. 테스트만 스레드로 돌리고 결과는 시그널로 돌려받는다.
    """
    done = Signal(object, str, str)  # (프로바이더 객체, 결과 문자열, 오류 메시지)

    def __init__(self,pm,pid,base_url,model,api_key,parent=None):
        super().__init__(parent)
        self._pm,self._pid,self._base,self._model,self._key=pm,pid,base_url,model,api_key

    def run(self):
        p=None
        try:
            p=self._pm.build_unsaved(self._pid,self._base,self._model,self._key)
            tester=getattr(p,'quick_test',None)
            result=tester() if callable(tester) else p.test()
            self.done.emit(p,str(result or ''),'')
        except Exception as e:
            self.done.emit(p,'',str(e))

class AISettingsDialog(QDialog):
    def __init__(self,providers,settings,parent=None):
        super().__init__(parent)
        ui=load_ui('ai_settings.ui')
        lay=QVBoxLayout(self)
        lay.setContentsMargins(0,0,0,0)
        lay.addWidget(ui)
        self.ui=ui
        self.pm,self.settings=providers,settings
        for n in ['provider','urlEdit','modelEdit','keyEdit','testBtn','saveBtn','fontEdit','fontSpin','fontSizeValue','textColor','bgColor','endStateCheck','connStatus']:
            setattr(self,n,ui.findChild(QWidget,n))
        self._apply_end_state_check_style()
        self._set_conn_status(False)
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
        t=ui.windowTitle()
        if t:self.setWindowTitle(t)
    def load_provider(self,i):
        if not self.ids:return
        pid=self.ids[i]; c=self.pm.config(pid)
        self.urlEdit.setText(c.get('base_url',''))
        self.keyEdit.setText(c.get('api_key',''))
        self._set_conn_status(False)  # 프로바이더 전환 시 연결 상태 초기화
        # 모델 목록 조회는 네트워크 I/O라서 UI 스레드에서 직접 하면 창이
        # 수 초간 멈춘다 (예: LM Studio 꺼짐 → 접속 대기). 저장된 모델만
        # 즉시 채우고, 목록은 백그라운드 스레드로 조회해 도착 시 반영한다.
        self._model_gen=getattr(self,'_model_gen',0)+1
        gen=self._model_gen
        self.modelEdit.clear()
        self.modelEdit.setEditText((c.get('model') or '').strip())
        threads=getattr(self,'_model_threads',None)
        if threads is None:
            threads=self._model_threads=[]
        t=_ModelListThread(self.pm,pid,c,gen)

        def _cleanup():
            if t in threads: threads.remove(t)
            if t in _RUNNING_MODEL_THREADS: _RUNNING_MODEL_THREADS.remove(t)
            t.deleteLater()
        t.got_models.connect(self._apply_models)
        t.finished.connect(_cleanup)
        threads.append(t)
        _RUNNING_MODEL_THREADS.append(t)
        t.start()

    def _apply_models(self,gen,models):
        if gen!=getattr(self,'_model_gen',0):
            return  # 프로바이더를 바꾼 뒤 늦게 도착한 이전 조회 결과는 무시
        current=self.modelEdit.currentText().strip()
        self.modelEdit.clear()
        if models:
            self.modelEdit.addItems(models)
        if current:
            idx=self.modelEdit.findText(current)
            if idx>=0:
                self.modelEdit.setCurrentIndex(idx)
            else:
                self.modelEdit.setEditText(current)
        # 서버에서 실제로 모델 목록을 받아왔으면 연결된 것으로 본다
        self._set_conn_status(bool(models))

    def _set_conn_status(self,state) -> None:
        """연결 상태 표기와 모델 목록 활성화를 함께 제어한다.

        True  → 연결됨(녹색), 모델 목록 활성화
        False → 연결 안 됨(회색), 모델 목록 비활성화
        'fail'→ 연결 실패(빨강), 모델 목록 비활성화
        """
        if state is True:
            text,color='연결됨','#27AE60'
        elif state is False:
            text,color='연결 안 됨','#8A8783'
        else:
            text,color='연결 실패','#E74C3C'
        self.connStatus.setText(text)
        self.connStatus.setStyleSheet(f'QLabel#connStatus {{ color: {color}; font-weight: 600; }}')
        self.modelEdit.setEnabled(state is True)

    def _apply_end_state_check_style(self) -> None:
        """종료 상태 체크박스를 녹색 배경 + 흰색 V(체크)로 강조한다.

        QSS의 ``image: url(...)``은 실행 시점 작업 디렉터리 기준으로 해석되므로,
        .ui에 상대 경로를 넣으면 환경에 따라 그림이 사라질 수 있다.
        그래서 이미지 경로만 절대 경로로 보정해 코드에서 적용한다.
        """
        svg=(Path(__file__).resolve().parent/'forms'/'check_mark.svg').as_posix()
        self.endStateCheck.setStyleSheet(
            'QCheckBox#endStateCheck::indicator {'
            ' width: 24px; height: 24px;'
            ' border: 2px solid #5E5B57; border-radius: 5px;'
            ' background: #2B2B2B; }'
            'QCheckBox#endStateCheck::indicator:hover { border-color: #7A7672; }'
            f'QCheckBox#endStateCheck::indicator:checked {{'
            f' background: #27AE60; border: 2px solid #1E8449; image: url("{svg}"); }}'
            'QCheckBox#endStateCheck:checked { color: #27AE60; font-weight: 600; }'
        )

    def _load_editor_controls(self):
        editor=self.settings.data.get('editor', {})
        family=str(editor.get('font_family','Malgun Gothic'))
        self.fontEdit.setCurrentFont(__import__('PySide6.QtGui', fromlist=['QFont']).QFont(family))
        self.fontSpin.setValue(int(editor.get('font_size',18)))
        self._set_color_button(self.textColor, str(editor.get('text_color','#E8E6E3')))
        self._set_color_button(self.bgColor, str(editor.get('bg_color','#2B2B2B')))
        self.fontSizeValue.setText(f'{self.fontSpin.value()} pt')
        self.endStateCheck.setChecked(bool(editor.get('auto_generate_end_state', False)))

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
        self.pm.save_provider(pid,self.urlEdit.text().strip(),self.modelEdit.currentText().strip(),self.keyEdit.text().strip())
        self.pm.set_active(pid)
        self.settings.data['editor'].update({
            'font_family': self.fontEdit.currentFont().family(),
            'font_size': self.fontSpin.value(),
            'text_color': self.textColor.text().strip().upper() or '#E8E6E3',
            'bg_color': self.bgColor.text().strip().upper() or '#2B2B2B',
            'auto_generate_end_state': self.endStateCheck.isChecked()
        })
        self.settings.save()
        self.accept()
    def test(self):
        """연결 테스트: 먼저 테스트하고 성공 시에만 저장한다 (논블로킹).

        - 테스트는 네트워크 I/O(서버 응답 생성 대기)라서 UI 스레드에서 직접
          실행하면 창이 수 초간 멈춘다 → 백그라운드 스레드로 실행
        - 대기 중에는 버튼이 '테스트 중...'으로 바뀌고 비활성화됨 (중복 클릭 방지)
        - 모델란이 비어 있으면 서버의 모델 목록에서 자동 선택해 modelEdit에 채운다
        - 테스트 실패 시 설정이 저장되지 않음
        """
        if getattr(self, '_test_running', False):
            return  # 이미 테스트 진행 중이면 중복 실행하지 않는다
        pid = self.ids[self.provider.currentIndex()]
        base_url = self.urlEdit.text().strip()
        model = self.modelEdit.currentText().strip()
        api_key = self.keyEdit.text().strip()
        self._test_running = True
        self.testBtn.setEnabled(False)
        self.testBtn.setText('테스트 중...')
        threads = getattr(self, '_test_threads', None)
        if threads is None:
            threads = self._test_threads = []
        t = _TestThread(self.pm, pid, base_url, model, api_key)
        threads.append(t)
        _RUNNING_TEST_THREADS.append(t)

        def _done(p, result, error):
            nonlocal model  # 자동 감지 모델 반영 시 재할당
            if t in threads:
                threads.remove(t)
            if t in _RUNNING_TEST_THREADS:
                _RUNNING_TEST_THREADS.remove(t)
            t.deleteLater()
            self._test_running = False
            if not self.isVisible():
                return  # 창이 닫힌 뒤 도착한 결과는 조용히 정리만 한다
            self.testBtn.setEnabled(True)
            self.testBtn.setText('연결 테스트')
            if error:
                self._set_conn_status('fail')
                QMessageBox.critical(self, '연결 실패', error)
                return
            # 자동 감지된 모델이 있으면 입력란에 반영
            detected = (p.config.get('model') or '').strip() if p else ''
            if detected and not model:
                self.modelEdit.setEditText(detected)
                model = detected
            # 성공 시에만 저장
            self.pm.save_provider(pid, base_url, model, api_key)
            self.pm.set_active(pid)
            self._set_conn_status(True)
            shown = f"연결 성공 (모델: {model or '자동'})\n\n{result}" if result else f"연결 성공 (모델: {model or '자동'})"
            QMessageBox.information(self, '연결 테스트', shown)
        t.done.connect(_done)
        t.start()


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
        self.longStorySpin = QSpinBox(); self.longStorySpin.setRange(1, 500)
        self.longStorySpin.setValue(int(s.get('long_story_size', 50)))
        self.subStorySpin = QSpinBox(); self.subStorySpin.setRange(1, 100)
        self.subStorySpin.setValue(int(s.get('sub_story_size', 10)))
        form.addRow('작품명', self.titleEdit)
        form.addRow('장르', self.genreEdit)
        form.addRow('분위기', self.moodEdit)
        form.addRow('총 화수', self.totalSpin)
        form.addRow('화당 목표 글자수', self.charSpin)
        form.addRow('허용 오차 (±글자수)', self.tolSpin)
        form.addRow('장기 스토리 구간 크기 (화)', self.longStorySpin)
        form.addRow('세부 스토리 구간 크기 (화)', self.subStorySpin)
        lay.addLayout(form)
        help_ = QLabel('허용 오차: AI 집필 시 목표 글자수 ± 범위 (예: 5000±300 → 4700~5300자).\n'
                       '장기 구간과 세부 구간은 스토리 화면의 계층 크기입니다. 예: 장기 50화 + 세부 10화 → 1~50화 안에 1~10화, 11~20화 …로 구성됩니다.')
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
            'section_size': self.subStorySpin.value(),
            'long_story_size': self.longStorySpin.value(),
            'sub_story_size': self.subStorySpin.value(),
        }
        self.pm.save_settings(vals)
        self.accept()
