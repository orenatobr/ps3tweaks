"""Unit tests for PS3Connection transport behavior."""

from __future__ import annotations

from typing import Any

import pytest

from ps3tweaks import utils
from ps3tweaks.utils import PS3Connection


class _DummyChannel:
    """Minimal readable channel used by dummy SSH exec results."""

    def __init__(self, payload: str) -> None:
        self._payload = payload.encode()

    def read(self) -> bytes:
        """Return encoded payload.

        Returns:
            Encoded bytes payload.
        """
        return self._payload


class _DummySFTP:
    """Minimal SFTP stub for file copy tests."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    def put(self, local_path: str, remote_path: str) -> None:
        """Simulate upload operation."""
        if self.fail:
            raise RuntimeError("upload failed")

    def get(self, remote_path: str, local_path: str) -> None:
        """Simulate download operation."""
        if self.fail:
            raise RuntimeError("download failed")

    def close(self) -> None:
        """No-op close method."""


class _DummySSHClient:
    """Minimal paramiko SSHClient replacement for deterministic tests."""

    def __init__(self, should_fail_connect: bool = False, sftp_fail: bool = False) -> None:
        self.should_fail_connect = should_fail_connect
        self.sftp_fail = sftp_fail
        self.connected = False

    def set_missing_host_key_policy(self, _policy: Any) -> None:
        """No-op policy setter."""

    def connect(self, ip: str, username: str, password: str) -> None:
        """Simulate SSH connection."""
        if self.should_fail_connect:
            raise RuntimeError("connect failed")
        self.connected = True

    def close(self) -> None:
        """Close connection state."""
        self.connected = False

    def exec_command(self, cmd: str) -> tuple[None, _DummyChannel, _DummyChannel]:
        """Return deterministic stdout/stderr payload."""
        return None, _DummyChannel("out"), _DummyChannel("err")

    def open_sftp(self) -> _DummySFTP:
        """Return dummy SFTP session."""
        return _DummySFTP(fail=self.sftp_fail)


def test_exec_requires_connection() -> None:
    """Validate RuntimeError when executing without connection."""
    connection = PS3Connection("127.0.0.1")
    with pytest.raises(RuntimeError):
        connection.exec("echo hi")


def test_connect_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate successful connection path."""

    monkeypatch.setattr(utils.paramiko, "SSHClient", lambda: _DummySSHClient())
    connection = PS3Connection("127.0.0.1")

    assert connection.connect() is True
    connection.disconnect()


def test_connect_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate ConnectionError on SSH connection failure."""

    monkeypatch.setattr(
        utils.paramiko, "SSHClient", lambda: _DummySSHClient(should_fail_connect=True)
    )
    connection = PS3Connection("127.0.0.1")

    with pytest.raises(ConnectionError):
        connection.connect()


def test_exec_copy_to_copy_from_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate command execution and transfer success paths."""

    monkeypatch.setattr(utils.paramiko, "SSHClient", lambda: _DummySSHClient())
    connection = PS3Connection("127.0.0.1")
    connection.connect()

    stdout, stderr = connection.exec("echo hi")
    assert stdout == "out"
    assert stderr == "err"

    assert connection.copy_to("local", "remote") is True
    assert connection.copy_from("remote", "local") is True


def test_copy_failures_raise_oserror(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate transfer error conversion to OSError."""

    monkeypatch.setattr(utils.paramiko, "SSHClient", lambda: _DummySSHClient(sftp_fail=True))
    connection = PS3Connection("127.0.0.1")
    connection.connect()

    with pytest.raises(OSError):
        connection.copy_to("local", "remote")

    with pytest.raises(OSError):
        connection.copy_from("remote", "local")
