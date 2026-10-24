"""Unit tests for sort_mygames.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sort_mygames import reorder_segment, sort_key  # noqa: E402


def _tile(key: str, title: str) -> str:
    return (
        f'<T key="{key}" include="inc"><P key="title"><>{title}</></P>'
        f'<P key="info"><>hdd0/PS3ISO</></P></T>'
    )


def _link(key: str, attr: str | None = None) -> str:
    return f'<I class="type:x-xmb/module-action" key="{key}" attr="{attr or key}"/>'


def _segment(seg_id: str, tiles: list[str], links: list[str]) -> str:
    return f'<V id="{seg_id}"><A>{"".join(tiles)}</A><I>{"".join(links)}</I></V>'


def test_sort_key_orders_sequels_oldest_first() -> None:
    """Numbered sequels sort by number, not alphabetically.

    Returns:
        None.
    """
    titles = ["Resistance 3 (USA)", "Resistance 2 (USA)", "Resistance (USA)"]

    assert sorted(titles, key=sort_key) == [
        "Resistance (USA)",
        "Resistance 2 (USA)",
        "Resistance 3 (USA)",
    ]


def test_reorder_segment_sorts_links() -> None:
    """Links are reordered by title while tiles stay untouched.

    Returns:
        None.
    """
    tiles = [_tile("0001", "Zeta"), _tile("0002", "Alpha")]
    content = _segment("seg_wm_ps3_items", tiles, [_link("0001"), _link("0002")])

    new, titles = reorder_segment(content, "seg_wm_ps3_items")

    assert titles == ["Alpha", "Zeta"]
    assert new.index('key="0002" attr') < new.index('key="0001" attr')
    assert "".join(tiles) in new


def test_reorder_segment_keeps_links_without_title() -> None:
    """A link whose tile has no title is kept, not silently dropped.

    Returns:
        None.
    """
    tiles = [_tile("0001", "Zeta"), '<T key="0003" include="inc"></T>', _tile("0002", "Alpha")]
    links = [_link("0001"), _link("0003"), _link("0002")]
    content = _segment("seg_wm_ps3_items", tiles, links)

    new, _ = reorder_segment(content, "seg_wm_ps3_items")

    assert new.count("<I class=") == 3
    assert 'key="0003"' in new


def test_reorder_segment_applies_when_attr_differs_from_key() -> None:
    """Reordering still writes when a link's attr is not equal to its key.

    Returns:
        None.
    """
    tiles = [_tile("0001", "Zeta"), _tile("0002", "Alpha")]
    content = _segment("seg_wm_ps3_items", tiles, [_link("0001", "a"), _link("0002", "b")])

    new, _ = reorder_segment(content, "seg_wm_ps3_items")

    assert new.index(_link("0002", "b")) < new.index(_link("0001", "a"))
    assert 'attr="a"' in new and 'attr="b"' in new


def test_reorder_segment_missing_segment_is_noop() -> None:
    """A segment absent from the file leaves the content unchanged.

    Returns:
        None.
    """
    content = _segment("seg_wm_ps3_items", [_tile("0001", "Alpha")], [_link("0001")])

    new, titles = reorder_segment(content, "seg_wm_ps2_items")

    assert new == content
    assert titles == []
