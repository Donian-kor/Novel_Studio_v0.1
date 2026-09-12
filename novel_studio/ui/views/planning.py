from ._base import BaseView
from PySide6.QtWidgets import QPlainTextEdit,QPushButton
class PlanningView(BaseView):
    def __init__(self,w):
        super().__init__(w); self.mount('planning.ui'); self.w=w
        self.ideaEdit=self.ui.findChild(QPlainTextEdit,'ideaEdit')
        self.generateBtn=self.ui.findChild(QPushButton,'generateBtn')
        self.useBtn=self.ui.findChild(QPushButton,'useBtn')
        self.masterEdit=self.ui.findChild(QPlainTextEdit,'masterEdit'); self.contractEdit=self.ui.findChild(QPlainTextEdit,'contractEdit'); self.masterPlotEdit=self.ui.findChild(QPlainTextEdit,'masterPlotEdit'); self.saveMasterBtn=self.ui.findChild(__import__('PySide6.QtWidgets',fromlist=['QPushButton']).QPushButton,'saveMasterBtn'); self.saveContractBtn=self.ui.findChild(__import__('PySide6.QtWidgets',fromlist=['QPushButton']).QPushButton,'saveContractBtn'); self.savePlotBtn=self.ui.findChild(__import__('PySide6.QtWidgets',fromlist=['QPushButton']).QPushButton,'savePlotBtn');
    def _b(self,n): return self.ui.findChild(QPushButton,n)
    @property
    def masterBtn(self): return self._b('masterBtn')
    @property
    def contractBtn(self): return self._b('contractBtn')
    @property
    def lockBtn(self): return self._b('lockBtn')
    @property
    def masterPlotBtn(self): return self._b('masterPlotBtn')
    def refresh(self): self.ideaEdit.setPlainText(self.w.db.get_meta('idea','')); self.masterEdit.setPlainText(self.w.db.get_plan()); c=self.w.db.get_contract(); self.contractEdit.setPlainText(c['content'] if c else ''); self.masterPlotEdit.setPlainText(self.w.db.get_meta('master_plot',''))
    def _b(self,n): return self.ui.findChild(QPushButton,n)
    @property
    def masterBtn(self): return self._b('masterBtn')
    @property
    def contractBtn(self): return self._b('contractBtn')
    @property
    def lockBtn(self): return self._b('lockBtn')
    @property
    def masterPlotBtn(self): return self._b('masterPlotBtn')
