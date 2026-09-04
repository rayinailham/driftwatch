"""Konfigurasi runtime dari `.env`, dipakai bersama oleh scraper dan penerbit halaman.

Dua hal yang dibaca dari sini:

- `load_env` — memuat `KEY=VALUE` dari `.env` tanpa menimpa variabel lingkungan asli,
  supaya `LAB_PORT=8101 make all` selalu menang atas isi `.env`.
- `apply_lab_port` — memindahkan port fixture lokal di `recon/driftlab.json` ke `LAB_PORT`.
  Tanpa ini, salinan bersih A11 wajib memakai `8100` dan akan menabrak fixture milik
  run harian di mesin yang sama (D8: salinan bersih memakai 8101).
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse

DEFAULT_LAB_PORT = 8100
LOCAL_HOSTS = {"127.0.0.1", "localhost"}


def load_env(root: Path) -> None:
    """Read KEY=VALUE lines from .env without clobbering real environment vars."""
    env_path = root / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def lab_port() -> int:
    """Port fixture DriftLab: `LAB_PORT` kalau sah, selain itu 8100."""
    raw = os.environ.get("LAB_PORT", "").strip()
    if not raw.isdigit():
        return DEFAULT_LAB_PORT
    port = int(raw)
    return port if 1 <= port <= 65535 else DEFAULT_LAB_PORT


def is_local(url: str) -> bool:
    return urlparse(url).hostname in LOCAL_HOSTS


def _swap_port(url: str, port: int) -> str:
    parsed = urlparse(url)
    if parsed.hostname not in LOCAL_HOSTS:
        return url
    return urlunparse(parsed._replace(netloc=f"{parsed.hostname}:{port}"))


def apply_lab_port(recon: dict, port: int | None = None) -> dict:
    """Tulis ulang URL loopback di recon ke `LAB_PORT`. Recon non-lokal tidak disentuh."""
    if not is_local(recon.get("base_url", "")):
        return recon
    target_port = lab_port() if port is None else port
    recon["base_url"] = _swap_port(recon["base_url"], target_port)
    pagination = recon.get("pagination")
    if isinstance(pagination, dict) and "url_template" in pagination:
        pagination["url_template"] = _swap_port(pagination["url_template"], target_port)
    api = recon.get("api")
    if isinstance(api, dict) and "endpoint" in api:
        api["endpoint"] = _swap_port(api["endpoint"], target_port)
    sitemap = recon.get("sitemap")
    if isinstance(sitemap, dict) and isinstance(sitemap.get("urls"), list):
        sitemap["urls"] = [_swap_port(u, target_port) for u in sitemap["urls"]]
    return recon
