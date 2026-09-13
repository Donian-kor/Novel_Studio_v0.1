import json, re
from hashlib import sha256

class MasterDiffService:
    def __init__(self, db, ai): self.db,self.ai=db,ai
    def propose(self, old, new, category='master_plan'):
        if old == new: return {'changed':False,'summary':'변경 없음','changes':[]}
        prompt=("기존 설정과 새 설정의 변경점을 JSON 배열로 추출하라. 기존 설정을 기준으로 한다.\n"
                "각 원소: {\"type\":\"add|modify|remove|conflict\",\"path\":\"\",\"before\":\"\",\"after\":\"\",\"reason\":\"\"}\n"
                "JSON만 출력.\n[기존]\n"+old[:18000]+"\n[새 설정]\n"+new[:18000])
        raw=self.ai.generate(prompt,temperature=.1,max_tokens=5000)
        changes=[]
        try:
            cleaned=re.sub(r'^```(?:json)?\s*|\s*```$','',raw.strip(),flags=re.I|re.S).strip()
            start,end=cleaned.find('['),cleaned.rfind(']')
            if start >= 0 and end > start:
                parsed=json.loads(cleaned[start:end+1])
                changes=parsed if isinstance(parsed,list) else []
        except Exception:
            changes=[]
        payload={'changed':True,'summary':f'{len(changes)}개 변경 제안','changes':changes,'hash_old':sha256(old.encode()).hexdigest(),'hash_new':sha256(new.encode()).hexdigest()}
        self.db.save_master_diff(category,json.dumps(payload,ensure_ascii=False),'제안')
        return payload
