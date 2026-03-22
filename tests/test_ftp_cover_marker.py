"""Unit tests for FTP cover marker module."""

from __future__ import annotations

import ftplib
from io import BytesIO
from pathlib import Path
from typing import Callable

import pytest
from PIL import Image

from ps3tweaks.ftp_cover_marker import (
    FTPSettings,
    add_completion_badge,
    load_settings,
    process_remote_cover,
)


def _build_test_image_bytes() -> bytes:
    """Create a simple PNG image fixture in memory.

    Returns:
        Raw PNG bytes.
    """
    image = Image.new("RGB", (120, 80), color=(20, 30, 40))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_load_settings_reads_yaml(tmp_path: Path) -> None:
    """Validate YAML parsing into FTP settings.

    Args:
        tmp_path: Temporary pytest path fixture.
    """
    config_file = tmp_path / "ps3_ftp.yml"
    config_file.write_text(
        (
            "ftp:\n"
            '  host: "192.168.0.50"\n'
            "  port: 2121\n"
            '  user: "ps3"\n'
            '  password: "secret"\n'
            "badge_ratio: 0.2\n"
        ),
        encoding="utf-8",
    )

    settings = load_settings(config_file)

    assert settings == FTPSettings(
        host="192.168.0.50",
        port=2121,
        user="ps3",
        password="secret",
        badge_ratio=0.2,
    )


def test_add_completion_badge_changes_top_left_area() -> None:
    """Ensure the badge modifies pixels in the top-left corner."""
    image = Image.new("RGB", (100, 100), color=(10, 10, 10))

    edited = add_completion_badge(image, 0.15)

    original_pixel = image.convert("RGBA").getpixel((10, 10))
    edited_pixel = edited.getpixel((10, 10))
    assert edited_pixel != original_pixel


def test_process_remote_cover_downloads_marks_and_uploads(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Validate full flow with mocked FTP backend.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        tmp_path: Temporary pytest path fixture.
    """
    original_bytes = _build_test_image_bytes()
    uploaded_payloads: list[bytes] = []

    class FakeFTP:
        """In-memory fake FTP client for deterministic tests."""

        def __enter__(self) -> FakeFTP:
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

        def connect(self, host: str, port: int) -> None:
            assert host == "127.0.0.1"
            assert port == 21

        def login(self, user: str, passwd: str) -> None:
            assert user == "anonymous"
            assert passwd == ""

        def retrbinary(self, command: str, callback: Callable[[bytes], object]) -> None:
            assert command == "RETR /dev_hdd0/game/COVER.PNG"
            callback(original_bytes)

        def storbinary(self, command: str, file_obj: BytesIO) -> None:
            assert command == "STOR /dev_hdd0/game/COVER.PNG"
            uploaded_payloads.append(file_obj.read())

    monkeypatch.setattr(ftplib, "FTP", FakeFTP)

    config_file = tmp_path / "ps3_ftp.yml"
    config_file.write_text(
        (
            "ftp:\n"
            '  host: "127.0.0.1"\n'
            "  port: 21\n"
            '  user: "anonymous"\n'
            '  password: ""\n'
            "badge_ratio: 0.15\n"
        ),
        encoding="utf-8",
    )

    output_path = tmp_path / "result.png"
    result_path = process_remote_cover(
        config_path=config_file,
        remote_path="/dev_hdd0/game/COVER.PNG",
        output_path=output_path,
        upload=True,
    )

    assert result_path == output_path
    assert output_path.exists()
    assert uploaded_payloads
