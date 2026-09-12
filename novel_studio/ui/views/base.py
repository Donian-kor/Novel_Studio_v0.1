from PySide6.QtWidgets import QWidget
from novel_studio.ui.loader import load_ui
class FormView(QWidget):
    FORM=''
    def __init__(self,parent=None):
        super().__init__(parent); self.form=load_ui(self.FORM,self); self.setLayout(self.form.layout())
