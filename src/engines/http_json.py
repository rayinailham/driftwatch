"""JSON API parser for the quotes target."""

import hashlib


def parse_quotes(payload: dict) -> list[tuple[dict, list[str], dict[str, str]]]:
    parsed = []
    for quote in payload["quotes"]:
        text = quote["text"]
        author = quote["author"]
        fields = {
            "quote_id": hashlib.sha256(text.encode()).hexdigest()[:16],
            "author_name": author["name"],
            "author_slug": author["slug"],
            "author_goodreads_link": author["goodreads_link"],
            "quote_word_count": len(text.split()),
            "tags": quote.get("tags") or [],
        }
        missing = ["tags"] if not fields["tags"] else []
        reason = {"tags": "array tags kosong pada respons API"} if missing else {}
        parsed.append((fields, missing, reason))
    return parsed
