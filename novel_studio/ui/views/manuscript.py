from .base import FormView
class ManuscriptView(FormView):
    FORM='manuscript.ui'
    def __init__(self,cb,parent=None):
        super().__init__(parent);f=self.form;self.chapter=f.chapterSpin;self.title=f.titleEdit;self.editor=f.editor;self.count=f.countLabel;f.chapterSpin.valueChanged.connect(cb['load']);f.editor.textChanged.connect(cb['count']);f.saveButton.clicked.connect(cb['save']);f.writeButton.clicked.connect(cb['write']);f.reviseButton.clicked.connect(cb['revise']);f.checkButton.clicked.connect(cb['check']);f.chatButton.clicked.connect(cb['chat'])
