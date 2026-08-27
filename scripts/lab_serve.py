#!/usr/bin/env python3
"""Serve DriftLab on loopback with deterministic drift hooks."""

from __future__ import annotations

import hashlib
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "fixtures" / "site"
SCENARIO_FILE = ROOT / "fixtures" / ".scenario"


def bucket(path: str) -> int:
    return int.from_bytes(hashlib.sha256(path.encode()).digest()[:4], "big") % 100


class DriftLabHandler(SimpleHTTPRequestHandler):
    failed_once: set[str] = set()
    hook_lock = threading.Lock()

    def _scenario(self) -> str:
        return SCENARIO_FILE.read_text().strip() if SCENARIO_FILE.exists() else ""

    def _apply_hook(self) -> bool:
        scenario = self._scenario()
        request_bucket = bucket(self.path.split("?", 1)[0])
        if scenario == "DO-06" and request_bucket < 15:
            with self.hook_lock:
                first_failure = self.path not in self.failed_once
                self.failed_once.add(self.path)
            if first_failure:
                self.send_error(503, "DriftLab injected failure")
                return True
        if scenario == "DO-08" and request_bucket < 10:
            time.sleep(4)
        return False

    def do_GET(self) -> None:
        if not self._apply_hook():
            super().do_GET()

    def do_HEAD(self) -> None:
        if not self._apply_hook():
            super().do_HEAD()


def main() -> None:
    if not SITE_DIR.is_dir():
        raise SystemExit("fixture missing; run scripts/gen_fixture.py first")
    server = ThreadingHTTPServer(("127.0.0.1", 8100), partial(DriftLabHandler, directory=str(SITE_DIR)))
    print("DriftLab listening on http://127.0.0.1:8100", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
