from PySide6.QtWidgets import QDialog,QMessageBox,QVBoxLayout,QWidget
from novel_studio.ui.loader import load_ui
class AISettingsDialog(QDialog):
    def __init__(self,providers,settings,parent=None):
        super().__init__(parent); ui=load_ui('ai_settings.ui'); lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.addWidget(ui); self.ui=ui; self.pm,self.settings=providers,settings
        for n in ['provider','urlEdit','modelEdit','keyEdit','testBtn','saveBtn','fontEdit','fontSpin','textColor','bgColor']: setattr(self,n,ui.findChild(QWidget,n))
        self.ids=list(providers.IDS); self.provider.addItems([providers.IDS[x] for x in self.ids]); self.fontEdit.setText(str(settings.data['editor']['font_family'])); self.fontSpin.setValue(int(settings.data['editor']['font_size'])); self.textColor.setText(settings.data['editor']['text_color']); self.bgColor.setText(settings.data['editor']['bg_color']); self.provider.currentIndexChanged.connect(self.load_provider); self.load_provider(self.ids.index(settings.data['active_provider'])); self.testBtn.clicked.connect(self.test); self.saveBtn.clicked.connect(self.save); self.resize(780,740)
    def load_provider(self,i):
        if not self.ids:return
        pid=self.ids[i]; c=self.pm.config(pid); self.urlEdit.setText(c.get('base_url','')); self.modelEdit.setText(c.get('model','')); self.keyEdit.setText(c.get('api_key',''))
    def save(self):
        pid=self.ids[self.provider.currentIndex()]; self.pm.save_provider(pid,self.urlEdit.text().strip(),self.modelEdit.text().strip(),self.keyEdit.text().strip()); self.pm.set_active(pid); self.settings.data['editor'].update({'font_family':self.fontEdit.text().strip() or 'Malgun Gothic','font_size':self.fontSpin.value(),'text_color':self.textColor.text().strip() or '#E8E6E3','bg_color':self.bgColor.text().strip() or '#2B2B2B'}); self.settings.save(); self.accept()
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
