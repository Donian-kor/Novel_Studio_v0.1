from __future__ import annotations
from pathlib import Path
from novel_studio.core.project import ProjectManager
from novel_studio.db.database import Database
class ProjectService:
    def __init__(self,project):self.project=project;self.db=None
    def create(self,root,title,genre,mood,total,chars,tol):
        self.project.create(Path(root),title,genre,mood,total,chars,tol); self.db=Database(self.project.root/"novel.db");
        for k,v in {"title":title,"genre":genre,"mood":mood,"target_chapters":str(total),"chapter_chars":str(chars),"tolerance":str(tol)}.items():self.db.set_meta(k,v)
        self.db.ensure_chapters(total,chars)
    def open(self,root): self.project.open(Path(root)); self.db=Database(self.project.root/"novel.db")
