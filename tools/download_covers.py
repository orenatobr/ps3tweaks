#!/usr/bin/env python3
"""
PS2 Game Covers Downloader - Final Version.

TheGamesDB (primary) + RetroArch (fallback).
No placeholders - only official covers.
"""

import logging
import sys
import time
import urllib.parse
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

import requests
from PIL import Image

logger = logging.getLogger(__name__)

API_KEY = "b16c47bb0922907dd58c4429addb4df7169c7ae3beaab7bffb1eda2b6b194227"
TGDB_BASE = "https://api.thegamesdb.net/v1"

# Supported consoles (platform_id, retroarch_name)
CONSOLES = {
    "1": {
        "name": "PlayStation 2",
        "platform_id": 11,
        "retroarch_dir": "Sony%20-%20PlayStation%202",
    },
    "2": {
        "name": "PlayStation 1",
        "platform_id": 10,
        "retroarch_dir": "Sony%20-%20PlayStation",
    },
    "3": {
        "name": "PlayStation 3",
        "platform_id": 12,
        "retroarch_dir": "Sony%20-%20PlayStation%203",
    },
    "4": {
        "name": "Nintendo 64",
        "platform_id": 3,
        "retroarch_dir": "Nintendo%20-%20Nintendo%2064",
    },
    "5": {
        "name": "Super Nintendo",
        "platform_id": 6,
        "retroarch_dir": "Nintendo%20-%20Super%20Nintendo%20Entertainment%20System",
    },
    "6": {
        "name": "Sega Genesis",
        "platform_id": 18,
        "retroarch_dir": "Sega%20-%20Genesis",
    },
}


def get_console() -> dict[str, Any]:
    """Prompt user to select a console.

    Returns:
        Dictionary containing console name, platform_id, and retroarch_dir.
    """
    logger.info("Starting console selection prompt")
    while True:
        logger.debug("Displaying console options")
        for key, console in CONSOLES.items():
            logger.debug(f"Option {key}: {console['name']}")
        user_input = input("Choose a console: ").strip()

        if user_input in CONSOLES:
            selected = CONSOLES[user_input]
            logger.info(f"Selected console: {selected['name']}")
            return selected

        logger.warning(f"Invalid option selected: {user_input}")


def get_games_directory(console_name: str) -> Path:
    """Prompt user for games directory and validate it exists.

    Args:
        console_name: Name of the console for the prompt.

    Returns:
        Validated Path to games directory.
    """
    logger.info(f"Requesting games directory for {console_name}")
    while True:
        user_input = input(f"Enter directory path for {console_name} games: ").strip()

        # Remove quotes if user pasted a path with quotes
        user_input = user_input.strip('"').strip("'")

        if not user_input:
            logger.warning("Empty path provided")
            continue

        games_dir = Path(user_input).expanduser()

        if not games_dir.exists():
            logger.warning(f"Directory not found: {games_dir}")
            continue

        if not games_dir.is_dir():
            logger.warning(f"Path is not a directory: {games_dir}")
            continue

        # Check for game files
        game_extensions = ["*.iso", "*.dec", "*.bin", "*.cue"]
        all_game_files = []
        for ext in game_extensions:
            all_game_files.extend(games_dir.glob(ext))

        game_count = len(all_game_files)
        logger.debug(f"Found {game_count} game files in {games_dir}")

        if game_count == 0:
            logger.warning(f"No game files found in {games_dir}")
            confirm = input("Continue anyway? (y/N): ").strip().lower()
            if confirm not in ["y", "yes"]:
                continue

        logger.info(f"Validated directory: {games_dir}")
        return games_dir


def clean_game_name(name: str) -> str:
    """Remove region codes, disc info, and file extensions from game name.

    Args:
        name: Game filename or title.

    Returns:
        Cleaned game name.
    """
    # First remove file extensions
    name = Path(name).stem if "." in name else name

    suffixes = [
        " (USA)",
        " (EUR)",
        " (PAL)",
        " (NTSC)",
        " (Japan)",
        " (JAP)",
        " (Disc 1)",
        " (Disc 2)",
        " (v2.00)",
        " (En,Fr,Es)",
        " (En,Ja)",
        " (T-En)",
        " (English Beta v0.9)",
        " (i)",
        " (T-En by*",
    ]

    for suffix in suffixes:
        if suffix.endswith("*"):
            prefix = suffix[:-1]
            if prefix in name:
                name = name.split(prefix)[0]
        else:
            name = name.replace(suffix, "")

    cleaned = name.strip()
    logger.debug(f"Cleaned game name: {name} -> {cleaned}")
    return cleaned


