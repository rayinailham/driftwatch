"""Production scraper CLI generated from DriftWatch recon files."""

import asyncio
import json
import logging
import subprocess
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import httpx
import typer
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from contracts import CONTRACTS
from engines.http_html import detail_links, parse_detail, parse_seo
from engines.http_json import parse_quotes
from store import Store
from validate import SchemaUnknownField, content_hash, make_record_id, validate_record

UA = "DriftWatch/1.0 (+mailto:rayinailham9@gmail.com)"
RETRYABLE_STATUSES = {429, 500, 502, 503, 504}
PUBLIC_MAX_CONCURRENCY = 3
JAKARTA = ZoneInfo("Asia/Jakarta")
log = logging.getLogger("driftwatch.scrape")
app = typer.Typer(add_completion=False)


class RetryableResponse(Exception):
    pass


class Fetcher:
    def __init__(self, client: httpx.AsyncClient, delay: float, concurrency: int):
        self.client = client
        self.delay = delay
        self.semaphore = asyncio.Semaphore(concurrency)
        self.rate_lock = asyncio.Lock()
        self.last_request_started: float | None = None
        self.gaps_ms: list[float] = []
        self.status_counts: Counter[str] = Counter()
        self.retries = 0

    async def fetch(self, url: str, params: dict | None = None) -> httpx.Response:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(4),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type((httpx.TransportError, RetryableResponse)),
            before_sleep=self._before_sleep,
            reraise=True,
        ):
            with attempt:
                async with self.semaphore:
                    await self._wait_for_slot()
                    response = await self.client.get(url, params=params)
                    self.status_counts[str(response.status_code)] += 1
                    if response.status_code in RETRYABLE_STATUSES:
                        raise RetryableResponse(f"HTTP {response.status_code}: {response.url}")
                    return response
        raise RuntimeError("retry loop selesai tanpa respons")

    async def _wait_for_slot(self) -> None:
        async with self.rate_lock:
            now = time.monotonic()
            if self.last_request_started is not None:
                await asyncio.sleep(max(0.0, self.delay - (now - self.last_request_started)))
                now = time.monotonic()
                self.gaps_ms.append((now - self.last_request_started) * 1000)
            self.last_request_started = now

    def _before_sleep(self, retry_state: Any) -> None:
        self.retries += 1
        log.warning("RETRY attempt=%s error=%s", retry_state.attempt_number, retry_state.outcome.exception())

    @property
    def observed_min_gap_ms(self) -> int | None:
        return round(min(self.gaps_ms)) if self.gaps_ms else None


