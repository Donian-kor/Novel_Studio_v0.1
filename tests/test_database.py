import tempfile
import unittest
from pathlib import Path

from novel_studio.db.threadsafe_database import ThreadSafeDatabase


class TestDatabase(unittest.TestCase):
    def test_crud_and_continuity_lookup(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = ThreadSafeDatabase(Path(tmp) / 'novel.db')
            db.ensure_chapters(3, 5000)
            db.set_chapter_meta(1, '1화', '작성완료', 6, 7, 5000)
            self.assertEqual(db.chapter(1)['char_count'], 6)

            db.save_character({'name': '홍길동', 'role': '주인공'})
            self.assertEqual(db.characters()[0]['name'], '홍길동')

            db.add_continuity(1, 'warning', 'consistency', '문제', '근거')
            checks = db.continuity_for_chapter(1)
            self.assertEqual(len(checks), 1)
            self.assertEqual(checks[0]['message'], '문제')
            db.close()


if __name__ == '__main__':
    unittest.main()
