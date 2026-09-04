#!/usr/bin/env python3
"""Pemindai kebocoran rahasia DriftWatch — gerbang `make audit` (D19).

Memisahkan dua kelas temuan, karena menyamakannya membuat audit ini tidak berguna:

RAHASIA   kunci API, token, password. **Wajib 0.** Satu temuan → exit 1.
IDENTITAS nilai yang memang sengaja tampak: User-Agent jujur berisi kontak (D3 mewajibkannya),
          nomor port fixture lokal, zona waktu, nama akun demo lokal. Dilaporkan supaya
          terlihat sebelum repo dibuka publik (D20), tetapi **tidak** menggagalkan audit.

Yang diperiksa:
  1. Nilai non-kosong dari `.env` yang muncul di berkas ter-track git.
  2. Pola kunci pihak ketiga (Anthropic, AWS, GitHub, Slack, kunci privat PEM, URL ber-password).
  3. Berkas sensitif yang ter-track git (`.env`, `data/`, `reports/`, `auth/`, `*.db`, `logs/`).
  4. Riwayat commit — pola kunci yang pernah masuk lalu dihapus tetap terbaca di `git log -p`.

Keluar 0 hanya kalau kelas RAHASIA nol di keempat pemeriksaan.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Nama variabel .env yang isinya diperlakukan sebagai RAHASIA.
SECRET_NAME = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|PASSWD|PASS|CREDENTIAL|AUTH)$")

# Pola kunci pihak ketiga. Sengaja menuntut panjang minimum supaya nama variabel
# kosong (`ANTHROPIC_API_KEY=`) atau contoh placeholder tidak dihitung temuan.
KEY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Anthropic API key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("OpenAI API key", re.compile(r"sk-[A-Za-z0-9]{32,}")),
    ("AWS access key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}")),
    ("Slack token", re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}")),
    ("kunci privat PEM", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("URL berisi password", re.compile(r"[a-z][a-z0-9+.\-]*://[^\s/:@]+:[^\s/@]{3,}@")),
]

SENSITIVE_TRACKED = [
    re.compile(r"^\.env$"),
    re.compile(r"^data/"),
    re.compile(r"^reports/"),
    re.compile(r"^auth/"),
    re.compile(r"^logs/"),
    re.compile(r"\.db$"),
    re.compile(r"\.session$"),
]

# Berkas yang memang berisi pola-pola itu sebagai *definisi pemindai*, bukan sebagai rahasia.
SELF = {"scripts/secret_audit.py"}


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, errors="replace"
    )
    return result.stdout if result.returncode == 0 else ""


SKIP_DIRS = {
    ".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", ".serena",
    ".playwright-mcp", "data", "reports", "logs",
}
SKIP_SUFFIX = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mkv", ".pdf", ".xlsx",
    ".zip", ".gz", ".db", ".pyc", ".ttf", ".woff", ".woff2", ".ico",
}


def walked_files() -> list[str]:
    """Fallback ketika direktori bukan repo git — salinan bersih A11 persis begitu."""
    found = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if set(relative.parts[:-1]) & SKIP_DIRS or relative.parts[0] in SKIP_DIRS:
            continue
        if relative.suffix in SKIP_SUFFIX:
            continue
        if relative.parts[:2] == ("fixtures", "site"):
            continue
        found.append(str(relative))
    return found


def scanned_files() -> tuple[list[str], str]:
    """Berkas yang diperiksa, plus mode pemindaian yang dipakai.

    Repo git → hanya berkas ter-track, karena itulah yang benar-benar terkirim.
    Bukan repo git → seluruh pohon kerja. Tanpa fallback ini, `make audit` di salinan
    bersih (yang memang tidak punya `.git`) memindai NOL berkas dan tetap melapor LULUS —
    gerbang yang selalu hijau adalah gerbang yang tidak menjaga apa pun.
    """
    tracked = [line for line in git("ls-files").splitlines() if line]
    if tracked:
        return tracked, "git ls-files (berkas ter-track)"
    return walked_files(), "walk pohon kerja (bukan repo git)"


def read(path: str) -> str | None:
    try:
        return (ROOT / path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def env_values() -> list[tuple[str, str, str]]:
    """[(nama, nilai, kelas)] untuk tiap baris .env yang punya nilai."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return []
    entries = []
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name, value = name.strip(), value.strip()
        if not value:
            continue
        kelas = "RAHASIA" if SECRET_NAME.search(name) else "IDENTITAS"
        entries.append((name, value, kelas))
    return entries


