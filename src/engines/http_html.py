"""HTML parsers for server-rendered targets."""

import re
from urllib.parse import urljoin

from selectolax.parser import HTMLParser


def detail_links(target: str, html: str, page_url: str) -> list[str]:
    tree = HTMLParser(html)
    selector = "article.product_pod h3 a" if target == "books" else "article.item-card h2 a"
    return [urljoin(page_url, node.attributes["href"]) for node in tree.css(selector)]


def parse_detail(target: str, html: str, url: str) -> tuple[dict, list[str], dict[str, str]]:
    tree = HTMLParser(html)
    if target == "books":
        rows = {
            row.css_first("th").text(strip=True): row.css_first("td").text(strip=True)
            for row in tree.css("table.table-striped tr")
        }
        description = tree.css_first("#product_description ~ p")
        rating = tree.css_first("div.product_main p.star-rating")
        fields = {
            "upc": rows.get("UPC"),
            "title": _text(tree, "div.product_main h1"),
            "price_incl_tax_gbp": _money(rows.get("Price (incl. tax)")),
            "price_excl_tax_gbp": _money(rows.get("Price (excl. tax)")),
            "tax_gbp": _money(rows.get("Tax")),
            "availability_count": _integer(rows.get("Availability")),
            "in_stock": "In stock" in rows.get("Availability", ""),
            "rating": rating.attributes.get("class", "").split()[-1] if rating else None,
            "category": _text(tree, "ul.breadcrumb li:nth-of-type(3) a"),
            "num_reviews": _integer(rows.get("Number of reviews")),
            "description_words": len(description.text().split()) if description else None,
        }
        return _with_missing(fields, {"description_words": "elemen #product_description tidak ada"})

    item = tree.css_first("article.item-detail")
    fields = {
        "item_id": _attribute(tree, "article.item-detail", "data-item-id"),
        "name": _text(tree, "h1.item-name"),
        "price": _float(_text(tree, "span.price")),
        "category": _text(tree, "span.category"),
        "note": _text(tree, "p.note"),
    }
    if item:
        for name, value in item.attributes.items():
            if name.startswith("data-") and name != "data-item-id":
                fields[name.removeprefix("data-").replace("-", "_")] = value
    return _with_missing(fields, {"note": "elemen p.note tidak ada di halaman detail"})


def parse_seo(html: str, url: str) -> tuple[dict, list[str], dict[str, str]]:
    tree = HTMLParser(html)
    article = tree.css_first("article")
    fields = {
        "url": url,
        "title": _text(tree, "head > title"),
        "h1": _text(tree, "article h1"),
        "meta_description": _attribute(tree, 'meta[name="description"]', "content"),
        "canonical": _attribute(tree, 'link[rel="canonical"]', "href"),
        "h2_count": len(tree.css("article h2")),
        "word_count": len(article.text().split()) if article else None,
        "link_count": len(tree.css("article a[href]")),
        "og_title": _attribute(tree, 'meta[property="og:title"]', "content"),
    }
    return _with_missing(fields, {"og_title": 'tag <meta property="og:title"> tidak ada'})


def _text(tree: HTMLParser, selector: str) -> str | None:
    node = tree.css_first(selector)
    return node.text(strip=True)[:2000] if node else None


def _attribute(tree: HTMLParser, selector: str, name: str) -> str | None:
    node = tree.css_first(selector)
    value = node.attributes.get(name) if node else None
    return value[:2000] if value else None


def _money(value: str | None) -> float | None:
    return _float(value.lstrip("£") if value else None)


def _float(value: str | None) -> float | None:
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


def _integer(value: str | None) -> int | None:
    match = re.search(r"\d+", value or "")
    return int(match.group()) if match else None


def _with_missing(
    fields: dict, optional_reasons: dict[str, str]
) -> tuple[dict, list[str], dict[str, str]]:
    missing = [name for name, value in fields.items() if value is None or value == "" or value == []]
    reasons = {
        name: optional_reasons.get(name, f"field {name} tidak ditemukan di sumber")
        for name in missing
    }
    return fields, missing, reasons
