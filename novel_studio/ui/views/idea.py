from .base import FormView
class IdeaView(FormView):
    FORM='idea.ui'
    def __init__(self,callbacks,parent=None):
        super().__init__(parent); self.idea=self.form.ideaEdit
        self.form.generateButton.clicked.connect(callbacks['generate']); self.form.useButton.clicked.connect(callbacks['use'])
