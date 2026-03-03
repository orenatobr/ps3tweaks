"""Unit tests for utility classes in ps3tweaks.utils."""

from pathlib import Path

from ps3tweaks.utils import ConfigManager


def test_config_manager_set_get_update(tmp_path: Path) -> None:
    """Validate ConfigManager persistence flow.

    Args:
        tmp_path: Temporary test path fixture from pytest.

    Returns:
        None.
    """
    config_file = tmp_path / "config.json"
    manager = ConfigManager(config_file)

    manager.set("k1", "v1")
    manager.update({"k2": 2})

    assert manager.get("k1") == "v1"
    assert manager.get("k2") == 2
    assert config_file.exists()


def test_config_manager_load_existing_file(tmp_path: Path) -> None:
    """Validate loading of existing JSON configuration.

    Args:
        tmp_path: Temporary test path fixture from pytest.

    Returns:
        None.
    """
    config_file = tmp_path / "existing.json"
    config_file.write_text('{"games": {"Test": {"console": "ps1"}}}', encoding="utf-8")

    manager = ConfigManager(config_file)

    assert manager.get("games") == {"Test": {"console": "ps1"}}
