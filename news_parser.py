"""Fetch RSS/Atom feeds and export articles to CSV or JSON."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import feedparser
import requests

USER_AGENT = "news-parser/1.0"
DEFAULT_TIMEOUT = 15
DEFAULT_LIMIT = 20


@dataclass
class Article:
    title: str
    link: str
    published: str
    summary: str
    source: str


class _TagStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join("".join(self._parts).split())


def strip_html(text: str) -> str:
    if not text:
        return ""
    parser = _TagStripper()
    parser.feed(text)
    return parser.get_text()


def to_iso(entry: dict) -> str:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        return datetime(*parsed[:6], tzinfo=timezone.utc).isoformat()
    return entry.get("published", entry.get("updated", ""))


def fetch(url: str, timeout: int = DEFAULT_TIMEOUT) -> bytes:
    response = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.content


def parse(content: bytes, source: str, limit: int = DEFAULT_LIMIT) -> list[Article]:
    feed = feedparser.parse(content)
    articles: list[Article] = []
    seen: set[str] = set()
    for entry in feed.entries[:limit]:
        link = entry.get("link", "")
        if not link or link in seen:
            continue
        seen.add(link)
        articles.append(
            Article(
                title=strip_html(entry.get("title", "")),
                link=link,
                published=to_iso(entry),
                summary=strip_html(entry.get("summary", "")),
                source=source,
            )
        )
    return articles


def filter_keyword(articles: list[Article], keyword: str) -> list[Article]:
    needle = keyword.lower()
    return [
        a for a in articles
        if needle in a.title.lower() or needle in a.summary.lower()
    ]


def export_csv(articles: list[Article], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(articles[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(a) for a in articles)


def export_json(articles: list[Article], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump([asdict(a) for a in articles], handle, ensure_ascii=False, indent=2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse RSS/Atom feeds into CSV or JSON.")
    parser.add_argument("-f", "--feed", action="append", required=True, help="Feed URL (repeatable)")
    parser.add_argument("-n", "--limit", type=int, default=DEFAULT_LIMIT, help="Max articles per feed")
    parser.add_argument("-k", "--keyword", help="Only keep articles containing this keyword")
    parser.add_argument("-F", "--format", choices=("csv", "json"), default="csv")
    parser.add_argument("-o", "--out", help="Output file path")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    return parser


def default_out(fmt: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("output") / f"news_{stamp}.{fmt}"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    articles: list[Article] = []
    for url in args.feed:
        try:
            articles.extend(parse(fetch(url, args.timeout), url, args.limit))
            print(f"[ok] {url}", file=sys.stderr)
        except Exception as exc:
            print(f"[skip] {url}: {exc}", file=sys.stderr)

    if args.keyword:
        articles = filter_keyword(articles, args.keyword)

    if not articles:
        print("No articles collected.", file=sys.stderr)
        return 1

    out = Path(args.out) if args.out else default_out(args.format)
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.format == "csv":
        export_csv(articles, out)
    else:
        export_json(articles, out)

    print(f"Saved {len(articles)} articles -> {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
