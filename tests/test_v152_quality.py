from __future__ import annotations

import json
from pathlib import Path

from novel_studio.core.app_settings import AppSettings


def test_app_settings_persists_ui_state(tmp_path: Path) -> None:
    settings = AppSettings.__new__(AppSettings)
    settings.path = tmp_path / "settings.json"
    settings.data = json.loads(json.dumps({"ui": {}}))
    settings.set_ui_state(
        geometry="R0VPTUVUUkVBTk" ,
        window_state="U1RBVEU=",
        left_panel_visible=False,
        right_panel_visible=True,
        selected_nav=3,
    )
    settings.save()

    restored = AppSettings.__new__(AppSettings)
    restored.path = settings.path
    restored.data = json.loads(restored.path.read_text(encoding="utf-8"))

    assert restored.get_ui_state("left_panel_visible") is False
    assert restored.get_ui_state("right_panel_visible") is True
    assert restored.get_ui_state("selected_nav") == 3
    assert restored.get_ui_state("geometry") == "R0VPTUVUUkVBTk"


def test_app_settings_merges_new_defaults_without_resetting_existing_values(tmp_path: Path) -> None:
    settings = AppSettings.__new__(AppSettings)
    settings.path = tmp_path / "settings.json"
    settings.data = {"editor": {"font_size": 22}, "ui": {"selected_nav": 2}}
    settings._merge(settings.data, {"editor": {"font_family": "Malgun Gothic"}, "ui": {"right_panel_visible": False}})
    assert settings.data["editor"]["font_size"] == 22
    assert settings.data["editor"]["font_family"] == "Malgun Gothic"
    assert settings.data["ui"]["selected_nav"] == 2
    assert settings.data["ui"]["right_panel_visible"] is False


def test_requirements_include_quality_tools() -> None:
    requirements = Path(__file__).parents[1].joinpath("requirements-dev.txt").read_text(encoding="utf-8")
    assert "pytest-qt" in requirements
    assert "mypy" in requirements
