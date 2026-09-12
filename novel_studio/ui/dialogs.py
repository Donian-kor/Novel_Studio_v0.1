from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox
from novel_studio.ui.loader import load_ui
class NewProjectDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent); self.form=load_ui('new_project.ui',self); self.setLayout(self.form.layout())
        self.title=self.form.titleEdit; self.folder=self.form.folderEdit; self.genre=self.form.genreEdit; self.mood=self.form.moodEdit; self.total=self.form.totalSpin; self.chars=self.form.charsSpin; self.tol=self.form.tolSpin
        self.form.browseButton.clicked.connect(self.browse); self.form.buttonBox.accepted.connect(self.validate_accept); self.form.buttonBox.rejected.connect(self.reject)
    def browse(self):
        p=QFileDialog.getExistingDirectory(self,'프로젝트 저장 폴더');
        if p:self.folder.setText(p)
    def validate_accept(self):
        if not self.title.text().strip() or not self.folder.text().strip(): QMessageBox.warning(self,'입력 필요','작품명과 저장 폴더를 입력하세요.'); return
        self.accept()

class AISettingsDialog(QDialog):
    def __init__(self,project,parent=None):
        super().__init__(parent); self.project=project; self.form=load_ui('ai_settings.ui',self); self.setLayout(self.form.layout())
        s=project.settings
        self.url=self.form.urlEdit; self.model=self.form.modelEdit; self.temp=self.form.tempSpin; self.top=self.form.topSpin; self.max_tokens=self.form.maxTokensSpin
        self.font=self.form.fontEdit; self.font_size=self.form.fontSizeSpin; self.text_color=self.form.textColorEdit; self.bg_color=self.form.bgColorEdit; self.spacing=self.form.spacingSpin
        self.url.setText(s.get('lmstudio_url','http://localhost:1234')); self.model.setText(s.get('model','')); self.temp.setValue(float(s.get('temperature','0.72'))); self.top.setValue(float(s.get('top_p','0.90'))); self.max_tokens.setValue(int(s.get('max_tokens','9000')))
        self.font.setText(s.get('editor_font_family','Malgun Gothic')); self.font_size.setValue(int(s.get('editor_font_size','18'))); self.text_color.setText(s.get('editor_text_color','#222222')); self.bg_color.setText(s.get('editor_bg_color','#FFFDF5')); self.spacing.setValue(float(s.get('editor_line_spacing','1.4')))
        self.form.refreshButton.clicked.connect(self.refresh_models); self.form.testButton.clicked.connect(self.test); self.form.modelsList.itemClicked.connect(lambda item: self.model.setText(item.text())); self.form.buttonBox.accepted.connect(self.save); self.form.buttonBox.rejected.connect(self.reject)
    def refresh_models(self):
        from novel_studio.ai.lmstudio import LMStudioClient
        try:
            ms=LMStudioClient(self.url.text().strip()).list_models(); self.form.modelsList.clear(); self.form.modelsList.addItems([m.get('id','') for m in ms])
        except Exception as e: QMessageBox.warning(self,'연결 실패',str(e))
    def test(self):
        from novel_studio.ai.lmstudio import LMStudioClient
        try:
            ms=LMStudioClient(self.url.text().strip(),self.model.text().strip()).list_models(); QMessageBox.information(self,'연결 성공',f'LM Studio 연결 성공\n모델 {len(ms)}개 확인')
        except Exception as e: QMessageBox.critical(self,'연결 실패',str(e))
    def save(self):
        self.project.save_settings({'lmstudio_url':self.url.text().strip(),'model':self.model.text().strip(),'temperature':str(self.temp.value()),'top_p':str(self.top.value()),'max_tokens':str(self.max_tokens.value()),'editor_font_family':self.font.text().strip(),'editor_font_size':str(self.font_size.value()),'editor_text_color':self.text_color.text().strip(),'editor_bg_color':self.bg_color.text().strip(),'editor_line_spacing':str(self.spacing.value())}); self.accept()
