from __future__ import annotations

import pytest

pytest.importorskip("PySide6")
pytest.importorskip("pytestqt")

from PySide6.QtWidgets import QLabel, QWidget


def test_qt_widget_smoke(qtbot) -> None:
    widget = QWidget()
    widget.setWindowTitle("Novel Studio")
    label = QLabel("UI 상태 테스트", widget)
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)
    assert label.text() == "UI 상태 테스트"


def test_main_window_can_switch_views_and_restore_ui_state(qtbot, tmp_path):
    from novel_studio.core.project import ProjectManager
    from novel_studio.ui.main_window import MainWindow

    root = tmp_path / "novel"
    ProjectManager().create(
        root=root,
        title="UI 검증",
        genre="선협",
        mood="진중",
        total_chapters=3,
        chapter_chars=5000,
        tolerance=300,
    )
    window = MainWindow(root)
    qtbot.addWidget(window)
    window.nav.setCurrentRow(2)
    assert window.stack.currentIndex() == 2
    window._set_left(False)
    window._set_right(False)
    window.close()


def test_manuscript_view_refresh_reloads_saved_chapter(qtbot, tmp_path):
    """요청 회귀 검증: ManuscriptView.refresh()가 저장 본문을 다시 읽어온다."""
    from novel_studio.core.project import ProjectManager
    from novel_studio.ui.main_window import MainWindow

    root = tmp_path / "novel"
    ProjectManager().create(
        root=root,
        title="원고 새로고침 검증",
        genre="선협",
        mood="진중",
        total_chapters=3,
        chapter_chars=5000,
        tolerance=300,
    )
    window = MainWindow(root)
    qtbot.addWidget(window)

    window.pm.save_chapter(1, "1화 저장 본문")
    window.manuscript_view.editor.setPlainText("편집 중인 임시 텍스트")
    window.manuscript_view.refresh()
    assert window.manuscript_view.editor.toPlainText() == "1화 저장 본문"
    assert window.manuscript_view.titleEdit.text() == "1화"
    window.close()


def test_collapsed_sidebar_expand_button_is_clickable(qtbot, tmp_path):
    """사이드바 접힘 회귀 검증: 접힌 뒤 펼치기 버튼이 충분히 커서 누를 수 있어야 한다."""
    from PySide6.QtCore import Qt

    from novel_studio.core.project import ProjectManager
    from novel_studio.ui.main_window import MainWindow

    root = tmp_path / "novel"
    ProjectManager().create(
        root=root,
        title="사이드바 접힘 검증",
        genre="선협",
        mood="진중",
        total_chapters=3,
        chapter_chars=5000,
        tolerance=300,
    )
    window = MainWindow(root)
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

    # 접기: 패널은 숨고, 핸들의 펼치기 버튼만 보여야 한다
    window._set_left(False)
    window._set_right(False)
    assert not window.left.isVisible()
    assert not window.right.isVisible()
    assert window.leftExpand.isVisible()
    assert window.rightExpand.isVisible()

    # 접힌 상태에서 펼치기 버튼이 충분히 커야 누를 수 있다
    # (핸들 폭 40px, 버튼 최소 높이 48px + 핸들 세로 Expanding)
    assert window.leftExpand.width() >= 36
    assert window.leftExpand.height() >= 48
    assert window.rightExpand.width() >= 36
    assert window.rightExpand.height() >= 48

    # 실제 클릭으로 다시 펼쳐지는지 기능 검증
    qtbot.mouseClick(window.leftExpand, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.rightExpand, Qt.MouseButton.LeftButton)
    assert window.left.isVisible()
    assert window.right.isVisible()
    window.close()


