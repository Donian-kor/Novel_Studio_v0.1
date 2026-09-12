from .base import FormView
class ChatView(FormView):
    FORM='chat.ui'
    def __init__(self,cb,parent=None):
        super().__init__(parent);f=self.form;self.log=f.chatLog;self.input=f.chatInput;f.sendButton.clicked.connect(cb['send']);f.clearButton.clicked.connect(self.log.clear)
