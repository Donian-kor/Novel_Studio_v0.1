# 임시 테스트 스크립트: 설정DB 새 폼 동작 검증 (오프스크린)
import os
import sys
import tempfile

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
sys.path.insert(0, r'c:/Users/donian/Desktop/python/Novel_Studio')

from PySide6.QtWidgets import QApplication

app = QApplication([])

from novel_studio.db.database import Database

dbpath = os.path.join(tempfile.gettempdir(), f'novel_test_entities_{os.getpid()}.db')
if os.path.exists(dbpath):
    os.remove(dbpath)
db = Database(dbpath)

from novel_studio.ui.views.entities import EntitiesView
from PySide6.QtWidgets import QWidget as _QW


class W(_QW):
    pass


w = W()
w.db = db
v = EntitiesView(w)

# 1) 인물 2명 준비 후 목록 확인
db.save_character({'name': '서연', 'role': '여주', 'profile': '원래 프로필'})
db.save_character({'name': '민준', 'role': '남주', 'goal': '복수'})
v.refresh()
assert v.list.count() == 2, v.list.count()

# 2) 서연 선택 후 프로필 필드만 수정
idx = [j for j in range(v.list.count()) if v.list.item(j).text() == '서연'][0]
v.list.setCurrentRow(idx)
assert v.nameEdit.text() == '서연', v.nameEdit.text()
v.fields['profile'].setPlainText('수정된 프로필')
assert idx in v._dirty, v._dirty

# 3) 다른 항목으로 이동해도 변경 표시 유지
v.list.setCurrentRow(0 if idx != 0 else 1)
assert len(v._dirty) == 1, v._dirty

# 4) 저장: 선택되지 않은 서연의 변경분이 반영되는지
v.save_entry(quiet=True)
rows = {r['name']: dict(r) for r in db.characters()}
assert rows['서연']['profile'] == '수정된 프로필', rows['서연']['profile']
assert rows['서연']['role'] == '여주'
assert rows['민준']['goal'] == '복수'
# 중첩 버그 회귀 확인: profile 값에 'profile:' 같은 라벨이 섞이지 않는지
assert 'profile' not in rows['서연']['profile']

# 5) 변경 없이 저장 → 내용 그대로 유지
v.save_entry(quiet=True)
rows2 = {r['name']: dict(r) for r in db.characters()}
assert rows2['서연']['profile'] == '수정된 프로필'
assert rows2['민준']['goal'] == '복수'

# 6) 카테고리 전환 시 변경분 자동 커밋
v.list.setCurrentRow(idx)
v.fields['goal'].setPlainText('새 목표')
v.catCombo.setCurrentText('세력')
rows3 = {r['name']: dict(r) for r in db.characters()}
assert rows3['서연']['goal'] == '새 목표', rows3['서연']['goal']

# 7) 이름 변경: 서연 -> 서연이 (기존 이름 삭제 + 새 이름 저장)
v.catCombo.setCurrentText('인물')
idx = [j for j in range(v.list.count()) if v.list.item(j).text() == '서연'][0]
v.list.setCurrentRow(idx)
v.nameEdit.setText('서연이')
v.save_entry(quiet=True)
names = sorted(r['name'] for r in db.characters())
assert names == sorted(['서연이', '민준']), names
rows4 = {r['name']: dict(r) for r in db.characters()}
assert rows4['서연이']['profile'] == '수정된 프로필', rows4['서연이']['profile']

# 8) 카테고리별 필드 구성 확인
for cat, expected in {
    '인물': ['role', 'profile', 'personality', 'speech_style', 'goal', 'secret', 'arc'],
    '세력': ['description', 'rules'],
    '복선': ['title', 'first_chapter', 'reveal_chapter', 'status', 'public_info', 'author_truth', 'related_characters', 'notes'],
    '핵심 사건': ['start_chapter', 'end_chapter', 'description', 'consequence', 'status'],
    '시간축': ['chapter_number', 'story_date', 'description', 'location', 'participants'],
}.items():
    v.catCombo.setCurrentText(cat)
    assert list(v.fields.keys()) == expected, (cat, list(v.fields.keys()))
    labels = [lbl for lbl, _w in v.detail_widgets()]
    assert labels[0] in ('이름', '코드', '제목')

print('TEST_OK')
