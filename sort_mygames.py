#!/usr/bin/env python3
"""Reorder the webMAN game list in mygames.xml.

Sort order: alphabetical by title, with same-franchise sequels ordered
oldest-first (Roman/Arabic numeral aware), and multi-disc releases kept
adjacent in disc order. Only the display-order <I> index inside each
<V id="seg_wm_*_items"> segment is reordered. The <T> game definitions and
their key attributes are left untouched.
"""

import argparse
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
MYGAMES_PATH = os.path.join(ROOT, "mygames.xml")
SEGMENTS = ("seg_wm_ps3_items", "seg_wm_ps2_items", "seg_wm_psx_items")

ROMAN_VALUES = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8,
    "IX": 9, "X": 10, "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
}  # fmt: skip

T_ENTRY_RE = re.compile(r'<T key="(\w+)" include="inc">(.*?)</T>', re.S)
TITLE_RE = re.compile(r'<P key="title"><>(.*?)</></P>')
I_TAG_RE = re.compile(r'<I class="type:x-xmb/module-action" key="(\w+)" attr="\w+"/>')
I_RUN_RE = re.compile(f"(?:{I_TAG_RE.pattern})+")
DISC_RE = re.compile(r"\(Disc (\d+)\)")
PAREN_RE = re.compile(r"\s*\([^)]*\)")
TRAILING_NUM_RE = re.compile(r"^(.*?)\s+([IVXLCDM]+|\d+)$")


def sort_key(title: str) -> tuple[str, int, str, int, str]:
    """Build the sort key for a game title.

    Args:
        title: Game title as shown in the webMAN list.

    Returns:
        Tuple ordering by franchise base, sequel number, subtitle, disc and title.
    """
    disc_match = DISC_RE.search(title)
    disc = int(disc_match.group(1)) if disc_match else 1

    clean = PAREN_RE.sub("", title).strip()
    # Split off a " - Subtitle" suffix (e.g. "Resistance - Fall of Man") so it
    # doesn't stop the sequel number on the head from matching its franchise
    # base, and isn't mistaken for a distinct franchise base itself.
    head, _, subtitle = clean.partition(" - ")

    m = TRAILING_NUM_RE.match(head)
    if m:
        base, num = m.group(1), m.group(2)
        if num in ROMAN_VALUES:
            franchise_num = ROMAN_VALUES[num]
        elif num.isdigit():
            franchise_num = int(num)
        else:
            base, franchise_num = head, 0
    else:
        base, franchise_num = head, 0

    return (base.lower(), franchise_num, subtitle.lower(), disc, title)


def reorder_segment(content: str, seg_id: str) -> tuple[str, list[str]]:
    """Reorder the <I> display index of one segment.

    Links whose tile has no title keep their relative order after the sorted
    ones. A segment that is absent from the file is left untouched.

    Args:
        content: Full mygames.xml text.
        seg_id: Segment id, e.g. ``seg_wm_ps3_items``.

    Returns:
        The updated content and the titles in their new order.
    """
    start = content.find(f'<V id="{seg_id}">')
    if start == -1:
        return content, []
    end = content.find("<V id=", start + 1)
    if end == -1:
        end = len(content)
    seg = content[start:end]

    titles: dict[str, str] = {}
    for key, body in T_ENTRY_RE.findall(seg):
        title_match = TITLE_RE.search(body)
        if title_match:
            titles[key] = title_match.group(1)

    run = I_RUN_RE.search(seg)
    if run is None:
        return content, []

    links = [(m.group(1), m.group(0)) for m in I_TAG_RE.finditer(run.group())]
    titled = sorted(
        (link for link in links if link[0] in titles), key=lambda link: sort_key(titles[link[0]])
    )
    untitled = [link for link in links if link[0] not in titles]
    new_run = "".join(tag for _, tag in titled + untitled)

    new_seg = seg[: run.start()] + new_run + seg[run.end() :]
    return content[:start] + new_seg + content[end:], [titles[key] for key, _ in titled]


def main() -> None:
    """Reorder mygames.xml, writing a numbered backup first."""
    parser = argparse.ArgumentParser(description="Reorder mygames.xml game list.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview the new order without writing anything."
    )
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")
    args = parser.parse_args()

    with open(MYGAMES_PATH, encoding="utf-8") as f:
        content = f.read()

    new_content = content
    previews = {}
    for seg_id in SEGMENTS:
        new_content, ordered_titles = reorder_segment(new_content, seg_id)
        previews[seg_id] = ordered_titles

    if args.dry_run:
        for seg_id, ordered_titles in previews.items():
            print(f"\n=== {seg_id} ({len(ordered_titles)} games) ===")
            for title in ordered_titles:
                print(f"  {title}")
        print("\n[dry-run] No changes written.")
        return

    if new_content == content:
        print("Already in order. No changes needed.")
        return

    if not args.yes:
        reply = input("Write reordered mygames.xml (backup will be created first)? [s/N] ")
        if reply.strip().lower() not in ("s", "sim", "y", "yes"):
            print("Aborted.")
            return

    backup_path = MYGAMES_PATH + ".bak"
    suffix = 1
    while os.path.exists(backup_path):
        backup_path = f"{MYGAMES_PATH}.bak{suffix}"
        suffix += 1
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Backup written to {backup_path}")

    with open(MYGAMES_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Wrote reordered {MYGAMES_PATH}")


if __name__ == "__main__":
    main()
