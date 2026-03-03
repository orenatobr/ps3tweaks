"""Utilities for SSH communication and configuration persistence."""

import json
import logging
from pathlib import Path
from typing import Any

import paramiko

logger = logging.getLogger(__name__)


class PS3Connection:
    """Handle SSH/SFTP communication with a PS3 host.

    Args:
        ip: PS3 IP address.
        user: SSH username.
        password: SSH password.
    """

    def __init__(self, ip: str, user: str = "root", password: str = "") -> None:
        self.ip = ip
        self.user = user
        self.password = password
        self.ssh: paramiko.SSHClient | None = None

    def connect(self) -> bool:
        """Open an SSH connection.

        Returns:
            ``True`` if connection succeeds.

        Raises:
            ConnectionError: If the SSH session cannot be established.
        """
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.ip, username=self.user, password=self.password)
            logger.info("Connected to PS3 host", extra={"ip": self.ip, "user": self.user})
            return True
        except Exception as exc:  # pragma: no cover - paramiko error shape varies
            logger.error("Failed to connect to PS3 host", extra={"ip": self.ip, "error": str(exc)})
            raise ConnectionError(f"Failed to connect to {self.ip}: {exc}") from exc

    def disconnect(self) -> None:
        """Close the SSH connection if open."""
        if self.ssh:
            self.ssh.close()
            logger.info("Disconnected from PS3 host", extra={"ip": self.ip})

    def exec(self, cmd: str) -> tuple[str, str]:
        """Execute a command on PS3.

        Args:
            cmd: Shell command to execute remotely.

        Returns:
            A tuple with stdout and stderr content.

        Raises:
            RuntimeError: If SSH connection is not open.
        """
        if not self.ssh:
            raise RuntimeError("Not connected to PS3")

        logger.debug("Executing remote command", extra={"command": cmd})
        _, stdout, stderr = self.ssh.exec_command(cmd)
        return stdout.read().decode(), stderr.read().decode()

    def copy_to(self, local_path: str, remote_path: str) -> bool:
        """Upload a file to PS3 via SFTP.

        Args:
            local_path: Source file path on host machine.
            remote_path: Target path on PS3.

        Returns:
            ``True`` if upload succeeds.

        Raises:
            RuntimeError: If SSH connection is not open.
            OSError: If file transfer fails.
        """
        if not self.ssh:
            raise RuntimeError("Not connected to PS3")

        try:
            sftp = self.ssh.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            logger.info(
                "Uploaded file to PS3", extra={"local_path": local_path, "remote_path": remote_path}
            )
            return True
        except Exception as exc:  # pragma: no cover - paramiko error shape varies
            logger.error(
                "Failed to upload file",
                extra={"local_path": local_path, "remote_path": remote_path, "error": str(exc)},
            )
            raise OSError(f"Failed to copy file: {exc}") from exc

    def copy_from(self, remote_path: str, local_path: str) -> bool:
        """Download a file from PS3 via SFTP.

        Args:
            remote_path: Source path on PS3.
            local_path: Target file path on host machine.

        Returns:
            ``True`` if download succeeds.

        Raises:
            RuntimeError: If SSH connection is not open.
            OSError: If file transfer fails.
        """
        if not self.ssh:
            raise RuntimeError("Not connected to PS3")

        try:
            sftp = self.ssh.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            logger.info(
                "Downloaded file from PS3",
                extra={"remote_path": remote_path, "local_path": local_path},
            )
            return True
        except Exception as exc:  # pragma: no cover - paramiko error shape varies
            logger.error(
                "Failed to download file",
                extra={"remote_path": remote_path, "local_path": local_path, "error": str(exc)},
            )
            raise OSError(f"Failed to copy file: {exc}") from exc


class ConfigManager:
    """Persist and mutate JSON configuration.

    Args:
        config_file: Path to the JSON config file.
    """

    def __init__(self, config_file: Path) -> None:
        self.config_file = config_file
        self.config: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        """Load JSON configuration if present.

        Returns:
            The parsed configuration dictionary, or an empty dictionary when file
            does not exist.
        """
        if self.config_file.exists():
            with open(self.config_file, encoding="utf-8") as file_handle:
                data = json.load(file_handle)
            logger.debug("Configuration loaded", extra={"path": str(self.config_file)})
            return data
        return {}

    def save(self) -> None:
        """Write current configuration to disk."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as file_handle:
            json.dump(self.config, file_handle, indent=2)
        logger.info("Configuration saved", extra={"path": str(self.config_file)})

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Key name to retrieve.
            default: Default value returned when key does not exist.

        Returns:
            Stored value or the provided default.
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value and persist it.

        Args:
            key: Key name to update.
            value: Value to store.
        """
        self.config[key] = value
        self.save()

    def update(self, data: dict[str, Any]) -> None:
        """Update multiple values and persist them.

        Args:
            data: Mapping with keys and values to merge.
        """
        self.config.update(data)
        self.save()
