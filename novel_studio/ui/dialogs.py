from __future__ import annotations
from pathlib import Path
from PySide6.QtWidgets import QDialog,QFormLayout,QLineEdit,QSpinBox,QPushButton,QHBoxLayout,QFileDialog,QComboBox,QVBoxLayout,QLabel

class NewProjectDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent); self.setWindowTitle('새 작품'); self.setMinimumWidth(430)
        f=QFormLayout(); self.folder=QLineEdit(str(Path.cwd()/'NovelProject')); b=QPushButton('찾기'); b.clicked.connect(self.browse); row=QHBoxLayout(); row.addWidget(self.folder); row.addWidget(b); f.addRow('프로젝트 폴더',row)
        self.title=QLineEdit('새 소설'); self.genre=QLineEdit('선협'); self.total=QSpinBox(); self.total.setRange(1,5000); self.total.setValue(500); self.chars=QSpinBox(); self.chars.setRange(500,50000); self.chars.setValue(5000); self.tol=QSpinBox(); self.tol.setRange(0,5000); self.tol.setValue(300)
        f.addRow('작품명',self.title); f.addRow('장르',self.genre); f.addRow('총 화수',self.total); f.addRow('화당 목표 글자 수',self.chars); f.addRow('허용 오차',self.tol)
        ok=QPushButton('생성'); ok.clicked.connect(self.accept); f.addRow(ok); self.setLayout(f)
    def browse(self):
        d=QFileDialog.getExistingDirectory(self,'프로젝트 폴더');
        if d: self.folder.setText(d)

class AISettingsDialog(QDialog):
    def __init__(self,settings,parent=None):
        super().__init__(parent); self.setWindowTitle('AI 설정 - LM Studio'); self.setMinimumWidth(520)
        f=QFormLayout(); self.url=QLineEdit(settings.get('lmstudio_url','http://localhost:1234')); self.model=QComboBox(); self.model.setEditable(True); self.model.addItem(settings.get('model',''))
        refresh=QPushButton('모델 목록 새로고침'); test=QPushButton('연결 테스트'); r=QHBoxLayout(); r.addWidget(self.model); r.addWidget(refresh); r.addWidget(test); f.addRow('LM Studio 주소 / 모델',self.url); f.addRow('',r)
        self.temp=QLineEdit(settings.get('temperature','0.72')); self.top_p=QLineEdit(settings.get('top_p','0.9')); self.max_tokens=QSpinBox(); self.max_tokens.setRange(256,50000); self.max_tokens.setValue(int(settings.get('max_tokens','7000')))
        f.addRow('Temperature',self.temp); f.addRow('Top P',self.top_p); f.addRow('최대 출력 토큰',self.max_tokens)
        self.status=QLabel('연결 테스트 전'); f.addRow('상태',self.status)
        save=QPushButton('저장'); save.clicked.connect(self.accept); f.addRow(save); self.setLayout(f)
        refresh.clicked.connect(self.refresh_models); test.clicked.connect(self.test_connection)
    def refresh_models(self):
        from novel_studio.ai.lmstudio import LMStudioClient
        try:
            models=LMStudioClient(self.url.text().strip()).list_models(); self.model.clear(); [self.model.addItem(m.get('id','')) for m in models]; self.status.setText(f'{len(models)}개 모델');
        except Exception as e: self.status.setText(f'실패: {e}')
    def test_connection(self):
        try:
            from novel_studio.ai.lmstudio import LMStudioClient
            models=LMStudioClient(self.url.text().strip(),self.model.currentText().strip()).list_models(); self.status.setText('연결됨: '+(models[0].get('id','') if models else '모델 없음'))
        except Exception as e: self.status.setText(f'연결 실패: {e}')
    def values(self): return {'lmstudio_url':self.url.text().strip(),'model':self.model.currentText().strip(),'temperature':self.temp.text().strip(),'top_p':self.top_p.text().strip(),'max_tokens':str(self.max_tokens.value())}