class Run:
    def __init__(
        self,
        target: str,
        recon: dict,
        directory: Path,
        resume: bool,
        delay: float,
        policy_delay: float,
        concurrency: int,
    ):
        self.target = target
        self.recon = recon
        self.directory = directory
        self.resume = resume
        self.delay = delay
        self.policy_delay = policy_delay
        self.concurrency = concurrency
        self.started = datetime.now(JAKARTA)
        self.run_id = self.started.strftime("%Y-%m-%dT%H-%M-%S")
        self.store = Store(directory / "progress.db")
        self.records_path = directory / "records.jsonl"
        self.records_written = 0
        self.duplicates_rejected = 0
        self.pages_fetched = 0
        self.errors = 0
        self.schema_unknown_fields: set[str] = set()
        self.fetcher: Fetcher | None = None

    async def execute(self, limit: int | None) -> None:
        headers = {"User-Agent": UA, "Accept": "application/json" if self.target == "quotes" else "text/html"}
        async with httpx.AsyncClient(headers=headers, timeout=30, follow_redirects=True) as client:
            self.fetcher = Fetcher(client, self.delay, self.concurrency)
            with self.records_path.open("a", encoding="utf-8") as output:
                if self.target == "quotes":
                    await self._quotes(limit, output)
                elif self.target == "seo":
                    await self._seo(limit, output)
                else:
                    await self._detail_target(limit, output)

    async def _quotes(self, limit: int | None, output: Any) -> None:
        fetcher = self._fetcher()
        maximum = self.recon["pagination"]["max_page_observed"]
        for page in range(1, min(maximum, limit or maximum) + 1):
            key = f"page:{page}"
            if self.resume and self.store.done(key):
                continue
            url = self.recon["api"]["endpoint"]
            try:
                response = await fetcher.fetch(url, {"page": page})
                response.raise_for_status()
                for fields, missing, reasons in parse_quotes(response.json()):
                    self._write(output, str(response.url), fields, missing, reasons)
                self.store.mark(key, "ok", _now())
                self.pages_fetched += 1
                log.info("page %s selesai records_written=%s", page, self.records_written)
                if not response.json()["has_next"]:
                    break
            except Exception as error:
                self._fail(key, url, error)
                raise

    async def _seo(self, limit: int | None, output: Any) -> None:
        fetcher = self._fetcher()
        urls = self.recon["sitemap"]["urls"][:limit]
        for url in urls:
            key = f"detail:{url}"
            if self.resume and self.store.done(key):
                continue
            try:
                response = await fetcher.fetch(url)
                response.raise_for_status()
                self._write(output, url, *parse_seo(response.text, url))
                self.store.mark(key, "ok", _now())
                self.pages_fetched += 1
                log.info("url selesai %s records_written=%s", url, self.records_written)
            except Exception as error:
                self._fail(key, url, error)
                raise

    async def _detail_target(self, limit: int | None, output: Any) -> None:
        fetcher = self._fetcher()
        pagination = self.recon["pagination"]
        maximum = pagination["max_page_observed"] + (1 if self.target == "driftlab" else 0)
        for page in range(1, min(maximum, limit or maximum) + 1):
            page_key = f"page:{page}"
            if self.resume and self.store.done(page_key):
                continue
            page_url = pagination["url_template"].format(n=page)
            try:
                response = await fetcher.fetch(page_url)
                if response.status_code == 404 and self.target == "driftlab":
                    fetcher.status_counts["404"] -= 1
                    if fetcher.status_counts["404"] == 0:
                        del fetcher.status_counts["404"]
                    break
                response.raise_for_status()
                for url in detail_links(self.target, response.text, page_url):
                    await self._detail(url, output)
                self.store.mark(page_key, "ok", _now())
                self.pages_fetched += 1
                log.info("page %s selesai records_written=%s", page, self.records_written)
            except Exception as error:
                self._fail(page_key, page_url, error)
                continue

    async def _detail(self, url: str, output: Any) -> None:
        fetcher = self._fetcher()
        key = f"detail:{url}"
        if self.resume and self.store.done(key):
            return
        try:
            response = await fetcher.fetch(url)
            response.raise_for_status()
            self._write(output, url, *parse_detail(self.target, response.text, url))
            self.store.mark(key, "ok", _now())
        except Exception as error:
            self._fail(key, url, error)
            raise

    def _write(self, output: Any, url: str, fields: dict, missing: list[str], reasons: dict[str, str]) -> None:
        key = fields[CONTRACTS[self.target]["key"]]
        record = {
            "record_id": make_record_id(self.target, key),
            "target": self.target,
            "url": url,
            "run_id": self.run_id,
            "fetched_at": _now(),
            "content_hash": content_hash(fields),
            "fields": fields,
            "missing_fields": missing,
            "missing_reason": reasons,
        }
        try:
            validate_record(record, self.target)
        except SchemaUnknownField:
            known = {field.name for field in CONTRACTS[self.target]["fields"]}
            self.schema_unknown_fields.update(set(fields) - known)
            raise
        if not self.store.add_seen(record["record_id"], record["content_hash"]):
            self.duplicates_rejected += 1
            return
        output.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
        self.records_written += 1
        output.flush()
        if self.records_written % 10 == 0:
            log.info("stream flush records_written=%s", self.records_written)

    def _fail(self, key: str, url: str, error: Exception) -> None:
        self.errors += 1
        self.store.mark(key, "error", _now(), str(error))
        log.error("request gagal url=%s error=%s", url, error)

    def _fetcher(self) -> Fetcher:
        if self.fetcher is None:
            raise RuntimeError("fetcher belum diinisialisasi")
        return self.fetcher

    def manifest(self, exit_code: int) -> dict:
        finished = datetime.now(JAKARTA)
        fields = [field.name for field in CONTRACTS[self.target]["fields"]]
        completeness = _completeness(self.records_path, fields)
        fetcher = self.fetcher
        return {
            "run_id": self.run_id,
            "target": self.target,
            "started_at": self.started.isoformat(timespec="seconds"),
            "finished_at": finished.isoformat(timespec="seconds"),
            "duration_sec": round((finished - self.started).total_seconds(), 3),
            "engine": self.recon["recommended_engine"],
            "exit_code": exit_code,
            "resume_used": self.resume,
            "pages_fetched": self.pages_fetched,
            "records_written": self.records_written,
            "records_unique": self.store.unique_count(),
            "duplicates_rejected": self.duplicates_rejected,
            "errors": self.errors,
            "schema_unknown_fields": sorted(self.schema_unknown_fields),
            "http_status_counts": dict(fetcher.status_counts) if fetcher else {},
            "retries": fetcher.retries if fetcher else 0,
            "field_completeness": completeness,
            "rate_limit": {
                "delay_sec": self.policy_delay,
                "actual_delay_sec": self.delay,
                "concurrency": self.concurrency,
                "observed_min_gap_ms": fetcher.observed_min_gap_ms if fetcher else None,
            },
            "code_version": _code_version(),
        }


