from pathlib import Path
from PySide6.QtWidgets import QDialog,QMessageBox,QFileDialog,QVBoxLayout
from novel_studio.ui.loader import load_ui
from novel_studio.core.project import ProjectManager
from novel_studio.core.app_settings import AppSettings
from novel_studio.db.database import Database
from novel_studio.ui.dialogs import AISettingsDialog

MOOD_BY_GENRE = {
    '선협': '진중하고 어두운 분위기',
    '무협': '의협적이고 거친 분위기',
    '판타지': '경이롭고 모험적인 분위기',
    '로맨스': '따뜻하고 설레는 분위기',
    '현대': '현실적이고 담백한 분위기',
    '스릴러': '긴장감 있고 어두운 분위기',
    '호러': '소름 끼고 불길한 분위기',
    'SF': '미래지적이고 차가운 분위기',
    '역사': '웅장하고 묵직한 분위기',
    '게임': '밝고 역동적인 분위기',
}


class StartupDialog(QDialog):
    def __init__(self):
        super().__init__(); ui=load_ui('startup.ui'); lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.addWidget(ui); self.ui=ui
        for n in ['titleEdit','genreEdit','moodEdit','totalSpin','charSpin','tolSpin','sectionSpin','createBtn','openBtn','settingsBtn','exitBtn']: setattr(self,n,ui.findChild(__import__('PySide6.QtWidgets',fromlist=['QWidget']).QWidget,n))
        self.selected_project=None; self.app_settings=AppSettings(); from novel_studio.ai.provider_manager import ProviderManager; self.providers=ProviderManager(self.app_settings)
        self._last_auto_mood = self.moodEdit.text().strip()
        try:
            self.genreEdit.currentTextChanged.connect(self._auto_mood)
        except Exception:
            pass
        self.createBtn.clicked.connect(self.create); self.openBtn.clicked.connect(self.open_existing); self.settingsBtn.clicked.connect(self.open_settings); self.exitBtn.clicked.connect(self.reject); self.resize(820,650); self.setWindowTitle('Novel Studio - 프로젝트 시작')
    def _auto_mood(self, genre):
        """요청: 장르를 바꾸면 분위기를 장르 기본값으로 자동 채운다. (사용자 수정 값은 유지)"""
        new = MOOD_BY_GENRE.get((genre or '').strip())
        if not new:
            return
        cur = self.moodEdit.text().strip()
        if not cur or cur == self._last_auto_mood:
            self.moodEdit.setText(new)
            self._last_auto_mood = new
    def create(self):
        base=QFileDialog.getExistingDirectory(self,'새 작품 저장 위치 선택')
        if not base:return
        title=self.titleEdit.text().strip() or '새 작품'; root=Path(base)/title
        if root.exists() and (root/'project.json').exists(): QMessageBox.warning(self,'이미 존재','같은 이름의 프로젝트가 이미 있습니다. 다른 작품명을 사용하세요.'); return
        try:
            genre = self.genreEdit.currentText().strip() if hasattr(self.genreEdit, 'currentText') else self.genreEdit.text().strip()
            pm=ProjectManager(); pm.create(root,title,genre or '선협',self.moodEdit.text().strip() or '진중하고 어두운 분위기',self.totalSpin.value(),self.charSpin.value(),self.tolSpin.value(),self.sectionSpin.value()); db=Database(root/'novel.db'); db.ensure_chapters(self.totalSpin.value(),self.charSpin.value()); db.close(); self.selected_project=root; self.accept()
        except Exception as e: QMessageBox.critical(self,'생성 실패',str(e))
    def open_existing(self):
        path=QFileDialog.getExistingDirectory(self,'기존 Novel Studio 프로젝트 선택')
        if not path:return
        if not (Path(path)/'project.json').exists(): QMessageBox.warning(self,'열기 실패','선택한 폴더에 project.json이 없습니다.'); return
        self.selected_project=Path(path); self.accept()
    def open_settings(self): AISettingsDialog(self.providers,self.app_settings,self).exec()
