from novel_studio.ai.prompts import chat_system
class ChatService:
    def __init__(self,db,ai,context):self.db,self.ai,self.context=db,ai,context
    def send(self,chapter,message):
        r=self.ai.generate(message,system=chat_system(self.context.build(chapter)),temperature=.70,max_tokens=8500); self.db.add_chat("user",message,chapter); self.db.add_chat("assistant",r,chapter); return r
