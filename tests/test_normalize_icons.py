"""Unit tests for normalize_icons.py."""

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from normalize_icons import FRAME_SIZE, find_images, process_image  # noqa: E402


def test_find_images_includes_avif_and_skips_appledouble(tmp_path: Path) -> None:
    """.avif covers are found; macOS AppleDouble sidecar files are ignored.

    Args:
        tmp_path: Temporary directory fixture from pytest.

    Returns:
        None.
    """
    real = tmp_path / "Game.avif"
    Image.new("RGB", (300, 200), "red").save(real, "AVIF")
    junk = tmp_path / "._Game.avif"
    junk.write_bytes(b"\x00\x05\x16\x07")  # not a real image, AppleDouble header

    found = find_images(str(tmp_path))

    assert found == [str(real)]


def test_avif_is_converted_to_png(tmp_path: Path) -> None:
    """A .avif source is decoded, normalized, and the original is removed.

    Args:
        tmp_path: Temporary directory fixture from pytest.

    Returns:
        None.
    """
    path = tmp_path / "game.avif"
    Image.new("RGB", (300, 200), "red").save(path, "AVIF")

    process_image(str(path))

    assert not path.exists()
    out_path = tmp_path / "game.png"
    assert out_path.exists()
    with Image.open(out_path) as result:
        assert result.size == (FRAME_SIZE, FRAME_SIZE)


def test_uppercase_png_extension_is_not_deleted(tmp_path: Path) -> None:
    """A same-image extension that differs only in case must survive.

    On case-insensitive filesystems (ExFAT, default macOS APFS), "Game.PNG"
    and "Game.png" are the same file; process_image must not delete it
    after overwriting it in place.

    Args:
        tmp_path: Temporary directory fixture from pytest.

    Returns:
        None.
    """
    path = tmp_path / "Game.PNG"
    Image.new("RGB", (300, 200), "red").save(path, "PNG")

    process_image(str(path))

    assert path.exists()
    with Image.open(path) as result:
        assert result.size == (FRAME_SIZE, FRAME_SIZE)


def test_lowercase_png_is_overwritten_in_place(tmp_path: Path) -> None:
    """An already-lowercase .png is resized in place, not duplicated or removed.

    Args:
        tmp_path: Temporary directory fixture from pytest.

    Returns:
        None.
    """
    path = tmp_path / "game.png"
    Image.new("RGB", (300, 200), "blue").save(path, "PNG")

    process_image(str(path))

    assert path.exists()
    assert list(tmp_path.iterdir()) == [path]


def test_jpg_is_converted_to_png_and_original_removed(tmp_path: Path) -> None:
    """A non-PNG source is converted and the original file is deleted.

    Args:
        tmp_path: Temporary directory fixture from pytest.

    Returns:
        None.
    """
    path = tmp_path / "game.jpg"
    Image.new("RGB", (300, 200), "green").save(path, "JPEG")

    process_image(str(path))

    assert not path.exists()
    out_path = tmp_path / "game.png"
    assert out_path.exists()
    with Image.open(out_path) as result:
        assert result.size == (FRAME_SIZE, FRAME_SIZE)
        assert result.mode == "RGBA"


def test_aspect_ratio_is_preserved_and_centered(tmp_path: Path) -> None:
    """A non-square source is letterboxed, not stretched, inside the frame.

    Args:
        tmp_path: Temporary directory fixture from pytest.

    Returns:
        None.
    """
    path = tmp_path / "wide.png"
    Image.new("RGB", (400, 100), "yellow").save(path, "PNG")

    process_image(str(path))

    with Image.open(path) as result:
        assert result.size == (FRAME_SIZE, FRAME_SIZE)
        # Top row should be transparent padding; a middle row should contain
        # the opaque source image.
        assert result.getpixel((FRAME_SIZE // 2, 0))[3] == 0
        assert result.getpixel((FRAME_SIZE // 2, FRAME_SIZE // 2))[3] == 255


def test_dry_run_makes_no_changes(tmp_path: Path) -> None:
    """--dry-run must not write or delete anything.

    Args:
        tmp_path: Temporary directory fixture from pytest.

    Returns:
        None.
    """
    path = tmp_path / "game.jpg"
    Image.new("RGB", (300, 200), "purple").save(path, "JPEG")

    process_image(str(path), dry_run=True)

    assert path.exists()
    assert list(tmp_path.iterdir()) == [path]
