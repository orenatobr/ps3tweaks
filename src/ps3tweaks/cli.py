"""Command-line interface for PS3 Emulator Manager.

Interactive menu-based configuration and status monitoring tool for PS3
emulator setup via SSH.
"""

import logging
import sys
from typing import NoReturn

from .manager import PS3EmulatorManager

logger = logging.getLogger(__name__)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure logging for CLI runtime.

    Args:
        level: Logging level (default: INFO).
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger.info("CLI logging configured")


def prompt_connection_details() -> tuple[str, str, str]:
    """Prompt user for PS3 connection details.

    Returns:
        Tuple of (ps3_ip, ps3_user, ps3_password).
    """
    ps3_ip = input("PS3 IP (example: 192.168.1.100): ").strip()
    if not ps3_ip:
        logger.error("PS3 IP not provided")
        sys.exit(1)

    ps3_user = input("SSH username (default: root): ").strip() or "root"
    ps3_pass = input("SSH password (default: letmein): ").strip() or "letmein"

    logger.info(
        "Connection details provided",
        extra={"ip": ps3_ip, "user": ps3_user},
    )
    return ps3_ip, ps3_user, ps3_pass


def display_main_menu() -> str:
    """Display main menu and return user choice.

    Returns:
        User selection (1-5).
    """
    print("\n" + "-" * 60)
    print("Options:")
    print("  1. Connect and list (VMCs, games)")
    print("  2. Configure a specific game")
    print("  3. Generate launcher scripts")
    print("  4. Show overall status")
    print("  5. Exit")
    print("-" * 60)
    return input("\nChoose an option (1-5): ").strip()


def display_connection_data(manager: PS3EmulatorManager) -> None:
    """Display VMCs and games after connection.

    Args:
        manager: Manager instance with active connection.
    """
    try:
        vmcs = manager.list_vmcs()
        logger.info("Retrieved VMC list", extra={"count": len(vmcs)})
        print("\n📀 Memory Cards:")
        for name, size in vmcs.items():
            print(f"   {name:<30} {size}")

        ps1_games = manager.list_games("ps1")
        print(f"\n🎮 PS1 Games ({len(ps1_games)}):")
        for game in ps1_games[:10]:
            print(f"   {game}")

        ps2_games = manager.list_games("ps2")
        print(f"\n🎮 PS2 Games ({len(ps2_games)}):")
        for game in ps2_games[:10]:
            print(f"   {game}")

        manager.disconnect()
    except Exception as exc:
        logger.error("Failed to retrieve connection data", exc_info=True)
        print(f"❌ Error: {exc}")


def configure_game(manager: PS3EmulatorManager) -> None:
    """Handle game configuration flow.

    Args:
        manager: Manager instance.
    """
    console = input("Console (ps1/ps2): ").strip().lower()
    if console not in ["ps1", "ps2"]:
        logger.warning("Invalid console selection", extra={"console": console})
        print("❌ Invalid console")
        return

    game_name = input("Game name: ").strip()
    if not game_name:
        logger.warning("Empty game name provided")
        print("❌ Empty name")
        return

    vmc = input("Memory card (or press ENTER for default): ").strip() or None

    try:
        manager.configure_game(game_name, console, vmc)
        logger.info("Game configured", extra={"game": game_name, "console": console})
        print(f"✅ Configured: {game_name}")
    except Exception as exc:
        logger.error("Failed to configure game", extra={"game": game_name, "error": str(exc)})
        print(f"❌ Error: {exc}")


def main() -> NoReturn:
    """Run the interactive CLI menu.

    Raises:
        SystemExit: When user exits the menu.
    """
    configure_logging()

    print("\n" + "=" * 60)
    print("🎮 PS3 EMULATOR CONFIGURATION MANAGER")
    print("=" * 60 + "\n")

    ps3_ip, ps3_user, ps3_pass = prompt_connection_details()

    manager = PS3EmulatorManager(ps3_ip, ps3_user, ps3_pass)
    logger.info("Manager initialized", extra={"ip": ps3_ip})

    while True:
        choice = display_main_menu()

        if choice == "1":
            logger.info("User selected: list VMCs and games")
            if manager.connect():
                display_connection_data(manager)
            else:
                logger.error("Failed to connect to PS3")
                print("❌ Could not connect to PS3")

        elif choice == "2":
            logger.info("User selected: configure game")
            configure_game(manager)

        elif choice == "3":
            logger.info("User selected: upload launcher scripts")
            if manager.connect():
                success = manager.upload_launcher_scripts()
                if success:
                    logger.info("Launcher scripts uploaded successfully")
                    print("✅ Launcher scripts uploaded")
                else:
                    logger.error("Failed to upload launcher scripts")
                    print("❌ Failed to upload scripts")
                manager.disconnect()
            else:
                logger.error("Failed to connect to PS3")
                print("❌ Could not connect to PS3")

        elif choice == "4":
            logger.info("User selected: show status")
            snapshot = manager.get_status_snapshot()
            if not snapshot["connected"]:
                logger.warning("Could not connect to PS3 for status")
                print("❌ Could not connect to PS3")
                continue

            print("\n📀 Memory Cards:")
            for name, size in snapshot["vmcs"].items():
                print(f"   {name:<30} {size}")

            ps1_games = snapshot["ps1_games"]
            print(f"\n🎮 PS1 Games ({len(ps1_games)}):")
            for game in ps1_games[:10]:
                print(f"   {game}")

            ps2_games = snapshot["ps2_games"]
            print(f"\n🎮 PS2 Games ({len(ps2_games)}):")
            for game in ps2_games[:10]:
                print(f"   {game}")

        elif choice == "5":
            logger.info("User exiting CLI")
            print("\n👋 Exiting...")
            sys.exit(0)

        else:
            logger.warning("Invalid menu selection", extra={"choice": choice})
            print("❌ Invalid option")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("CLI interrupted by user")
        print("\n\n⏸️ Interrupted")
        sys.exit(0)
    except Exception as exc:
        logger.error("Fatal error in CLI", exc_info=True)
        print(f"\n❌ Fatal error: {exc}")
        sys.exit(1)