def test_settings_dialog_title_and_size_follow_ui_file(qtbot, tmp_path):
    """설정창 회귀 검증: 제목/크기가 ai_settings.ui 기준으로 결정되어야 한다.

    과거에는 코드에서 setWindowTitle이 누락되어 창 제목이 'Novel Studio'로
    표시되고, resize(780, 740)이 .ui 크기보다 우선했다.
    """
    from novel_studio.core.project import ProjectManager
    from novel_studio.ui.dialogs import AISettingsDialog
    from novel_studio.ui.main_window import MainWindow

    root = tmp_path / "novel"
    ProjectManager().create(
        root=root,
        title="설정창 검증",
        genre="선협",
        mood="진중",
        total_chapters=3,
        chapter_chars=5000,
        tolerance=300,
    )
    window = MainWindow(root)
    qtbot.addWidget(window)

    d = AISettingsDialog(window.providers, window.app, window)
    qtbot.addWidget(d)
    # 제목: .ui의 windowTitle을 읽어 실제 창 제목에 적용
    assert d.ui.windowTitle() == "AI / 편집기 설정"
    assert d.windowTitle() == "AI / 편집기 설정"
    # 체크박스: .ui에서 로드되며, 저장된 설정 상태를 반영
    from PySide6.QtWidgets import QCheckBox
    cb = d.ui.findChild(QCheckBox, "endStateCheck")
    assert cb is not None
    assert cb.text() == "원고 저장 후 AI로 화 종료 상태 자동 생성"
    assert cb.isChecked() == bool(window.app.data.get("editor", {}).get("auto_generate_end_state", False))
    # 체크 강조: 체크 시 지시자(indicator) 영역이 녹색으로 렌더링되어야 한다
    cb.setChecked(True)
    img = cb.grab().toImage()
    greens = 0
    for y in range(min(40, img.height())):
        for x in range(min(40, img.width())):
            c = img.pixelColor(x, y)
            if abs(c.red() - 39) < 40 and abs(c.green() - 174) < 40 and abs(c.blue() - 96) < 40:
                greens += 1
    assert greens > 0
    # 크기: 코드 강제 resize(780, 740) 제거 → 콘텐츠 기반 크기
    assert (d.width(), d.height()) != (780, 740)
    assert d.height() < 600
    # 백그라운드 모델 목록 조회가 끝난 뒤 닫는다 (종료 시 스레드 잔류 방지)
    qtbot.waitUntil(lambda: not getattr(d, "_model_threads", []), timeout=15000)
    # 연결 확인 전에는 모델 목록이 비활성화되고 상태는 '연결 안 됨'
    assert not d.modelEdit.isEnabled()
    assert d.connStatus.text() == "연결 안 됨"
    d.close()


def test_settings_dialog_opens_without_network_block(qtbot, tmp_path):
    """설정창 딜레이 회귀 검증: 열기가 모델 목록 네트워크 조회로 블로킹되지 않아야 한다.

    과거에는 load_provider()가 UI 스레드에서 list_models()를 호출해 LM Studio가
    꺼져 있으면 접속 대기(~4초)만큼 설정창 열림이 지연됐다.
    """
    import time

    from novel_studio.core.project import ProjectManager
    from novel_studio.ui.dialogs import AISettingsDialog
    from novel_studio.ui.main_window import MainWindow

    root = tmp_path / "novel"
    ProjectManager().create(
        root=root,
        title="모델 목록 논블로킹 검증",
        genre="선협",
        mood="진중",
        total_chapters=3,
        chapter_chars=5000,
        tolerance=300,
    )
    window = MainWindow(root)
    qtbot.addWidget(window)

    # 실제처럼 목록 조회가 느린 상황을 스텁으로 재현 (0.5초 지연)
    orig_build = window.providers._build

    def slow_build(pid, cfg):
        provider = orig_build(pid, cfg)
        orig_list = provider.list_models

        def slow_list():
            time.sleep(0.5)
            return orig_list()

        provider.list_models = slow_list
        return provider

    window.providers._build = slow_build

    t0 = time.perf_counter()
    d = AISettingsDialog(window.providers, window.app, window)
    create_ms = (time.perf_counter() - t0) * 1000
    qtbot.addWidget(d)
    # 다이얼로그 생성은 네트워크 대기 없이 즉시 끝나야 한다 (과거 ~4초 블로킹)
    assert create_ms < 1000, f"설정창 생성이 {create_ms:.0f}ms로 너무 느림 (블로킹 의심)"
    # 저장된 모델명은 조회와 무관하게 즉시 반영되어 있어야 한다
    saved_model = (window.app.data["providers"].get(window.app.data["active_provider"], {}).get("model") or "").strip()
    assert d.modelEdit.currentText().strip() == saved_model
    # 백그라운드 조회 종료까지 기다려 스레드 잔류 없이 정리되는지 확인
    qtbot.waitUntil(lambda: not d._model_threads, timeout=15000)
    d.close()


