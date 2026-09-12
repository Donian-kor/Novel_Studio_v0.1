from .base import FormView
class RangesView(FormView):
    FORM='ranges.ui'
    def __init__(self,cb,parent=None):
        super().__init__(parent);f=self.form;self.size=f.sizeSpin;self.list=f.rangeList;self.detail=f.rangeDetail;f.generateButton.clicked.connect(cb['generate']);f.snapshotButton.clicked.connect(cb['snapshot']);f.rangeList.currentRowChanged.connect(cb['select'])
