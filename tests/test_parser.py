import unittest

from novel_studio.plot.parser import parse_chapter_plans, validate_chapter_plans


class ParserTests(unittest.TestCase):
    def test_markdown_headers(self):
        text = "### 제1화\n제목: 시작\n[목표]\n내용\n\n### 제2화\n제목: 전환\n[목표]\n내용"
        plans = parse_chapter_plans(text)
        self.assertEqual([(p[0], p[1]) for p in plans], [(1, "시작"), (2, "전환")])
        self.assertTrue(validate_chapter_plans(plans, 1, 2)["valid"])

    def test_legacy_headers(self):
        text = "[화 번호]: 3화\n[제목]: 세 번째\n내용\n\n제4화 - 네 번째\n내용"
        plans = parse_chapter_plans(text)
        self.assertEqual([(p[0], p[1]) for p in plans], [(3, "세 번째"), (4, "네 번째")])

    def test_plain_headers(self):
        text = "1화. 첫 번째\n내용\n\n2화: 두 번째\n내용"
        plans = parse_chapter_plans(text)
        self.assertEqual([(p[0], p[1]) for p in plans], [(1, "첫 번째"), (2, "두 번째")])

    def test_missing_chapter_is_detected(self):
        plans = parse_chapter_plans("### 제1화\n제목: 하나\n본문")
        result = validate_chapter_plans(plans, 1, 2)
        self.assertFalse(result["valid"])
        self.assertEqual(result["missing"], [2])


if __name__ == "__main__":
    unittest.main(verbosity=2)
