from .base import FormView
class MemoryView(FormView):
    FORM='memory.ui'
    def __init__(self,cb,parent=None):
        super().__init__(parent);f=self.form;self.edit=f.memoryEdit;f.summarizeButton.clicked.connect(cb['summary']);f.checkButton.clicked.connect(cb['check'])
