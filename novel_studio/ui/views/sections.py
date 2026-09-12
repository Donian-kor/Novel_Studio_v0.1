from .base import FormView
from novel_studio.ui.loader import load_ui
SECTIONS=['세계관','수련체계','세력','장소','인물','시간축','복선','핵심 사건']
class SectionsView(FormView):
    FORM='sections.ui'
    def __init__(self,cb,parent=None):
        super().__init__(parent);self.tabs=self.form.sectionTabs;self.edits={}
        for sec in SECTIONS:
            p=load_ui('section_page.ui',self);p.sectionTitle.setText(sec);self.tabs.addTab(p,sec);self.edits[sec]=p.contentEdit
            p.generateButton.clicked.connect(lambda _,s=sec:cb['generate'](s));p.improveButton.clicked.connect(lambda _,s=sec:cb['improve'](s));p.loadButton.clicked.connect(lambda _,s=sec:cb['load'](s))
