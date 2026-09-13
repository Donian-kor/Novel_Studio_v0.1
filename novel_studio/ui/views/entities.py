from ._base import BaseView
from PySide6.QtWidgets import QListWidget, QPlainTextEdit, QPushButton, QComboBox, QInputDialog, QMessageBox, QSplitter, QLineEdit
from PySide6.QtCore import Qt, QSettings
from novel_studio.ai.prompts import entity_catalog_prompt
from novel_studio.utils.entity_parser import parse_entity_catalog

class EntitiesView(BaseView):
    """설정 DB: 인물/세력/장소/복선/핵심 사건/시간축 관리."""
    CATS=['인물','세력','장소','복선','핵심 사건','시간축']
    ROLE_HINT='인물 역할 예: 남주 / 여주 / 조연 / 엑스트라'
    def __init__(self,w):
        super().__init__(w); self.mount('entities.ui'); self.w=w
        self.catCombo=self.ui.findChild(QComboBox,'catCombo'); self.catCombo.addItems(self.CATS)
        self.list=self.ui.findChild(QListWidget,'entryList'); self.detail=self.ui.findChild(QPlainTextEdit,'detail')
        self.nameEdit=self.ui.findChild(QLineEdit,'nameEdit')
        self.addBtn=self.ui.findChild(QPushButton,'addBtn'); self.aiBtn=self.ui.findChild(QPushButton,'generateBtn'); self.saveBtn=self.ui.findChild(QPushButton,'saveBtn'); self.delBtn=self.ui.findChild(QPushButton,'delBtn')
        self._install_splitter('entitiesSplitter', self.list, self.detail, sizes=(360,900))
        self.catCombo.currentTextChanged.connect(self.refresh); self.list.currentRowChanged.connect(self.show_selected)
        self.addBtn.clicked.connect(self.add_entry)
        self.aiBtn.clicked.connect(self.ai_generate)
        self.saveBtn.clicked.connect(self.save_entry)
        self.delBtn.clicked.connect(self.delete_entry)
        self.refresh()
    def _install_splitter(self,name,left,right,sizes=(360,900)):
        split=self.ui.findChild(QSplitter,name)
        if split is None:return
        split.setOrientation(Qt.Horizontal); split.setChildrenCollapsible(False); split.setHandleWidth(9)
        split.setStyleSheet('QSplitter::handle { background: #6a6a6a; } QSplitter::handle:hover { background: #9a9a9a; }')
        saved=QSettings('NovelStudio','NovelStudio').value(name+'Sizes', None)
        if saved:
            try: split.setSizes([int(x) for x in saved])
            except Exception: split.setSizes(list(sizes))
        else: split.setSizes(list(sizes))
        split.splitterMoved.connect(lambda pos,index,n=name,sp=split: QSettings('NovelStudio','NovelStudio').setValue(n+'Sizes', sp.sizes()))
        for w in (left,right):
            w.setMinimumWidth(120)
        self.splitter=split
    def _rows(self):
        db=self.w.db; cat=self.catCombo.currentText()
        if cat=='인물': return [('char',r['name'],r) for r in db.characters()]
        if cat in ('세력','장소'):
            return [('world',r['name'],r) for r in db.world_entities(category=cat)]
        if cat=='복선': return [('fore',r['code'] or r['title'],r) for r in db.foreshadows()]
        if cat=='핵심 사건': return [('major',r['title'],r) for r in db.major_events()]
        return [('time',f"{r['chapter_number'] or '-'}화 {r['title']}",r) for r in db.timeline()]
    def refresh(self):
        self._cache=self._rows(); self.list.clear()
        for _,label,_ in self._cache:self.list.addItem(str(label))
        if self._cache:self.list.setCurrentRow(0)
        else:self.detail.setPlainText('항목이 없습니다. [+ 추가] 또는 [AI로 생성/보완]을 눌러 만드세요.')
    def show_selected(self,i):
        if not getattr(self,'_cache',None) or not 0<=i<len(self._cache):
            self.nameEdit.clear()
            self.detail.clear()
            return
        kind,label,row=self._cache[i]; self.nameEdit.setText(self._display_name(row)); text=self._fmt(row)
        tl=self._entity_timeline_text(kind,row)
        if tl: text+='\n\n[상태 타임라인]\n'+tl
        self.detail.setPlainText(text)

    def _entity_timeline_text(self,kind,row):
        """인물/세력/장소 항목에 화별 상태 변화 원장(타임라인)을 붙여 보여준다."""
        if kind not in ('char','world'): return ''
        name=self._display_name(row)
        rows=self.w.db.entity_timeline(kind,name)
        if not rows: return ''
        return '\n'.join(f"{r['chapter_number']}화: {(r['state'] or '')[:400]}" for r in rows)

    def _strip_timeline(self,text):
        marker='\n\n[상태 타임라인]'
        return text.split(marker,1)[0] if marker in text else text

    def _display_name(self,row):
        if self.catCombo.currentText()=='복선': return row['code'] or row['title'] or ''
        if self.catCombo.currentText()=='시간축': return row['title'] or ''
        return row['name'] if 'name' in row.keys() else row['title'] or ''
    def _fmt(self,r):
        return '\n'.join(f'{k}: {r[k]}' for k in r.keys() if k!='id')
    def add_entry(self):
        cat=self.catCombo.currentText(); name,ok=QInputDialog.getText(self.w,f'{cat} 추가','이름/제목을 입력하세요:')
        if not(ok and name.strip()):return
        name=name.strip(); db=self.w.db
        if cat=='인물':
            role,_=QInputDialog.getText(self.w,'역할',self.ROLE_HINT+'\n역할:'); db.save_character({'name':name,'role':role or '조연'})
        elif cat in ('세력','장소'): db.save_world({'name':name,'category':cat})
        elif cat=='복선': db.save_foreshadow({'code':name,'title':name})
        elif cat=='핵심 사건': db.save_major_event({'title':name})
        else: db.save_timeline({'title':name,'chapter_number':None})
        self.refresh()
    def save_entry(self,quiet=False):
        if not getattr(self,'_cache',None): return False
        i=self.list.currentRow()
        if not 0<=i<len(self._cache): return False
        kind,label,row=self._cache[i]; text=self.detail.toPlainText(); name=(self.nameEdit.text().strip() if self.nameEdit else label.strip()); db=self.w.db
        if not name:
            QMessageBox.warning(self.w,'저장 실패','이름/제목/코드를 입력하세요.')
            return False
        try:
            if kind=='char':
                old=row['name']; data={**dict(row),'name':name,'profile':self._strip_timeline(text)};
                if old!=name: db.delete_character(old)
                db.save_character(data)
            elif kind=='world':
                old=row['name']; data={**dict(row),'name':name,'description':self._strip_timeline(text)};
                if old!=name: db.delete_world(old)
                db.save_world(data)
            elif kind=='fore':
                old=row['code']; data={**dict(row),'code':name,'title':(row['title'] if row['title'] and row['title']!=old else name),'notes':text};
                if old!=name: db.delete_foreshadow(old)
                db.save_foreshadow(data)
            elif kind=='major':
                old=row['title']; data={**dict(row),'title':name,'description':text};
                if old!=name: db.delete_major_event(old)
                db.save_major_event(data)
            else:
                db.execute('UPDATE timeline_events SET title=?,description=? WHERE id=?',(name,text,row['id']))
            self.refresh()
            if not quiet: QMessageBox.information(self.w,'저장',f'{name} 저장 완료')
            return True
        except Exception as e:
            QMessageBox.critical(self.w,'저장 실패',f'설정 DB 저장 중 오류가 발생했습니다.\n{e}')
            return False

    def delete_entry(self):
        if not getattr(self,'_cache',None):return
        i=self.list.currentRow()
        if not 0<=i<len(self._cache):return
        kind,label,row=self._cache[i]
        if QMessageBox.question(self.w,'삭제',f'{label} 삭제할까요?')!=QMessageBox.StandardButton.Yes:return
        db=self.w.db
        if kind=='char':db.delete_character(row['name'])
        elif kind=='world':db.delete_world(row['name'])
        elif kind=='fore':db.delete_foreshadow(row['code'])
        elif kind=='major':db.delete_major_event(row['title'])
        else:db.delete_timeline(row['id'])
        self.refresh()
    def _master(self):
        t=self.w.db.get_plan()
        if not t.strip():
            QMessageBox.warning(self.w,'마스터 기획 필요','먼저 [기획]에서 마스터 기획을 생성하거나 저장하세요.'); return ''
        return t
    def ai_generate(self):
        cat=self.catCombo.currentText(); master=self._master()
        if not master:return
        total=int(self.w.pm.settings.get('target_chapters',500) or 500)
        self.w._run(f'마스터 기획에서 {cat} 자동 추출/보완 중...',
            lambda:self.w.ai.generate(entity_catalog_prompt(cat,master,total),temperature=.35,max_tokens=12000),
            lambda t:self._store_catalog(cat,t))
    def _store_catalog(self,cat,text):
        items=parse_entity_catalog(text)
        if not items:
            QMessageBox.warning(self.w,'AI 결과 오류','마스터 기획에서 설정 항목을 추출하지 못했습니다. AI 응답 형식을 확인하세요.')
            return
        db=self.w.db; count=0
        for x in items:
            try:
                if cat=='인물' and x.get('name'):
                    role=x.get('role') or '조연'; db.save_character({'name':x['name'],'role':role,'profile':x.get('profile',''),'personality':x.get('personality',''),'speech_style':x.get('speech_style',''),'goal':x.get('goal',''),'secret':x.get('secret',''),'arc':x.get('arc','')})
                elif cat in ('세력','장소') and x.get('name'):
                    db.save_world({'name':x['name'],'category':cat,'description':x.get('description',''),'rules':x.get('rules','')}); count+=1; continue
                elif cat=='복선' and (x.get('code') or x.get('title')):
                    code=x.get('code') or f"F{count+1:03d}"; db.save_foreshadow({'code':code,'title':x.get('title') or code,'first_chapter':x.get('first_chapter') or None,'reveal_chapter':x.get('reveal_chapter') or None,'status':x.get('status') or '활성','public_info':x.get('public_info',''),'author_truth':x.get('author_truth',''),'related_characters':x.get('related_characters',''),'notes':x.get('notes','')}); count+=1; continue
                elif cat=='핵심 사건' and x.get('title'):
                    db.save_major_event({'title':x['title'],'start_chapter':x.get('start_chapter') or None,'end_chapter':x.get('end_chapter') or None,'description':x.get('description',''),'consequence':x.get('consequence',''),'status':x.get('status') or '계획'}); count+=1; continue
                elif cat=='시간축' and x.get('title'):
                    db.save_timeline({'chapter_number':x.get('chapter_number') or None,'story_date':x.get('story_date',''),'title':x['title'],'description':x.get('description',''),'location':x.get('location',''),'participants':x.get('participants','')}); count+=1; continue
                if cat=='인물' and x.get('name'):count+=1
            except Exception:
                continue
        self.refresh(); QMessageBox.information(self.w,'AI 자동 추가',f'마스터 기획에서 {count}개 항목을 추가/갱신했습니다.')
