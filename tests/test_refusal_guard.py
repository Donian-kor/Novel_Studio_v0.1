"""집필/윤문 결과가 AI 안내·거부 메시지일 때 저장을 차단하는 방어 로직 테스트.

실제 발생한 사고: 3화 분량 보정(adjust)에 빈 원고가 전달되어 AI가
"원고를 제공하지 않으셨기 때문에..."라는 거부 메시지를 반환했고,
그 메시지가 검증 없이 chapters/003.txt에 저장되어 다음 집필·윤문이
계속 오염되는 악순환이 생겼다.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from novel_studio.manuscript.chapter_writer import ChapterWriter
from novel_studio.ui.main_window import MainWindow


REAL_REFUSAL = (
    '죄송합니다만, 원고를 제공하지 않으셨기 때문에 원고 내용을 확인하고 조정을 할 수 없습니다. '
    '원고의 내용과 형식을 공유해 주시면, 사건의 흐름과 문체를 유지하면서 900~1100자로 '
    '자연스럽게 조정해 드리겠습니다. 원고를 보내주시면 바로 작업을 시작하겠습니다. 감사합니다.'
)

NORMAL_MANUSCRIPT = (
    '박지영은 창밖을 멍하니 바라보다 노트북을 닫고 손끝으로 책상 위를 가볍게 두드린다. '
    '오늘 밤에는 가족들과 솔직하게 대화를 나누기로 마음먹었다. 부모님의 기대와 자신의 선택 '
    '사이에서 늘 갈등했다. 아버지의 말이 귓가에 맴돈다.' * 3
)


class _FailingAI:
    """adjust가 AI를 호출하면 테스트 실패로 기록하는 스텁."""

    def __init__(self):
        self.called = False

    def generate(self, *args, **kwargs):
        self.called = True
        raise AssertionError('빈 원고로 AI가 호출되면 안 됩니다.')


def test_real_refusal_message_is_detected():
    """실제 003.txt에 저장됐던 거부 메시지를 정확히 감지한다."""
    assert MainWindow._looks_like_ai_refusal(REAL_REFUSAL)


def test_normal_manuscript_is_not_flagged():
    """정상 원고는 거부 메시지로 오탐하지 않는다."""
    assert not MainWindow._looks_like_ai_refusal(NORMAL_MANUSCRIPT)


def test_long_text_with_marker_is_not_flagged():
    """길이 상한(800자)을 넘는 본문은 마커가 있어도 오탐하지 않는다."""
    long_text = (NORMAL_MANUSCRIPT + ' ') * 3 + ' 죄송합니다만 말씀드릴 것이 있습니다.'
    assert len(long_text) > 800
    assert not MainWindow._looks_like_ai_refusal(long_text)


def test_empty_text_is_handled_separately():
    """빈 문자열은 거부 판정이 아니라 별도 분기(빈 응답)로 처리된다."""
    assert not MainWindow._looks_like_ai_refusal('')
    assert not MainWindow._looks_like_ai_refusal(None)


def test_adjust_rejects_empty_text_without_ai_call():
    """빈 원고로 adjust를 호출하면 AI 호출 전에 ValueError로 차단된다."""
    ai = _FailingAI()
    writer = ChapterWriter(db=None, ai=ai, project=None, context=None)
    try:
        writer.adjust('', target=1000, tol=100)
        raised = False
    except ValueError:
        raised = True
    assert raised, '빈 원고에서 ValueError가 발생해야 한다'
    assert not ai.called, '빈 원고로는 AI를 호출하지 않아야 한다'


def test_adjust_accepts_normal_text():
    """정상 원고는 기존처럼 AI 보정 프롬프트로 전달된다."""
    captured = {}

    class _FakeSettings:
        data = {'ai': {'max_tokens': 9000}}

    class _OKAI:
        settings = _FakeSettings()

        def generate(self, prompt, **kwargs):
            captured['prompt'] = prompt
            return '보정된 원고'

    class _FakeProject:
        settings = {'chapter_chars': 1000}

    writer = ChapterWriter(db=None, ai=_OKAI(), project=_FakeProject(), context=None)
    out = writer.adjust('정상 원고 본문', target=1000, tol=100)
    assert out == '보정된 원고'
    assert '정상 원고 본문' in captured['prompt']
    assert '900~1100자' in captured['prompt']


if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f'PASS: {fn.__name__}')
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f'FAIL: {fn.__name__}: {e}')
    print(f'{len(fns) - failed}/{len(fns)} passed')
    sys.exit(1 if failed else 0)