def main() -> int:
    files, mode = scanned_files()
    contents = {path: read(path) for path in files}
    secret_findings: list[str] = []
    identity_findings: list[str] = []

    print("DriftWatch — audit kebocoran rahasia")
    print(f"repo: {ROOT}")
    print(f"berkas dipindai: {len(files)}  ({mode})")
    if not files:
        print("\nGAGAL — nol berkas dipindai; audit yang tidak melihat apa pun tidak sah.")
        return 1

    # 1. nilai .env
    print("\n[1] Nilai dari .env yang muncul di berkas yang dipindai")
    entries = env_values()
    for name, value, kelas in entries:
        hits = [p for p, text in contents.items() if text and value in text and p != ".env"]
        line = f"  {kelas:9s} {name:20s} {len(hits)} berkas"
        if hits:
            line += ": " + ", ".join(sorted(hits)[:6]) + (" …" if len(hits) > 6 else "")
        print(line)
        if hits:
            (secret_findings if kelas == "RAHASIA" else identity_findings).append(
                f"{name} muncul di {len(hits)} berkas"
            )
    env_path = ROOT / ".env"
    if env_path.exists():
        declared = [
            l.split("=", 1)[0].strip()
            for l in env_path.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.strip().startswith("#") and "=" in l
        ]
        for name in declared:
            if name not in [n for n, _, _ in entries]:
                print(f"  {'—':9s} {name:20s} kosong, tidak ada nilai untuk bocor")
    else:
        print("  .env tidak ada — tidak ada nilai untuk dibandingkan")

    # 2. pola kunci pihak ketiga
    print("\n[2] Pola kunci pihak ketiga di berkas yang dipindai")
    pattern_hits = 0
    for label, pattern in KEY_PATTERNS:
        for path, text in contents.items():
            if not text or path in SELF:
                continue
            for match in pattern.finditer(text):
                pattern_hits += 1
                shown = match.group(0)[:12]
                print(f"  RAHASIA   {label}: {path} → {shown}…")
                secret_findings.append(f"{label} di {path}")
    if pattern_hits == 0:
        print("  RAHASIA   nihil — 0 kecocokan untuk 7 pola")

    # 3. berkas sensitif ter-track
    #
    # Pemeriksaan ini SELALU bertanya ke git, bukan ke daftar `files`: yang berbahaya
    # adalah berkas yang ikut terkirim ke remote, bukan berkas yang kebetulan ada di
    # direktori kerja. Salinan bersih A11 memang WAJIB punya `.env` supaya pipeline jalan;
    # menyebutnya kebocoran hanya karena ia ada di disk adalah temuan palsu.
    print("\n[3] Berkas sensitif yang ter-track git")
    tracked = [line for line in git("ls-files").splitlines() if line]
    if tracked:
        tracked_sensitive = [p for p in tracked if any(r.search(p) for r in SENSITIVE_TRACKED)]
        if tracked_sensitive:
            for path in tracked_sensitive:
                print(f"  RAHASIA   ter-track: {path}")
                secret_findings.append(f"berkas sensitif ter-track: {path}")
        else:
            print("  RAHASIA   nihil — .env, data/, reports/, auth/, logs/, *.db, *.session bersih")
    else:
        print("  —         bukan repo git; tidak ada yang ter-track. Yang diperiksa: .gitignore")
        ignore = ROOT / ".gitignore"
        rules = ignore.read_text(encoding="utf-8").splitlines() if ignore.exists() else []
        wanted = [".env", "data/", "reports/", "auth/", "logs/", "*.db"]
        missing = [w for w in wanted if w not in [r.strip() for r in rules]]
        if missing:
            print(f"  RAHASIA   .gitignore tidak memuat: {', '.join(missing)}")
            secret_findings.append(f".gitignore tidak memuat {', '.join(missing)}")
        else:
            print(f"  RAHASIA   nihil — .gitignore memuat {', '.join(wanted)}")

    # 4. riwayat commit
    print("\n[4] Riwayat commit (pola kunci yang pernah masuk lalu dihapus)")
    history = git("log", "-p", "--all", "--no-color")
    if not history:
        print("  —         riwayat tidak terbaca (bukan repo git?), dilewati")
    else:
        history_hits = 0
        for label, pattern in KEY_PATTERNS:
            found = pattern.findall(history)
            if found:
                history_hits += len(found)
                print(f"  RAHASIA   {label}: {len(found)} kemunculan di riwayat")
                secret_findings.append(f"{label} di riwayat commit")
        if history_hits == 0:
            print(f"  RAHASIA   nihil — {len(history.splitlines())} baris diff diperiksa, 0 kecocokan")

    print("\n" + "=" * 62)
    print(f"KELAS RAHASIA   : {len(secret_findings)} kebocoran")
    print(f"KELAS IDENTITAS : {len(identity_findings)} nilai tampak (tidak menggagalkan audit)")
    for item in identity_findings:
        print(f"  · {item}")
    if identity_findings:
        print("  Semuanya disengaja: D3 mewajibkan User-Agent jujur berisi kontak, dan")
        print("  port fixture serta zona waktu bukan rahasia. Ditampilkan supaya terlihat")
        print("  sebelum repo dibuka publik (D20).")
    if secret_findings:
        print("\nGAGAL — kebocoran kelas RAHASIA:")
        for item in secret_findings:
            print(f"  · {item}")
        return 1
    print("\nLULUS — 0 kebocoran kelas RAHASIA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
