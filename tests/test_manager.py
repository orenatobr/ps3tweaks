"""Unit and integration-style tests for PS3EmulatorManager."""

from pathlib import Path

import pytest

from ps3tweaks.manager import PS3EmulatorManager


class DummySSHConnection:
    """Minimal in-memory stub for PS3Connection behavior in tests."""

    def __init__(self, should_connect: bool = True) -> None:
        self.should_connect = should_connect
        self.ssh = None
        self.commands: list[str] = []
        self.uploads: list[tuple[str, str]] = []

    def connect(self) -> bool:
        """Simulate connection establishment.

        Returns:
            True when configured as successful.

        Raises:
            ConnectionError: If configured to fail.
        """
        if not self.should_connect:
            raise ConnectionError("connection failed")
        self.ssh = object()
        return True

    def disconnect(self) -> None:
        """Simulate disconnection."""
        self.ssh = None

    def exec(self, cmd: str) -> tuple[str, str]:
        """Simulate command execution response.

        Args:
            cmd: Command string.

        Returns:
            Tuple of stdout and stderr text.
        """
        self.commands.append(cmd)
        if "ls -lh /dev_hdd0/vmc/" in cmd:
            stdout = "-rw-r--r-- 1 root root 131072 Jan 1 00:00 /dev_hdd0/vmc/PS1_slot1.vmc\n"
            return stdout, ""
        if "ls /dev_hdd0/PSXISO/" in cmd:
            return "Metal Gear Solid.iso\n", ""
        if "ls /dev_hdd0/PS2ISO/" in cmd:
            return "God of War.iso\n", ""
        return "", ""

    def copy_to(self, local_path: str, remote_path: str) -> bool:
        """Track file upload calls.

        Args:
            local_path: Source file path.
            remote_path: Destination path.

        Returns:
            Always True.
        """
        self.uploads.append((local_path, remote_path))
        return True


@pytest.fixture
def manager(tmp_path: Path) -> PS3EmulatorManager:
    """Create manager instance with isolated config path.

    Args:
        tmp_path: Temporary test path fixture.

    Returns:
        Configured PS3EmulatorManager.
    """
    mgr = PS3EmulatorManager("192.168.0.10")
    mgr.config_manager.config_file = tmp_path / "ps3_emulator_config.json"
    mgr.config_manager.config = {}
    mgr.ssh = DummySSHConnection()
    return mgr


def test_connect_success(manager: PS3EmulatorManager) -> None:
    """Ensure connect returns True when SSH succeeds."""
    assert manager.connect() is True


def test_connect_failure(tmp_path: Path) -> None:
    """Ensure connect returns False when SSH fails."""
    mgr = PS3EmulatorManager("192.168.0.10")
    mgr.config_manager.config_file = tmp_path / "config.json"
    mgr.config_manager.config = {}
    mgr.ssh = DummySSHConnection(should_connect=False)

    assert mgr.connect() is False


def test_configure_game_persists_data(manager: PS3EmulatorManager) -> None:
    """Validate per-game configuration persistence."""
    manager.configure_game("MGS", "ps1")

    config = manager.get_game_config("MGS")
    assert config is not None
    assert config["console"] == "ps1"
    assert config["analog_mode"] is True


def test_configure_game_invalid_console(manager: PS3EmulatorManager) -> None:
    """Validate invalid console guard clause."""
    with pytest.raises(ValueError):
        manager.configure_game("MGS", "ps3")


def test_list_vmcs(manager: PS3EmulatorManager) -> None:
    """Ensure VMC parser returns filename-size mapping."""
    vmcs = manager.list_vmcs()
    assert vmcs["PS1_slot1.vmc"] == "131072"


def test_list_games(manager: PS3EmulatorManager) -> None:
    """Ensure game listing fetches values from remote responses."""
    assert manager.list_games("ps1") == ["Metal Gear Solid.iso"]
    assert manager.list_games("ps2") == ["God of War.iso"]


def test_generate_launcher_script(manager: PS3EmulatorManager) -> None:
    """Ensure launcher generation contains expected emulator markers."""
    script = manager.generate_launcher_script("ps1")
    assert "PS1_EMULATOR" in script
    assert "PS1_slot1.vmc" in script


def test_upload_launcher_scripts(manager: PS3EmulatorManager) -> None:
    """Validate upload flow for both launchers."""
    manager.ssh.ssh = object()
    success = manager.upload_launcher_scripts()

    assert success is True
    assert len(manager.ssh.uploads) == 2


def test_get_status_snapshot(manager: PS3EmulatorManager) -> None:
    """Validate status snapshot structure and values."""
    snapshot = manager.get_status_snapshot()

    assert snapshot["connected"] is True
    assert snapshot["vmcs"]["PS1_slot1.vmc"] == "131072"
    assert "Metal Gear Solid.iso" in snapshot["ps1_games"]
    assert "God of War.iso" in snapshot["ps2_games"]
