from __future__ import annotations
import shutil
from datetime import datetime
from pathlib import Path
class BackupService:
    def __init__(self,pm): self.pm=pm
    def backup(self):
        if not self.pm.active: raise RuntimeError('프로젝트가 없습니다.')
        dest=self.pm.paths.backups / datetime.now().strftime('%Y%m%d_%H%M%S')
        shutil.copytree(self.pm.paths.root,dest,ignore=shutil.ignore_patterns('backups','__pycache__'),dirs_exist_ok=True)
        return dest
