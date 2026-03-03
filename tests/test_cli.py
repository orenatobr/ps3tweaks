"""Tests for CLI control flow and interactive behavior."""

from __future__ import annotations

import builtins
from collections.abc import Iterator

import pytest

import ps3tweaks.cli as cli_module


class DummyManager:
    """Simple manager stub used to isolate CLI behavior."""

    def __init__(self, ps3_ip: str, ps3_user: str = "root", ps3_pass: str = "") -> None:
        self.ps3_ip = ps3_ip
        self.ps3_user = ps3_user
        self.ps3_pass = ps3_pass

    def connect(self) -> bool:
        """Simulate successful connection."""
        return True

    def disconnect(self) -> None:
        """No-op disconnect."""

    def list_vmcs(self) -> dict[str, str]:
        """Return fixed VMC listing."""
        return {"PS1_slot1.vmc": "131072"}

    def list_games(self, console: str) -> list[str]:
        """Return deterministic game listing by console."""
        return ["A.iso"] if console == "ps1" else ["B.iso"]

    def configure_game(self, game_name: str, console: str, vmc_slot1: str | None = None) -> None:
        """No-op configure method for menu branch coverage."""

    def upload_launcher_scripts(self) -> bool:
        """Always return success for upload flow."""
        return True

    def get_status_snapshot(self) -> dict[str, object]:
        """Return fixed status payload."""
        return {
            "connected": True,
            "vmcs": {"PS1_slot1.vmc": "131072"},
            "ps1_games": ["A.iso"],
            "ps2_games": ["B.iso"],
        }


def _input_generator(values: list[str]) -> Iterator[str]:
    """Create an iterator for mocked ``input`` calls.

    Args:
        values: Ordered list of values returned by input.

    Yields:
        One value per ``input`` call.
    """
    yield from values


def test_main_exits_when_ip_missing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate early exit branch when IP is missing."""
    answers = _input_generator([""])
    monkeypatch.setattr(builtins, "input", lambda _: next(answers))

    with pytest.raises(SystemExit) as exc_info:
        cli_module.main()

    assert exc_info.value.code == 1
    output = capsys.readouterr().out
    assert "🎮 PS3 EMULATOR CONFIGURATION MANAGER" in output


def test_main_covers_menu_branches(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Run through key menu branches to maximize CLI coverage."""
    answers = _input_generator(
        [
            "192.168.0.10",  # ip
            "letmein",  # password
            "1",  # list
            "2",  # configure
            "ps1",  # console
            "Metal Gear",  # game name
            "",  # default vmc
            "3",  # upload
            "4",  # snapshot
            "5",  # exit
        ]
    )
    monkeypatch.setattr(builtins, "input", lambda _: next(answers))
    monkeypatch.setattr(cli_module, "PS3EmulatorManager", DummyManager)

    with pytest.raises(SystemExit) as exc_info:
        cli_module.main()

    assert exc_info.value.code == 0
    output = capsys.readouterr().out

    assert "Options:" in output
    assert "PS1 Games" in output
    assert "Exiting" in output
