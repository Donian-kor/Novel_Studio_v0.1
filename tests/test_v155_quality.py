import unittest
from unittest.mock import patch
import urllib.request


class TestV155Timeout(unittest.TestCase):
    def test_ai_request_uses_long_timeout_not_connect_timeout(self):
        from novel_studio.ai.providers.base import AIProvider

        class P(AIProvider):
            def _chat_impl(self, *a, **k): return ''
            def _chat_stream_impl(self, *a, **k): return iter(())

        provider = P({})
        sentinel = object()
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured['timeout'] = timeout
            return sentinel

        req = urllib.request.Request('http://127.0.0.1:1234/v1/chat/completions', method='POST')
        with patch('urllib.request.urlopen', fake_urlopen):
            out = provider._check_urlopen(req, 1800)
        self.assertIs(out, sentinel)
        self.assertEqual(captured['timeout'], 1800.0)


class TestV155UIContract(unittest.TestCase):
    def test_story_ui_has_three_stage_cards_and_clear_labels(self):
        from pathlib import Path
        text = (Path(__file__).resolve().parents[1] / 'novel_studio/ui/forms/story.ui').read_text(encoding='utf-8')
        for name in ('masterPlotPreview','detailList','chapterCombo','generateBtn','regenerateSelectedBtn','regenerateAllBtn','generateChapterBtn','regenerateChapterBtn','saveBtn','detail'):
            self.assertIn(f'name="{name}"', text)
        for card in ('masterCard','detailCard','chapterCard','detailEditCard'):
            self.assertIn(f'name="{card}"', text)
        for label in ('① 전체 줄거리','② 구간별 상세 스토리','③ 화별 스토리'):
            self.assertIn(label, text)
        self.assertIn('구간 수', text)


if __name__ == '__main__':
    unittest.main()