@app.command()
def main(
    target: str = typer.Option(..., help="books | quotes | seo | driftlab"),
    limit: int | None = typer.Option(None, min=1, help="Berhenti setelah N unit kerja"),
    resume: bool = typer.Option(False, help="Lewati unit checkpoint berstatus ok"),
    delay: float | None = typer.Option(None, min=0, help="Timpa delay; HANYA untuk uji DO-11"),
    policy_delay: float | None = typer.Option(None, min=0, help="Jeda minimum kebijakan untuk audit"),
    concurrency: int = typer.Option(1, min=1, help="Maksimum request serentak"),
    date: str | None = typer.Option(None, help="Timpa folder tanggal: YYYY-MM-DD"),
    out: Path | None = typer.Option(None, help="Folder hasil run"),
) -> None:
    if target not in CONTRACTS:
        raise typer.BadParameter("target harus books, quotes, seo, atau driftlab")
    run_date = date or datetime.now(JAKARTA).date().isoformat()
    try:
        datetime.strptime(run_date, "%Y-%m-%d")
    except ValueError as error:
        raise typer.BadParameter("date harus YYYY-MM-DD") from error
    recon = json.loads((Path(__file__).parents[1] / "recon" / f"{target}.json").read_text())
    local = urlparse(recon["base_url"]).hostname in {"127.0.0.1", "localhost"}
    default_delay = recon["robots"]["crawl_delay"] or (0.0 if local else 1.0)
    effective_delay = delay if delay is not None else default_delay
    effective_policy_delay = policy_delay if policy_delay is not None else default_delay
    if not local:
        effective_delay = max(1.0, effective_delay)
        effective_policy_delay = max(1.0, effective_policy_delay)
        concurrency = min(concurrency, PUBLIC_MAX_CONCURRENCY)
    directory = out or Path("data") / target / run_date
    if directory.exists() and any(directory.iterdir()) and not resume:
        typer.confirm(
            f"Folder {directory} sudah berisi data. Jalankan lagi untuk menguji dedupe?",
            abort=True,
        )
    directory.mkdir(parents=True, exist_ok=True)
    _configure_logging(directory / "run.log")
    run = Run(target, recon, directory, resume, effective_delay, effective_policy_delay, concurrency)
    exit_code = 0
    try:
        asyncio.run(run.execute(limit))
        if run.store.unique_count() == 0:
            exit_code = 1
    except (Exception, KeyboardInterrupt):
        exit_code = 1
        log.exception("run gagal target=%s", target)
    finally:
        (directory / "run.json").write_text(
            json.dumps(run.manifest(exit_code), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        run.store.close()
    if exit_code:
        raise typer.Exit(exit_code)


def _configure_logging(path: Path) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(path, encoding="utf-8"), logging.StreamHandler()],
        force=True,
    )


def _now() -> str:
    return datetime.now(JAKARTA).isoformat(timespec="seconds")


def _completeness(path: Path, field_names: list[str]) -> dict[str, float]:
    counts = Counter()
    total = 0
    if path.exists():
        with path.open(encoding="utf-8") as source:
            for line in source:
                if not line.strip():
                    continue
                fields = json.loads(line)["fields"]
                total += 1
                counts.update(name for name in field_names if fields.get(name) not in (None, "", []))
    return {name: counts[name] / total if total else 0.0 for name in field_names}


def _code_version() -> str:
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return f"git:{sha}"
    except (OSError, subprocess.CalledProcessError):
        return "git:unknown"


if __name__ == "__main__":
    app()
