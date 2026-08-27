#!/usr/bin/env python3
"""Reset, mutate, and verify the deterministic DriftLab fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from gen_fixture import SITE_DIR, generate_fixture, render_fixture


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_FILE = ROOT / "fixtures" / ".scenario"
SCENARIOS = tuple(f"DO-{number:02d}" for number in range(1, 12))


def reset() -> None:
    generate_fixture(1337)
    SCENARIO_FILE.unlink(missing_ok=True)


def load_items() -> list[dict[str, str]]:
    return json.loads((SITE_DIR / "items.json").read_text())


def apply_scenario(code: str) -> None:
    reset()
    items = load_items()
    if code == "DO-01":
        for number in range(201, 213):
            items.append(
                {
                    "item_id": f"DW-{number:04d}",
                    "name": f"Added Fixture Item {number:03d}",
                    "price": f"{number / 10:.2f}",
                    "category": "added",
                    "note": "DO-01 deterministic addition",
                }
            )
    elif code == "DO-02":
        for item in items[:4]:
            item["price"] = f"{float(item['price']) + 10:.2f}"
    elif code == "DO-03":
        items.pop(0)
    elif code == "DO-04":
        render_fixture(items)
        for path in [SITE_DIR / "index.html", *SITE_DIR.glob("page-*.html")]:
            path.write_text(path.read_text().replace('class="item-card"', 'class="c-9f2a1"'))
        return
    elif code == "DO-05":
        render_fixture(items)
        for item in items[:60]:
            path = SITE_DIR / "items" / f"{item['item_id']}.html"
            path.write_text(path.read_text().replace('class="item-name"', 'class="name-missing"', 1))
        return
    elif code in {"DO-06", "DO-08"}:
        SCENARIO_FILE.write_text(code)
        return
    elif code == "DO-07":
        render_fixture(items)
        path = SITE_DIR / "items" / f"{items[0]['item_id']}.html"
        path.write_text(
            path.read_text().replace(
                '<article class="item-detail"',
                '<article class="item-detail" data-promo="unexpected"',
                1,
            )
        )
        return
    elif code == "DO-09":
        SCENARIO_FILE.write_text(code)
        return
    elif code == "DO-10":
        for item in items[:80]:
            item["category"] = "restructured"
    elif code == "DO-11":
        SCENARIO_FILE.write_text(code)
        return
    else:
        raise ValueError(f"unsupported scenario: {code}")
    render_fixture(items)


def fixture_hash() -> str:
    digest = hashlib.sha256()
    for path in sorted(file for file in SITE_DIR.rglob("*") if file.is_file()):
        digest.update(path.relative_to(SITE_DIR).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def verify() -> None:
    reset()
    first_hash = fixture_hash()
    assert len(load_items()) == 200
    reset()
    second_hash = fixture_hash()
    assert first_hash == second_hash
    print(f"baseline items=200 reproducible_sha256={first_hash}")

    checks = {
        "DO-01": lambda: len(load_items()) == 212,
        "DO-02": lambda: load_items()[0]["price"] != build_baseline()[0]["price"],
        "DO-03": lambda: len(load_items()) == 199,
        "DO-04": lambda: "c-9f2a1" in (SITE_DIR / "page-1.html").read_text(),
        "DO-05": lambda: "name-missing" in (SITE_DIR / "items" / "DW-0001.html").read_text(),
        "DO-06": lambda: SCENARIO_FILE.read_text() == "DO-06",
        "DO-07": lambda: "data-promo" in (SITE_DIR / "items" / "DW-0001.html").read_text(),
        "DO-08": lambda: SCENARIO_FILE.read_text() == "DO-08",
        "DO-09": lambda: SCENARIO_FILE.read_text() == "DO-09",
        "DO-10": lambda: sum(item["category"] == "restructured" for item in load_items()) == 80,
        "DO-11": lambda: SCENARIO_FILE.read_text() == "DO-11",
    }
    for code in SCENARIOS:
        apply_scenario(code)
        assert checks[code](), code
        print(f"{code} fixture PASS")
    reset()
    print("11/11 PASS; fixture reset to 200 items")


def build_baseline() -> list[dict[str, str]]:
    generate_fixture(1337)
    return load_items()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--reset", action="store_true")
    action.add_argument("--verify", action="store_true")
    action.add_argument("--scenario", choices=SCENARIOS)
    args = parser.parse_args()
    if args.reset:
        reset()
        print("DriftLab reset to 200 items")
    elif args.verify:
        verify()
    else:
        assert args.scenario is not None
        apply_scenario(args.scenario)
        print(f"{args.scenario} applied; items={len(load_items())}")


if __name__ == "__main__":
    main()
