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
    elif code == "DO-03":
        items.pop(0)
    else:
        raise ValueError(f"unsupported P1 scenario: {code}")
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

    apply_scenario("DO-01")
    assert len(load_items()) == 212
    print("DO-01 added=12 PASS")
    reset()
    assert len(load_items()) == 200

    apply_scenario("DO-03")
    assert len(load_items()) == 199
    print("DO-03 removed=1 PASS")
    reset()
    assert len(load_items()) == 200
    print("2/11 PASS; fixture reset to 200 items")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--reset", action="store_true")
    action.add_argument("--verify", action="store_true")
    action.add_argument("--scenario", choices=("DO-01", "DO-03"))
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