def test_connection_test_gates_model_list_and_status(qtbot, tmp_path):
    """연결 상태 회귀 검증: 연결 확인 전 모델 목록 비활성, 테스트 성공 시 활성+녹색 표기.

    - 다이얼로그를 열면 모델 목록이 비활성화되고 '연결 안 됨'이어야 한다
    - 연결 테스트 성공 → 모델 목록 활성화 + '연결됨'(녹색)
    - 연결 테스트 실패 → 비활성화 유지 + '연결 실패'(빨강)
    """
    from PySide6.QtWidgets import QMessageBox

    from novel_studio.core.project import ProjectManager
    from novel_studio.ui.dialogs import AISettingsDialog
    from novel_studio.ui.main_window import MainWindow

    root = tmp_path / "novel"
    ProjectManager().create(
        root=root,
        title="연결 상태 검증",
        genre="선협",
        mood="진중",
        total_chapters=3,
        chapter_chars=5000,
        tolerance=300,
    )
    window = MainWindow(root)
    qtbot.addWidget(window)

    d = AISettingsDialog(window.providers, window.app, window)
    qtbot.addWidget(d)
    # 연결 테스트 완료 콜백이 early-return하지 않도록 창을 표시한다
    d.show()
    # 백그라운드 조회 종료 대기 후 초기 상태 확인
    qtbot.waitUntil(lambda: not d._model_threads, timeout=15000)
    assert not d.modelEdit.isEnabled()
    assert d.connStatus.text() == "연결 안 됨"

    # 메시지박스와 저장 부수효과를 차단 (사용자 실제 설정 파일 보호)
    monkeypatched = {"info": QMessageBox.information, "critical": QMessageBox.critical}
    QMessageBox.information = lambda *a, **k: None
    QMessageBox.critical = lambda *a, **k: None
    orig_save = window.providers.save_provider
    orig_active = window.providers.set_active
    window.providers.save_provider = lambda *a, **k: None
    window.providers.set_active = lambda *a, **k: None
    try:
        class _OkProvider:
            config = {}

            def quick_test(self):
                return "ok"

        window.providers.build_unsaved = lambda pid, u, m, k: _OkProvider()
        d.test()  # 성공 경로 (백그라운드 스레드)
        assert not d.testBtn.isEnabled()
        assert d.testBtn.text() == "테스트 중..."
        qtbot.waitUntil(lambda: not d._test_threads, timeout=15000)
        assert d.testBtn.isEnabled()
        assert d.testBtn.text() == "연결 테스트"
        assert d.modelEdit.isEnabled()
        assert d.connStatus.text() == "연결됨"
        assert "#27AE60" in d.connStatus.styleSheet()

        class _FailProvider:
            config = {}

            def quick_test(self):
                raise RuntimeError("연결 거부")

        window.providers.build_unsaved = lambda pid, u, m, k: _FailProvider()
        d.test()  # 실패 경로 (백그라운드 스레드)
        qtbot.waitUntil(lambda: not d._test_threads, timeout=15000)
        assert d.testBtn.isEnabled()
        assert not d.modelEdit.isEnabled()
        assert d.connStatus.text() == "연결 실패"
        assert "#E74C3C" in d.connStatus.styleSheet()
    finally:
        QMessageBox.information = monkeypatched["info"]
        QMessageBox.critical = monkeypatched["critical"]
        window.providers.save_provider = orig_save
        window.providers.set_active = orig_active
    d.close()


def test_chat_window_title_and_size_follow_ui_file(qtbot, tmp_path):
    """채팅창 회귀 검증: 제목은 chat.ui의 windowTitle에서 읽고, 코드 강제 620x760 크기는 제거."""
    from novel_studio.core.project import ProjectManager
    from novel_studio.ui.main_window import MainWindow

    root = tmp_path / "novel"
    ProjectManager().create(
        root=root,
        title="채팅창 검증",
        genre="선협",
        mood="진중",
        total_chapters=3,
        chapter_chars=5000,
        tolerance=300,
    )
    window = MainWindow(root)
    qtbot.addWidget(window)
    cw = window.chat_window
    qtbot.addWidget(cw)
    assert cw.ui.windowTitle() == "AI 작품 비서"
    assert cw.windowTitle() == "AI 작품 비서"
    assert (cw.width(), cw.height()) != (620, 760)
    assert cw.height() < 700
    window.close()
