"""Unit tests for utility classes in ps3tweaks.utils."""

from pathlib import Path

import pytest

from ps3tweaks.utils import ConfigManager, PS3Connection


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


def test_ps3_connection_transfers_require_open_ssh() -> None:
    """Uploads and downloads must fail fast when SSH is not connected.

    Returns:
        None.
    """
    conn = PS3Connection("192.168.1.85")

    with pytest.raises(RuntimeError):
        conn.copy_to("a", "b")
    with pytest.raises(RuntimeError):
        conn.copy_from("a", "b")
