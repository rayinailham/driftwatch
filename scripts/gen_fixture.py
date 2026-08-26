#!/usr/bin/env python3
"""Generate the deterministic DriftWatch local fixture."""

from __future__ import annotations

import argparse
import html
import json
import random
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "fixtures" / "site"
CATEGORIES = ("books", "garden", "home", "office", "toys")
ADJECTIVES = ("Amber", "Bright", "Calm", "Delta", "Evergreen", "Fine", "Grand", "Harbor")
NOUNS = ("Compass", "Journal", "Lamp", "Mug", "Planter", "Puzzle", "Shelf", "Toolkit")


def build_items(seed: int, count: int = 200) -> list[dict[str, str]]:
    rng = random.Random(seed)
    items = []
    for item_id in range(1, count + 1):
        items.append(
            {
                "item_id": f"DW-{item_id:04d}",
                "name": f"{rng.choice(ADJECTIVES)} {rng.choice(NOUNS)} {item_id:03d}",
                "price": f"{rng.randint(500, 25000) / 100:.2f}",
                "category": rng.choice(CATEGORIES),
                "note": f"Fixture note {rng.randint(1000, 9999)}",
            }
        )
    return items


def _card(item: dict[str, str]) -> str:
    return (
        '<article class="item-card" data-item-id="{item_id}">'
        '<h2 class="item-name"><a href="items/{item_id}.html">{name}</a></h2>'
        '<span class="price">{price}</span><span class="category">{category}</span>'
        "</article>"
    ).format(**{key: html.escape(value) for key, value in item.items()})


def _page(title: str, body: str) -> str:
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<title>{html.escape(title)}</title></head><body><main>{body}</main></body></html>\n"
    )


def render_fixture(items: list[dict[str, str]], site_dir: Path = SITE_DIR) -> None:
    shutil.rmtree(site_dir, ignore_errors=True)
    (site_dir / "items").mkdir(parents=True)
    (site_dir / "items.json").write_text(json.dumps(items, indent=2) + "\n")
    (site_dir / "robots.txt").write_text("User-agent: *\nAllow: /\n")

    pages = [items[offset : offset + 20] for offset in range(0, len(items), 20)]
    for number, page_items in enumerate(pages, 1):
        cards = "\n".join(_card(item) for item in page_items)
        (site_dir / f"page-{number}.html").write_text(_page(f"DriftLab page {number}", cards))
    (site_dir / "index.html").write_text(_page("DriftLab", "\n".join(_card(item) for item in pages[0])))

    for item in items:
        values = {key: html.escape(value) for key, value in item.items()}
        detail = (
            '<article class="item-detail" data-item-id="{item_id}">'
            '<h1 class="item-name">{name}</h1><span class="price">{price}</span>'
            '<span class="category">{category}</span><p class="note">{note}</p></article>'
        ).format(**values)
        (site_dir / "items" / f"{item['item_id']}.html").write_text(_page(item["name"], detail))


def generate_fixture(seed: int = 1337) -> None:
    render_fixture(build_items(seed))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=1337)
    args = parser.parse_args()
    generate_fixture(args.seed)
    print(f"generated 200 items in {SITE_DIR} with seed {args.seed}")


if __name__ == "__main__":
    main()
