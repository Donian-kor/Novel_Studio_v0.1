from .base import FormView
class PlanningView(FormView):
    FORM='planning.ui'
    def __init__(self,cb,parent=None):
        super().__init__(parent); f=self.form
        for name in ['ideaEdit','masterEdit','contractEdit','masterPlotEdit']: setattr(self,name,getattr(f,name))
        f.ideaButton.clicked.connect(cb['idea']);f.useIdeaButton.clicked.connect(cb['use']);f.masterButton.clicked.connect(cb['master']);f.allSectionsButton.clicked.connect(cb['all_sections']);f.contractButton.clicked.connect(cb['contract']);f.lockContractButton.clicked.connect(cb['lock']);f.masterPlotButton.clicked.connect(cb['master_plot']);f.saveMasterButton.clicked.connect(cb['save_master']);f.savePlotButton.clicked.connect(cb['save_plot'])
