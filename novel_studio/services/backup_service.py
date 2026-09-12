from datetime import datetime
import shutil
class BackupService:
    def __init__(self,project):self.project=project
    def backup(self):
        if not self.project.active: raise RuntimeError("프로젝트가 없습니다.")
        dest=self.project.paths.backups/datetime.now().strftime("%Y%m%d_%H%M%S"); shutil.copytree(self.project.paths.root,dest,dirs_exist_ok=True,ignore=shutil.ignore_patterns("backups","__pycache__",".venv")); return dest
