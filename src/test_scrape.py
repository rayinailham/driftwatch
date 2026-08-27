"""Focused checks for scraper retry and SQLite deduplication."""

import asyncio
import tempfile
import unittest
from pathlib import Path

import httpx

from scrape import Fetcher
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


if __name__ == "__main__":
    unittest.main()
