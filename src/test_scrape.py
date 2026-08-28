"""Focused checks for scraper retry and SQLite deduplication."""

import asyncio
import io
import json
import tempfile
import unittest
from pathlib import Path

import httpx

from scrape import Fetcher, Run
from engines.http_html import parse_detail
from store import Store


class FetcherTests(unittest.TestCase):
    def test_404_and_403_are_not_retried(self) -> None:
        for status in (403, 404):
            with self.subTest(status=status):
                calls = 0

                def respond(request: httpx.Request) -> httpx.Response:
                    nonlocal calls
                    calls += 1
                    return httpx.Response(status, request=request)

                async def exercise() -> httpx.Response:
                    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
                        return await Fetcher(client, delay=0, concurrency=1).fetch("https://example.test/finding")

                self.assertEqual(asyncio.run(exercise()).status_code, status)
                self.assertEqual(calls, 1)

    def test_503_stops_after_four_attempts(self) -> None:
        calls = 0

        def respond(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            return httpx.Response(503, request=request)

        async def exercise() -> None:
            async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
                await Fetcher(client, delay=0, concurrency=1).fetch("https://example.test/busy")

        with self.assertRaisesRegex(Exception, "HTTP 503"):
            asyncio.run(exercise())
        self.assertEqual(calls, 4)


class StoreTests(unittest.TestCase):
    def test_seen_primary_key_rejects_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory) / "progress.db")
            try:
                self.assertTrue(store.add_seen("books:upc:1", "sha256:first"))
                self.assertFalse(store.add_seen("books:upc:1", "sha256:second"))
                self.assertEqual(store.unique_count(), 1)
            finally:
                store.close()


class PartialHarvestTests(unittest.TestCase):
    def test_listing_failure_keeps_partial_output_and_sets_nonzero_exit(self) -> None:
        listing = '<article class="item-card"><h2><a href="/item/1.html">One</a></h2></article>'
        detail = (
            '<article class="item-detail" data-item-id="DW-001">'
            '<h1 class="item-name">One</h1><span class="price">1.0</span>'
            '<span class="category">fixture</span></article>'
        )

        class FakeFetcher:
            status_counts = {"200": 2, "500": 1}
            retries = 0
            observed_min_gap_ms = None

            async def fetch(self, url: str, params: dict | None = None) -> httpx.Response:
                request = httpx.Request("GET", url)
                if url.endswith("page-1.html"):
                    return httpx.Response(200, text=listing, request=request)
                if url.endswith("1.html"):
                    return httpx.Response(200, text=detail, request=request)
                return httpx.Response(500, request=request)

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            recon = {
                "pagination": {
                    "max_page_observed": 1,
                    "url_template": "http://127.0.0.1:8100/page-{n}.html",
                },
                "recommended_engine": "httpx+selectolax",
            }
            run = Run("driftlab", recon, directory, False, 0.0, 0.0, 1)
            run.fetcher = FakeFetcher()  # type: ignore[assignment]
            output = io.StringIO()
            try:
                asyncio.run(run._detail_target(None, output))
                manifest_data = run.manifest(run.exit_code())
                rows = [json.loads(line) for line in output.getvalue().splitlines()]

                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["record_id"], "driftlab:item_id:DW-001")
                self.assertEqual(run.errors, 1)
                self.assertEqual(manifest_data["exit_code"], 1)
                self.assertEqual(manifest_data["http_status_counts"], {"200": 2, "500": 1})
                self.assertTrue(run.store.done("page:1"))
                self.assertFalse(run.store.done("page:2"))
            finally:
                run.store.close()

    def test_driftlab_404_pagination_terminator_is_not_failure(self) -> None:
        class FakeFetcher:
            status_counts = {"404": 1}
            retries = 0
            observed_min_gap_ms = None

            async def fetch(self, url: str, params: dict | None = None) -> httpx.Response:
                return httpx.Response(404, request=httpx.Request("GET", url))

        with tempfile.TemporaryDirectory() as temporary:
            recon = {
                "pagination": {
                    "max_page_observed": 1,
                    "url_template": "http://127.0.0.1:8100/page-{n}.html",
                },
                "recommended_engine": "httpx+selectolax",
            }
            run = Run("driftlab", recon, Path(temporary), False, 0.0, 0.0, 1)
            fetcher = FakeFetcher()
            run.fetcher = fetcher  # type: ignore[assignment]
            try:
                asyncio.run(run._detail_target(None, io.StringIO()))
                self.assertEqual(run.errors, 0)
                self.assertEqual(fetcher.status_counts, {})
            finally:
                run.store.close()

    def test_progress_marked_ok_is_done(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory) / "progress.db")
            try:
                store.mark("page:1", "ok", "2026-08-27T09:00:00+07:00")
                self.assertTrue(store.done("page:1"))
            finally:
                store.close()


class ParserTests(unittest.TestCase):
    HTML = """
    <ul class="breadcrumb"><li></li><li></li><li><a>Poetry</a></li></ul>
    <div class="product_main"><h1>A Light in the Attic</h1><p class="star-rating Three"></p></div>
    <table class="table-striped">
      <tr><th>UPC</th><td>a897fe39b1053632</td></tr>
      <tr><th>Price (incl. tax)</th><td>£51.77</td></tr>
      <tr><th>Price (excl. tax)</th><td>£51.77</td></tr>
      <tr><th>Tax</th><td>£0.00</td></tr>
      <tr><th>Availability</th><td>In stock (22 available)</td></tr>
      <tr><th>Number of reviews</th><td>0</td></tr>
    </table>
    """

    def test_book_parser_produces_required_fields(self) -> None:
        fields, missing, reasons = parse_detail("books", self.HTML, "https://example.test/book")
        self.assertEqual(fields["upc"], "a897fe39b1053632")
        self.assertEqual(fields["title"], "A Light in the Attic")
        self.assertEqual(fields["price_incl_tax_gbp"], 51.77)
        self.assertEqual(fields["availability_count"], 22)
        self.assertEqual(fields["rating"], "Three")
        self.assertEqual(missing, ["description_words"])
        self.assertEqual(reasons, {"description_words": "elemen #product_description tidak ada"})

    def test_missing_required_field_has_reason(self) -> None:
        fields, missing, reasons = parse_detail("books", self.HTML.replace("<h1>A Light in the Attic</h1>", ""), "")
        self.assertIsNone(fields["title"])
        self.assertIn("title", missing)
        self.assertEqual(reasons["title"], "field title tidak ditemukan di sumber")


if __name__ == "__main__":
    unittest.main()
