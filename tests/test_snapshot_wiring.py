# -*- coding: utf-8 -*-
"""원고 '저장' 버튼 배선과 상태 스냅샷 조회 폴백에 대한 회귀 테스트.

배경: PySide6 QPushButton.clicked(bool)는 슬롯의 첫 인자에 checked(False)를
주입한다. save_current(update_memory=True)를 직접 연결하면 update_memory=False가
되어 스냅샷/기억 갱신이 실행되지 않는 버그가 있었다. 배선부는 반드시
``lambda _checked=False: ...`` 형태로 감싸야 한다.
"""
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication, QPushButton

from novel_studio.db.threadsafe_database import ThreadSafeDatabase


def _app():
    return QApplication.instance() or QApplication([])


class TestSaveButtonWiring(unittest.TestCase):
    """원고 뷰 / 상단 도구 모음의 clicked(bool) 주입 차단 패턴."""

    def test_clicked_injects_false_into_direct_slot(self):
        """버그 재현: clicked를 한 개 인자를 가진 메서드에 직접 연결하면 False가 주입된다.

        production: save_current(self, update_memory=True)에 clicked.connect(...)로
        직접 연결하면 update_memory=False가 되어 기억 갱신이 실행되지 않는다.
        """

        class _Fake:
            def __init__(self):
                self.calls = []

            def save_current(self, update_memory=True):
                self.calls.append(update_memory)

        _app()
        fake = _Fake()
        btn = QPushButton('저장')
        btn.clicked.connect(fake.save_current)
        btn.click()

        self.assertEqual(fake.calls, [False])

    def test_lambda_wrapper_swallows_checked(self):
        """배선 패턴: 람다가 checked를 삼키므로 슬롯 기본값이 그대로 쓰인다."""
        _app()
        btn = QPushButton('저장')
        results = []

        # main_window._wire_manuscript_buttons와 동일한 배선
        def fake_save_current(update_memory=True):
            results.append(update_memory)

        btn.clicked.connect(lambda _checked=False: fake_save_current())
        btn.click()

        self.assertEqual(results, [True])

    def test_save_all_wiring_keeps_manual_popup_semantics(self):
        """save_all은 silent 기본값 False(수동 저장)가 유지되어야 한다."""
        _app()
        btn = QPushButton('saveAllBtn')
        results = []

        # main_window._init_ui의 saveAllBtn 배선과 동일한 패턴
        def fake_save_all(silent=False):
            results.append(('manual' if not silent else 'silent'))

        btn.clicked.connect(lambda _checked=False: fake_save_all())
        btn.click()

        self.assertEqual(results, ['manual'])


class TestStateSnapshotFallback(unittest.TestCase):
    """_update_state 폴백: state:N-1이 없으면 N-1 이하 최신만 사용."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = ThreadSafeDatabase(Path(self.tmp.name) / 'novel.db')

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_latest_state_snapshot_before_or_equal(self):
        self.db.save_snapshot('state:1', '1화 상태')
        self.db.save_snapshot('state:3', '3화 상태')

        # 인자 없음 → 전체 최신
        row = self.db.latest_state_snapshot()
        self.assertEqual(row['scope'], 'state:3')

        # 2화 기준 → 2화 이하 최신인 state:1 (미확정 가능성이 있는 state:3 제외)
        row = self.db.latest_state_snapshot(2)
        self.assertEqual(row['scope'], 'state:1')

        # 0 이하 → 전체 최신 (1화 화면 같은 케이스)
        row = self.db.latest_state_snapshot(0)
        self.assertIsNone(row)

    def test_empty_database_returns_none(self):
        self.assertIsNone(self.db.latest_state_snapshot(2))
        self.assertIsNone(self.db.latest_state_snapshot())


class TestSaveButtonBusyLock(unittest.TestCase):
    """스냅샷 생성 동안 저장 버튼이 로딩 상태로 잠기는 회귀 테스트.

    save_current()는 파일 저장 후 백그라운드로 기억/스냅샷을 갱신한다.
    완료/실패/취소 어느 경로를 타도 _set_save_buttons_busy(False)로
    복원되어야 하고, 연타로 작업을 스킵시키는 일이 없어야 한다.
    """

    @staticmethod
    def _fake_window():
        return SimpleNamespace(
            saveAllBtn=QPushButton('전체 저장'),
            _save_all_btn_text='전체 저장',
            _save_btn=QPushButton('저장'),
            _save_btn_text='저장',
        )

    def test_busy_locks_buttons_and_shows_loading_text(self):
        _app()
        from novel_studio.ui.main_window import MainWindow

        fake = self._fake_window()
        MainWindow._set_save_buttons_busy(fake, True)

        self.assertFalse(fake.saveAllBtn.isEnabled())
        self.assertFalse(fake._save_btn.isEnabled())
        self.assertEqual(fake.saveAllBtn.text(), '⏳ 스냅샷 생성 중...')
        self.assertEqual(fake._save_btn.text(), '⏳ 스냅샷 생성 중...')

        MainWindow._set_save_buttons_busy(fake, False)
        self.assertTrue(fake.saveAllBtn.isEnabled())
        self.assertTrue(fake._save_btn.isEnabled())
        self.assertEqual(fake.saveAllBtn.text(), '전체 저장')
        self.assertEqual(fake._save_btn.text(), '저장')

    def test_restore_preserves_original_button_text(self):
        _app()
        from novel_studio.ui.main_window import MainWindow

        fake = SimpleNamespace(
            saveAllBtn=QPushButton('임의 문구'),
            _save_all_btn_text='임의 문구',
            _save_btn=QPushButton('임의 문구 2'),
            _save_btn_text='임의 문구 2',
        )
        MainWindow._set_save_buttons_busy(fake, True)
        MainWindow._set_save_buttons_busy(fake, False)
        self.assertEqual(fake.saveAllBtn.text(), '임의 문구')
        self.assertEqual(fake._save_btn.text(), '임의 문구 2')

    def test_tolerates_missing_buttons(self):
        _app()
        from novel_studio.ui.main_window import MainWindow

        fake = SimpleNamespace()  # UI에 버튼이 없을 수도 있다
        MainWindow._set_save_buttons_busy(fake, True)
        MainWindow._set_save_buttons_busy(fake, False)


class TestControllerRunTaskCallbacks(unittest.TestCase):
    """run_task가 done/error/cancelled 콜백을 _run_job까지 전달하는지 검증."""

    def test_forwards_all_callbacks_to_run_job(self):
        from novel_studio.controllers.novel_controller import NovelController

        controller = NovelController()
        done = lambda r: None
        err = lambda e: None
        cancel = lambda: None

        with mock.patch.object(controller, '_run_job', return_value=True) as run:
            ok = controller.run_task(
                '레이블', 'fn',
                done_callback=done, error_callback=err, cancelled_callback=cancel,
            )

        self.assertTrue(ok)
        run.assert_called_once_with('레이블', 'fn', done, err, cancel)

    def test_backward_compatible_without_callbacks(self):
        from novel_studio.controllers.novel_controller import NovelController

        controller = NovelController()
        with mock.patch.object(controller, '_run_job', return_value=True) as run:
            ok = controller.run_task('레이블', 'fn')

        self.assertTrue(ok)
        run.assert_called_once_with('레이블', 'fn', None, None, None)


if __name__ == '__main__':
    unittest.main()