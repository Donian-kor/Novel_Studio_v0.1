import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path
BASE = Path('novel_studio')

# --- 1. planning.py rewrite ---
(BASE/'ui/views/planning.py').write_text(
"from ._base import BaseView\n"
"from PySide6.QtWidgets import QPlainTextEdit, QPushButton\n"
"\n"
"class PlanningView(BaseView):\n"
"    def __init__(self, w):\n"
"        super().__init__(w); self.mount('planning.ui'); self.w = w\n"
"        self.ideaEdit = self.ui.findChild(QPlainTextEdit, 'ideaEdit')\n"
"        self.generateBtn = self.ui.findChild(QPushButton, 'generateBtn')\n"
"        self.useBtn = self.ui.findChild(QPushButton, 'useBtn')\n"
"        self.masterEdit = self.ui.findChild(QPlainTextEdit, 'masterEdit')\n"
"        self.contractEdit = self.ui.findChild(QPlainTextEdit, 'contractEdit')\n"
"        self.masterPlotEdit = self.ui.findChild(QPlainTextEdit, 'masterPlotEdit')\n"
"        self.saveMasterBtn = self.ui.findChild(QPushButton, 'saveMasterBtn')\n"
"        self.saveContractBtn = self.ui.findChild(QPushButton, 'saveContractBtn')\n"
"        self.savePlotBtn = self.ui.findChild(QPushButton, 'savePlotBtn')\n"
"\n"
"    def _b(self, n): return self.ui.findChild(QPushButton, n)\n"
"    @property\n"
"    def masterBtn(self): return self._b('masterBtn')\n"
"    @property\n"
"    def contractBtn(self): return self._b('contractBtn')\n"
"    @property\n"
"    def lockBtn(self): return self._b('lockBtn')\n"
"    @property\n"
"    def masterPlotBtn(self): return self._b('masterPlotBtn')\n"
"\n"
"    def refresh(self):\n"
"        self.ideaEdit.setPlainText(self.w.db.get_meta('idea', ''))\n"
"        self.masterEdit.setPlainText(self.w.db.get_plan())\n"
"        c = self.w.db.get_contract()\n"
"        self.contractEdit.setPlainText(c['content'] if c else '')\n"
"        self.masterPlotEdit.setPlainText(self.w.db.get_meta('master_plot', ''))\n",
encoding='utf-8')
print('planning.py done')

# --- 2. manuscript.py rewrite (spell/strip buttons) ---
(BASE/'ui/views/manuscript.py').write_text(
"from ._base import BaseView\n"
"from PySide6.QtWidgets import QLineEdit, QPushButton, QListWidget, QPlainTextEdit, QLabel\n"
"\n"
"class ManuscriptView(BaseView):\n"
"    def __init__(self, w):\n"
"        super().__init__(w); self.mount('manuscript.ui'); self.w = w\n"
"        self.titleEdit = self.ui.findChild(QLineEdit, 'titleEdit')\n"
"        self.writeBtn = self.ui.findChild(QPushButton, 'writeBtn')\n"
"        self.chatBtn = self.ui.findChild(QPushButton, 'chatBtn')\n"
"        self.reviseBtn = self.ui.findChild(QPushButton, 'reviseBtn')\n"
"        self.checkBtn = self.ui.findChild(QPushButton, 'checkBtn')\n"
"        self.saveBtn = self.ui.findChild(QPushButton, 'saveBtn')\n"
"        self.spellBtn = self.ui.findChild(QPushButton, 'spellBtn')\n"
"        self.stripBtn = self.ui.findChild(QPushButton, 'stripBtn')\n"
"        self.chapterList = self.ui.findChild(QListWidget, 'chapterList')\n"
"        self.editor = self.ui.findChild(QPlainTextEdit, 'editor')\n"
"        self.countLabel = self.ui.findChild(QLabel, 'countLabel')\n",
encoding='utf-8')
print('manuscript.py done')
