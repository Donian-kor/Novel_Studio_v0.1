from .base import FormView
class PlotsView(FormView):
    FORM='plots.ui'
    def __init__(self,cb,parent=None):
        super().__init__(parent);f=self.form;self.start=f.startSpin;self.end=f.endSpin;self.list=f.plotList;self.detail=f.plotDetail;f.generateButton.clicked.connect(cb['generate']);f.improveButton.clicked.connect(cb['improve']);f.plotList.currentRowChanged.connect(cb['select'])
