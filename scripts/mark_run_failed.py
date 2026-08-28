#!/usr/bin/env python3
"""Mark an existing run manifest failed after a pipeline stage fails."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def mark_failed(path: Path) -> None:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["exit_code"] = 1
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        mark_failed(args.path)
    except (OSError, json.JSONDecodeError) as error:
        print(f"gagal menandai run: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
