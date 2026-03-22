"""FTP-based cover marker utility for PS3 images.

This module downloads an image from a PS3 FTP server, overlays a completion
badge in the top-left corner, and can upload the edited image back.
"""

from __future__ import annotations

import argparse
import ftplib
import logging
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageColor, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def _parse_simple_yaml(config_text: str) -> dict[str, Any]:
    """Parse a minimal YAML subset used by this project config.

    Args:
        config_text: Raw YAML file content.

    Returns:
        Parsed dictionary with support for one nested mapping level.
    """
    root: dict[str, Any] = {}
    current_section: str | None = None

    for raw_line in config_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if not line.startswith(" "):
            if stripped.endswith(":"):
                current_section = stripped[:-1].strip()
                root[current_section] = {}
                continue

            key, _, value = stripped.partition(":")
            root[key.strip()] = _coerce_yaml_scalar(value.strip())
            current_section = None
            continue

        if current_section is None:
            continue

        nested_key, _, nested_value = stripped.partition(":")
        section = root.get(current_section)
        if isinstance(section, dict):
            section[nested_key.strip()] = _coerce_yaml_scalar(nested_value.strip())

    return root


def _coerce_yaml_scalar(raw_value: str) -> Any:
    """Convert scalar YAML-like values into Python types.

    Args:
        raw_value: Scalar value token.

    Returns:
        Best-effort typed scalar.
    """
    if not raw_value:
        return ""

    if (raw_value.startswith('"') and raw_value.endswith('"')) or (
        raw_value.startswith("'") and raw_value.endswith("'")
    ):
        return raw_value[1:-1]

    lowered = raw_value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"

    try:
        return int(raw_value)
    except ValueError:
        pass

    try:
        return float(raw_value)
    except ValueError:
        return raw_value


@dataclass(frozen=True)
class FTPSettings:
    """Store FTP connection and rendering settings.

    Attributes:
        host: PS3 host address.
        port: FTP server port.
        user: FTP username.
        password: FTP password.
        badge_ratio: Fraction of the smallest image side used as badge size.
    """

    host: str
    port: int
    user: str
    password: str
    badge_ratio: float = 0.15


