#!/usr/bin/env python3
"""World Intel RSS ingest.
Reads the feed list from .claude/scripts/feeds.txt (one "Name | URL" per line),
downloads every feed, and prints: source | date | title | description | link
Usage:  python3 .claude/scripts/rss_ingest.py --days 1
"""
import argparse, calendar, html, re, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser

FEEDS = Path(__file__).parent / "feeds.txt"


def clean(text, limit=300):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    return text[:limit]


def load_feeds(path):
    feeds = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        name, url = (part.strip() for part in line.split("|", 1))
        if url.startswith("http"):
            feeds[url] = name
    return feeds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=1)
    ap.add_argument("--feeds", default=str(FEEDS))
    args = ap.parse_args()

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    feeds = load_feeds(args.feeds)
    if not feeds:
        sys.exit("ERROR | no feeds found in feeds.txt")

    seen, rows = set(), []
    for url, source in feeds.items():
        parsed = feedparser.parse(url)
        if not parsed.entries:
            print(f"WARN | {source} | feed returned 0 entries", file=sys.stderr)
        for entry in parsed.entries:
            stamp = entry.get("published_parsed") or entry.get("updated_parsed")
            link = entry.get("link", "")
            if not stamp or link in seen:
                continue
            when = datetime.fromtimestamp(calendar.timegm(stamp), timezone.utc)
            if when < cutoff:
                continue
            seen.add(link)
            is_hn = "ycombinator" in url or "hnrss" in url
            desc = "" if is_hn else clean(entry.get("summary", ""))
            title = clean(entry.get("title", ""), 200)
            rows.append((when, f"{source} | {when:%Y-%m-%d} | {title} | {desc} | {link}"))

    for _, line in sorted(rows, reverse=True):
        print(line)
    print(f"TOTAL | {len(rows)} items from {len(feeds)} feeds, last {args.days} day(s)")


if __name__ == "__main__":
    main()