def download_from_thegamesdb(game_name: str, platform_id: int) -> Optional[Image.Image]:
    """Download cover image from TheGamesDB API.

    Args:
        game_name: Game title to search for.
        platform_id: TheGamesDB platform ID.

    Returns:
        PIL Image object if found, None otherwise.
    """
    logger.debug(f"Searching TheGamesDB for game: {game_name} (platform {platform_id})")

    # Try different name variations
    search_variations = [
        game_name,
        game_name.replace(" - ", ": "),
        game_name.split(" (")[0],  # Just base name
    ]

    # Special case for Warriors - API returns "The Warriors" not "Warriors"
    if game_name.lower().startswith("warriors"):
        search_variations.insert(1, "The Warriors")

    if " - " in game_name:
        parts = game_name.split(" - ")
        search_variations.append(parts[0])

    # Remove empty strings
    search_variations = [s for s in search_variations if s.strip()]

    for search_name in search_variations:
        if not search_name or len(search_name) < 3:
            continue

        params = {
            "apikey": API_KEY,
            "name": search_name,
            "include": "boxart",
        }

        try:
            resp = requests.get(f"{TGDB_BASE}/Games/ByGameName", params=params, timeout=10)

            if resp.status_code != 200:
                continue

            data = resp.json()
            games = data.get("data", {}).get("games", [])

            if not games:
                continue

            # Filter for selected platform ONLY
            platform_games = [g for g in games if g.get("platform") == platform_id]

            if not platform_games:
                continue

            # Score matches to find best one
            best_match = None
            best_score = 0

            for game in platform_games:
                title = game.get("game_title", "").lower()
                search_lower = search_name.lower()

                # Check if this is a special edition - reject these heavily
                special_edition_keywords = [
                    "[bundle]",
                    "[promo",
                    "[greatest",
                    "[guitar bundle]",
                    "ultimate ",
                    "platinum",
                    "[special",
                    "[limited",
                    "greatest hits",
                    "essentials",
                    "black label",
                ]

                # Skip completely if matches very specific patterns that are known bad matches
                if any(keyword in title for keyword in special_edition_keywords):
                    # Skip this game entirely - don't even score it
                    continue

                # Score based on match quality
                if title == search_lower:
                    score = 100
                elif search_lower in title:
                    score = 80
                else:
                    # Check word matches
                    search_words = set(search_lower.split())
                    title_words = set(title.split())
                    matches = len(search_words & title_words)
                    score = matches * 10

                if score > best_score:
                    best_score = score
                    best_match = game

            if not best_match or best_score <= 0:
                continue

            # Get boxart data
            boxart = data.get("include", {}).get("boxart", {})
            game_images = boxart.get("data", {})

            game_id_str = str(best_match["id"])
            if game_id_str not in game_images:
                continue

            # Find front boxart
            images = game_images[game_id_str]
            front_img = None
            for img in images:
                if img.get("type") == "boxart" and img.get("side") == "front":
                    front_img = img
                    break

            if not front_img:
                continue

            # Download image
            base_urls = boxart.get("base_url", {})
            filename = front_img.get("filename", "")
            image_url = base_urls.get("original", "") + filename

            img_resp = requests.get(image_url, timeout=10)
            if img_resp.status_code == 200:
                return Image.open(BytesIO(img_resp.content))

        except Exception:
            pass

        time.sleep(0.1)  # Rate limiting between attempts

    return None


def download_from_retroarch(
    game_name: str, retroarch_dir: str, debug: bool = False
) -> Optional[Image.Image]:
    """Download cover image from RetroArch libretro-thumbnails.

    Args:
        game_name: Game title to search for.
        retroarch_dir: RetroArch directory path (URL-encoded).
        debug: Enable debug logging for RetroArch search attempts.

    Returns:
        PIL Image object if found, None otherwise.
    """
    logger.debug(f"Searching RetroArch for game: {game_name}")

    retroarch_base = (
        f"https://raw.githubusercontent.com/libretro/libretro-thumbnails/master/{retroarch_dir}"
    )

    # Try different name variations
    name_variations = [
        game_name,
        game_name.replace(" - ", " "),
        game_name.split(" (")[0],  # Just base name without region
    ]

    for name_var in name_variations:
        if debug:
            print(f"\n    [Trying] {name_var}")
        # Try different URL patterns
        for boxart_type in ["Named_Boxarts", "Boxarts"]:
            # Encode name for URL
            url_name = urllib.parse.quote(name_var, safe="")

            url = f"{retroarch_base}/{boxart_type}/{url_name}.png"

            try:
                resp = requests.head(url, timeout=5)
                if debug:
                    print(f"      {boxart_type}: {resp.status_code}")
                if resp.status_code == 200:
                    # URL exists, download it
                    img_resp = requests.get(url, timeout=10)
                    if img_resp.status_code == 200:
                        return Image.open(BytesIO(img_resp.content))
            except Exception as exc:
                if debug:
                    error_type = type(exc).__name__
                    print(f"      {boxart_type}: ERROR - {error_type}")

    return None


