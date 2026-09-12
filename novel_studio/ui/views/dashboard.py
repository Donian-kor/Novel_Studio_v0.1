from .base import FormView
class DashboardView(FormView):
    FORM='dashboard.ui'
    def __init__(self,parent=None):super().__init__(parent);self.text=self.form.dashboardText
    def set_text(self,text):self.text.setPlainText(text)