def load_settings(config_path: Path) -> FTPSettings:
    """Load FTP settings from a YAML file.

    Args:
        config_path: Path to YAML config file.

    Returns:
        Parsed and validated ``FTPSettings`` instance.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If required fields are missing or invalid.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, encoding="utf-8") as file_handle:
        raw_config = _parse_simple_yaml(file_handle.read())

    ftp_config = raw_config.get("ftp", {})
    host = str(ftp_config.get("host", "")).strip()
    port = int(ftp_config.get("port", 21))
    user = str(ftp_config.get("user", "anonymous")).strip() or "anonymous"
    password = str(ftp_config.get("password", ""))
    badge_ratio = float(raw_config.get("badge_ratio", 0.15))

    if not host:
        raise ValueError("Missing required value: ftp.host")
    if port <= 0:
        raise ValueError("FTP port must be a positive integer")
    if badge_ratio <= 0 or badge_ratio >= 1:
        raise ValueError("badge_ratio must be between 0 and 1")

    return FTPSettings(
        host=host,
        port=port,
        user=user,
        password=password,
        badge_ratio=badge_ratio,
    )


def add_completion_badge(image: Image.Image, badge_ratio: float) -> Image.Image:
    """Add a completion badge to the top-left corner of an image.

    Args:
        image: Original image.
        badge_ratio: Fraction of min(width, height) used as badge box size.

    Returns:
        A new ``Image`` with a green rounded-square badge and a check mark.
    """
    if badge_ratio <= 0 or badge_ratio >= 1:
        raise ValueError("badge_ratio must be between 0 and 1")

    rendered = image.convert("RGBA")
    draw = ImageDraw.Draw(rendered)
    width, height = rendered.size

    base = min(width, height)
    badge_size = max(18, int(base * badge_ratio))
    margin = max(6, int(base * 0.02))
    x0, y0 = margin, margin
    x1, y1 = x0 + badge_size, y0 + badge_size

    draw.rounded_rectangle(
        [x0, y0, x1, y1],
        radius=max(4, badge_size // 6),
        fill=ImageColor.getrgb("#1B9E32") + (230,),
        outline=ImageColor.getrgb("#FFFFFF") + (240,),
        width=max(1, badge_size // 15),
    )

    # Draw a check shape so we do not depend on emoji-capable fonts.
    p1 = (x0 + int(badge_size * 0.22), y0 + int(badge_size * 0.55))
    p2 = (x0 + int(badge_size * 0.43), y0 + int(badge_size * 0.75))
    p3 = (x0 + int(badge_size * 0.78), y0 + int(badge_size * 0.30))
    line_width = max(2, badge_size // 9)
    draw.line([p1, p2, p3], fill=(255, 255, 255, 255), width=line_width, joint="curve")

    try:
        symbol_size = max(12, badge_size // 3)
        font = ImageFont.truetype("DejaVuSans.ttf", symbol_size)
        draw.text(
            (x0 + badge_size + margin // 2, y0),
            "DONE",
            fill=(255, 255, 255, 230),
            font=font,
        )
    except OSError:
        logger.debug("Could not load TrueType font; skipping DONE label")

    return rendered


def download_image(ftp: ftplib.FTP, remote_path: str) -> bytes:
    """Download an image file from FTP.

    Args:
        ftp: Active FTP client.
        remote_path: Remote image path.

    Returns:
        Raw file bytes.
    """
    buffer = BytesIO()
    ftp.retrbinary(f"RETR {remote_path}", buffer.write)
    return buffer.getvalue()


def upload_image(ftp: ftplib.FTP, remote_path: str, data: bytes) -> None:
    """Upload image bytes to FTP.

    Args:
        ftp: Active FTP client.
        remote_path: Remote target path.
        data: Image bytes to upload.
    """
    ftp.storbinary(f"STOR {remote_path}", BytesIO(data))


def process_remote_cover(
    config_path: Path,
    remote_path: str,
    output_path: Path,
    upload: bool = True,
) -> Path:
    """Process one remote image: download, mark complete, save, and optionally upload.

    Args:
        config_path: YAML settings file path.
        remote_path: Remote image path in the PS3 FTP server.
        output_path: Local output image path.
        upload: Whether to upload the edited image back to PS3.

    Returns:
        Local output path where the edited image was saved.
    """
    settings = load_settings(config_path)
    logger.info(
        "Starting remote cover processing",
        extra={"host": settings.host, "remote": remote_path},
    )

    with ftplib.FTP() as ftp:
        ftp.connect(settings.host, settings.port)
        ftp.login(settings.user, settings.password)
        logger.info("Connected to FTP server", extra={"host": settings.host, "port": settings.port})

        original_bytes = download_image(ftp, remote_path)
        image = Image.open(BytesIO(original_bytes))
        edited = add_completion_badge(image, settings.badge_ratio)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        edited.save(output_path)
        logger.info("Saved local edited image", extra={"path": str(output_path)})

        if upload:
            upload_buffer = BytesIO()
            fmt = image.format or "PNG"
            edited.save(upload_buffer, format=fmt)
            upload_image(ftp, remote_path, upload_buffer.getvalue())
            logger.info("Uploaded edited image back to PS3", extra={"remote": remote_path})

    return output_path


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Download a PS3 cover over FTP, mark it as completed, and upload it back."
    )
    parser.add_argument(
        "--config",
        default="config/ps3_ftp_config.yml",
        help="Path to YAML config file (default: config/ps3_ftp_config.yml)",
    )
    parser.add_argument("--remote-path", required=True, help="Remote image path on PS3 FTP")
    parser.add_argument(
        "--output",
        default="output/marked_cover.png",
        help="Local output path (default: output/marked_cover.png)",
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Do not upload the edited image back to PS3",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)",
    )
    return parser.parse_args()


def main() -> int:
    """Entry point for CLI execution.

    Returns:
        Exit code ``0`` on success, ``1`` on failure.
    """
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    try:
        process_remote_cover(
            config_path=Path(args.config),
            remote_path=args.remote_path,
            output_path=Path(args.output),
            upload=not args.no_upload,
        )
        return 0
    except Exception as exc:  # pragma: no cover - CLI top-level guard
        logger.error("Failed to process remote cover", exc_info=True)
        logger.error("Error details", extra={"error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
