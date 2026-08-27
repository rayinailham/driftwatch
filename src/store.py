"""SQLite checkpoint and deduplication storage."""

import sqlite3
from pathlib import Path


class Store:
    def __init__(self, path: Path):
        self.connection = sqlite3.connect(path)
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS progress (
                key TEXT PRIMARY KEY,
                status TEXT,
                fetched_at TEXT,
                error TEXT
            );
            CREATE TABLE IF NOT EXISTS seen (
                record_id TEXT PRIMARY KEY,
                content_hash TEXT
            );
            """
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def done(self, key: str) -> bool:
        row = self.connection.execute(
            "SELECT status FROM progress WHERE key = ?", (key,)
        ).fetchone()
        return row is not None and row[0] == "ok"

    def mark(self, key: str, status: str, fetched_at: str, error: str | None = None) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO progress(key, status, fetched_at, error) VALUES (?, ?, ?, ?)",
            (key, status, fetched_at, error),
        )
        self.connection.commit()

    def add_seen(self, record_id: str, content_hash: str) -> bool:
        self.connection.execute(
            "INSERT OR IGNORE INTO seen(record_id, content_hash) VALUES (?, ?)",
            (record_id, content_hash),
        )
        inserted = self.connection.execute("SELECT changes()").fetchone()[0] == 1
        self.connection.commit()
        return inserted

    def unique_count(self) -> int:
        return self.connection.execute("SELECT COUNT(*) FROM seen").fetchone()[0]