def resize_with_padding(img: Image.Image, target_size: tuple[int, int] = (260, 300)) -> Image.Image:
    """Resize image to fit within target size with transparent padding.

    Preserves aspect ratio by scaling and centering within target bounds.

    Args:
        img: PIL Image to resize.
        target_size: (width, height) target dimensions. Defaults to (260, 300).

    Returns:
        Resized PIL Image with RGBA transparency.
    """

    # Convert to RGBA if needed (for transparency)
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # Calculate scaling to fit within target size
    img_ratio = img.width / img.height
    target_ratio = target_size[0] / target_size[1]

    if img_ratio > target_ratio:
        # Image is wider - scale by width
        new_width = target_size[0]
        new_height = int(new_width / img_ratio)
    else:
        # Image is taller - scale by height
        new_height = target_size[1]
        new_width = int(new_height * img_ratio)

    # Resize using high-quality resampling
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create transparent background
    background = Image.new("RGBA", target_size, (0, 0, 0, 0))

    # Calculate position to center the image
    x = (target_size[0] - new_width) // 2
    y = (target_size[1] - new_height) // 2

    # Paste resized image onto transparent background
    background.paste(img_resized, (x, y))

    return background


def main() -> None:
    """Execute cover downloader workflow.

    Prompts for console selection, game directory, and initiates download
    from TheGamesDB with RetroArch as fallback.
    """
    logger.info("Starting Game Covers Downloader")

    # Get console from user
    console = get_console()
    logger.info(f"Selected console: {console['name']}")

    # Get games directory from user
    games_dir = get_games_directory(console["name"])
    logger.info(f"Using games directory: {games_dir}")

    # Ask for debug mode
    debug_mode = input("Enable DEBUG mode for RetroArch? (y/N): ").strip().lower()
    if debug_mode in ["y", "yes"]:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("DEBUG mode enabled")

    # Scan for game files
    game_extensions = ["*.iso", "*.dec", "*.bin", "*.cue"]
    iso_files = []
    for ext in game_extensions:
        iso_files.extend(sorted(games_dir.glob(ext)))
    iso_files = sorted(set(iso_files))  # Remove duplicates and sort

    logger.info(f"Found {len(iso_files)} game files")

    if not iso_files:
        logger.error("No ISO files found!")
        sys.exit(1)

    successful = 0
    fallback_count = 0
    failed = 0

    for i, iso_file in enumerate(iso_files, 1):
        game_name = iso_file.stem
        search_name = clean_game_name(game_name)

        logger.info(f"[{i:2d}/{len(iso_files)}] Processing: {game_name}")

        # Try TheGamesDB first
        img = download_from_thegamesdb(search_name, console["platform_id"])

        if img:
            logger.debug("Found cover in TheGamesDB")
        else:
            # Fallback to RetroArch
            img = download_from_retroarch(
                search_name,
                console["retroarch_dir"],
                debug=logger.level == logging.DEBUG,
            )

            if img:
                logger.debug("Found cover in RetroArch (fallback)")
                fallback_count += 1
            else:
                logger.warning("Cover not found anywhere")
                failed += 1
                time.sleep(0.2)
                continue

        # Resize with transparent padding
        try:
            img_final = resize_with_padding(img, target_size=(260, 300))

            # Save to root with ISO name
            output_path = games_dir / f"{game_name}.png"
            img_final.save(output_path, quality=95)

            file_size = output_path.stat().st_size / 1024
            logger.info(f"Saved cover: {output_path} ({file_size:.0f}KB)")

            successful += 1

        except Exception as exc:
            logger.error(f"Error saving cover: {exc}", exc_info=True)
            failed += 1

        time.sleep(0.3)  # Rate limiting

    # Print final summary
    logger.info(f"Download complete: {successful} successful, {failed} failed")
    logger.info(f"  From TheGamesDB: {successful - fallback_count}")
    logger.info(f"  From RetroArch: {fallback_count}")
    logger.info(f"Covers saved to: {games_dir}/")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as exc:
        logger.error(f"Fatal error: {exc}", exc_info=True)
        sys.exit(1)
