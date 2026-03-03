"""High-level manager for PS3 emulator configuration workflows."""

from __future__ import annotations

import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from .config import PS1_DEFAULT, PS2_DEFAULT
from .utils import ConfigManager, PS3Connection

logger = logging.getLogger(__name__)


class PS3EmulatorManager:
    """Manage emulator defaults and PS3 script deployment.

    Args:
        ps3_ip: Target PS3 IP address.
        ps3_user: SSH username.
        ps3_pass: SSH password.
    """

    PS3_VMC_PATH = "/dev_hdd0/vmc/"
    PS3_CONFIG_PATH = "/dev_hdd0/ps3tweaks/"
    PSXISO_PATH = "/dev_hdd0/PSXISO/"
    PS2ISO_PATH = "/dev_hdd0/PS2ISO/"

    def __init__(self, ps3_ip: str, ps3_user: str = "root", ps3_pass: str = "") -> None:
        self.ps3_ip = ps3_ip
        self.ps3_user = ps3_user
        self.ps3_pass = ps3_pass
        self.ssh = PS3Connection(ps3_ip, ps3_user, ps3_pass)

        config_dir = Path(__file__).parent.parent.parent / "config"
        config_file = config_dir / "ps3_emulator_config.json"
        self.config_manager = ConfigManager(config_file)

    def connect(self) -> bool:
        """Connect to PS3 via SSH.

        Returns:
            ``True`` when connection succeeds, otherwise ``False``.
        """
        try:
            self.ssh.connect()
            logger.info("Connected to PS3", extra={"ip": self.ps3_ip})
            return True
        except ConnectionError:
            logger.error("Could not connect to PS3", extra={"ip": self.ps3_ip})
            return False

    def disconnect(self) -> None:
        """Disconnect from PS3."""
        self.ssh.disconnect()

    def list_vmcs(self) -> dict[str, str]:
        """List available VMC files.

        Returns:
            Mapping of ``filename -> size`` as parsed from ``ls -lh`` output.
        """
        try:
            command = f"ls -lh {self.PS3_VMC_PATH}*.vmc 2>/dev/null || echo ''"
            stdout, _ = self.ssh.exec(command)
            vmc_files: dict[str, str] = {}

            for line in stdout.strip().splitlines():
                parts = line.split()
                if len(parts) >= 9 and ".vmc" in parts[-1]:
                    filename = parts[-1].split("/")[-1]
                    vmc_files[filename] = parts[4]

            logger.info("Listed VMC files", extra={"count": len(vmc_files)})
            return vmc_files
        except Exception as exc:  # pragma: no cover - depends on remote host state
            logger.error("Failed to list VMC files", extra={"error": str(exc)})
            return {}

    def list_games(self, console: str) -> list[str]:
        """List game images for a console type.

        Args:
            console: ``ps1`` or ``ps2``.

        Returns:
            A list of ISO file names.
        """
        iso_path = self.PSXISO_PATH if console == "ps1" else self.PS2ISO_PATH
        try:
            command = f"ls {iso_path} 2>/dev/null | grep -E '\\.(iso|dec|bin)$' || echo ''"
            stdout, _ = self.ssh.exec(command)
            games = [item.strip() for item in stdout.strip().splitlines() if item.strip()]
            logger.info("Listed games", extra={"console": console, "count": len(games)})
            return games
        except Exception as exc:  # pragma: no cover - depends on remote host state
            logger.error("Failed to list games", extra={"console": console, "error": str(exc)})
            return []

    def configure_game(self, game_name: str, console: str, vmc_slot1: str | None = None) -> None:
        """Persist settings for a specific game.

        Args:
            game_name: Display name used as configuration key.
            console: ``ps1`` or ``ps2``.
            vmc_slot1: Optional memory card override for slot 1.

        Raises:
            ValueError: If ``console`` is not supported.
        """
        if console not in {"ps1", "ps2"}:
            raise ValueError("Console must be 'ps1' or 'ps2'")

        games = self.config_manager.get("games", {})
        default_vmc = (
            PS1_DEFAULT.memory_card_slot1 if console == "ps1" else PS2_DEFAULT.memory_card_slot1
        )

        games[game_name] = {
            "console": console,
            "memory_card_slot1": vmc_slot1 or default_vmc,
            "video_mode": "normal" if console == "ps1" else "fullscreen",
            "analog_mode": console == "ps1",
        }

        self.config_manager.set("games", games)
        logger.info(
            "Game configuration saved",
            extra={"game_name": game_name, "console": console, "vmc": vmc_slot1 or default_vmc},
        )

    def get_game_config(self, game_name: str) -> dict[str, Any] | None:
        """Retrieve a game-specific configuration.

        Args:
            game_name: Configuration key for the game.

        Returns:
            The configuration dictionary if present, otherwise ``None``.
        """
        games = self.config_manager.get("games", {})
        config = games.get(game_name)
        logger.debug(
            "Retrieved game config", extra={"game_name": game_name, "found": config is not None}
        )
        return config

    def generate_launcher_script(self, console: str) -> str:
        """Generate a shell launcher script for a console.

        Args:
            console: ``ps1`` or ``ps2``.

        Returns:
            Script contents as a string.

        Raises:
            ValueError: If ``console`` is invalid.
        """
        if console not in {"ps1", "ps2"}:
            raise ValueError("Console must be 'ps1' or 'ps2'")

        return f"""#!/bin/bash
# PS3 Emulator Auto-Configurator - {console.upper()}
# Generated - DO NOT EDIT MANUALLY

CONSOLE=\"{console}\"
PS1_EMULATOR=\"/usr/lib64/ps1_netemu.self\"
PS2_EMULATOR=\"/usr/lib64/ps2_netemu.self\"
VMC_PATH=\"/dev_hdd0/vmc/\"

mount_memory_card() {{
    local source=$1
    local slot=$2

    if [ ! -f \"$source\" ]; then
        echo \"ERROR: Memory card not found: $source\"
        return 1
    fi

    ln -sf \"$source\" \"$VMC_PATH/slot$slot.vmc\" || return 1
    return 0
}}

set_video_mode() {{
    local mode=$1
    echo \"Configuring video mode: $mode\"
}}

main() {{
    mkdir -p /dev_hdd0/ps3tweaks/

    case \"$CONSOLE\" in
        ps1)
            mount_memory_card \"$VMC_PATH/PS1_slot1.vmc\" 1
            set_video_mode normal
            exec \"$PS1_EMULATOR\"
            ;;
        ps2)
            mount_memory_card \"$VMC_PATH/PS2_slot1.vmc\" 1
            set_video_mode fullscreen
            exec \"$PS2_EMULATOR\"
            ;;
        *)
            echo \"ERROR: Unknown console\"
            exit 1
            ;;
    esac
}}

main \"$@\"
"""

    def upload_launcher_scripts(self) -> bool:
        """Upload PS1/PS2 launcher scripts to PS3.

        Returns:
            ``True`` when both scripts are uploaded and made executable.
        """
        if not self.ssh.ssh:
            logger.error("Cannot upload scripts: SSH is not connected")
            return False

        try:
            self.ssh.exec(f"mkdir -p {self.PS3_CONFIG_PATH}")

            for console in ("ps1", "ps2"):
                script_content = self.generate_launcher_script(console)
                with NamedTemporaryFile(
                    mode="w", suffix=f"_{console}.sh", delete=False, encoding="utf-8"
                ) as temp_file:
                    temp_file.write(script_content)
                    temp_path = temp_file.name

                remote_path = f"{self.PS3_CONFIG_PATH}launcher_{console}.sh"
                self.ssh.copy_to(temp_path, remote_path)
                self.ssh.exec(f"chmod +x {remote_path}")
                Path(temp_path).unlink(missing_ok=True)
                logger.info(
                    "Launcher uploaded", extra={"console": console, "remote_path": remote_path}
                )

            return True
        except Exception as exc:  # pragma: no cover - depends on remote host state
            logger.error("Failed to upload launchers", extra={"error": str(exc)})
            return False

    def get_status_snapshot(self) -> dict[str, Any]:
        """Build a status snapshot for CLI display.

        Returns:
            A dictionary with VMC and game listing data.
        """
        snapshot: dict[str, Any] = {
            "connected": False,
            "vmcs": {},
            "ps1_games": [],
            "ps2_games": [],
        }

        if self.connect():
            snapshot["connected"] = True
            snapshot["vmcs"] = self.list_vmcs()
            snapshot["ps1_games"] = self.list_games("ps1")
            snapshot["ps2_games"] = self.list_games("ps2")
            self.disconnect()

        return snapshot
