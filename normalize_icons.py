#!/usr/bin/env python3
import argparse
import os
import sys

from PIL import Image, UnidentifiedImageError

ROOT = os.path.dirname(os.path.abspath(__file__))
FRAME_SIZE = 160
EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff", ".tif", ".avif"}
SKIP_DIRS = {".git", ".claude", "node_modules", "output", "tests"}


def find_images(root):
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fname in filenames:
            if fname.startswith("._"):
                continue
            _, ext = os.path.splitext(fname)
            if ext.lower() in EXTS:
                found.append(os.path.join(dirpath, fname))
    return found


def process_image(path, dry_run=False):
    base, ext = os.path.splitext(path)
    out_path = base + ".png"

    with Image.open(path) as raw:
        img = raw.convert("RGBA")
        img.load()

    img.thumbnail((FRAME_SIZE, FRAME_SIZE), Image.LANCZOS)

    canvas = Image.new("RGBA", (FRAME_SIZE, FRAME_SIZE), (0, 0, 0, 0))
    x = (FRAME_SIZE - img.width) // 2
    y = (FRAME_SIZE - img.height) // 2
    canvas.paste(img, (x, y), img)

    same_path = os.path.exists(out_path) and os.path.samefile(out_path, path)

    if dry_run:
        action = (
            "overwrite (already .png)"
            if same_path
            else f"-> {os.path.basename(out_path)} (original deleted)"
        )
        print(f"  [dry-run] {path} {action}")
        return

    canvas.save(out_path, "PNG")

    if not same_path:
        os.remove(path)


def main():
    parser = argparse.ArgumentParser(
        description="Normalize images into a 160x160 transparent frame, preserving aspect ratio."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List what would be done without writing or deleting anything.",
    )
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")
    args = parser.parse_args()

    images = find_images(ROOT)
    print(f"Found {len(images)} image file(s) under {ROOT}")

    if not images:
        return

    if args.dry_run:
        for path in images:
            process_image(path, dry_run=True)
        print(f"\n[dry-run] {len(images)} file(s) would be processed. No changes made.")
        return

    if not args.yes:
        prompt = (
            f"Proceed to convert {len(images)} image(s) to 160x160 PNG "
            "and delete originals (except existing .png)? [s/N] "
        )
        reply = input(prompt).strip().lower()
        if reply not in ("s", "sim", "y", "yes"):
            print("Aborted.")
            return

    converted = 0
    errors = 0
    for path in images:
        try:
            process_image(path)
            converted += 1
        except (UnidentifiedImageError, OSError) as e:
            errors += 1
            print(f"  [error] {path}: {e}", file=sys.stderr)

    print(f"\nDone. Converted: {converted}, errors: {errors}, total found: {len(images)}")


if __name__ == "__main__":
    main()
