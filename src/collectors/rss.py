from datetime import datetime, timezone
from time import mktime
from typing import Any, Optional
import re

import feedparser
import requests


HEADERS = {
    "User-Agent": (
        "RDTech-Intelligence/0.1 "
        "(R&D technology intelligence aggregator)"
    )
}


def _parse_date(entry: Any) -> Optional[str]:
    """Return publication date as an ISO-8601 UTC timestamp."""

    for field in ("published_parsed", "updated_parsed"):
        value = entry.get(field)

        if value:
            try:
                dt = datetime.fromtimestamp(
                    mktime(value),
                    tz=timezone.utc,
                )
                return dt.isoformat()
            except (TypeError, ValueError, OverflowError):
                pass

    return None


def _clean_summary(entry: Any, source: dict) -> str:
    """Return the useful article summary without feed-specific metadata."""

    summary = entry.get("summary", "").strip()

    # Nature journal RSS feeds prepend a <p> block containing journal name,
    # publication date, and DOI. Those fields are already represented by the
    # normalized record, so keep only the article description that follows.
    if source.get("id", "").startswith("nature_"):
        summary = re.sub(
            r"^\s*<p>.*?</p>\s*",
            "",
            summary,
            count=1,
            flags=re.IGNORECASE | re.DOTALL,
        )

    return summary.strip()


def collect_rss(source: dict) -> tuple[list[dict], dict]:
    """Fetch, parse, and normalize an RSS/Atom source."""

    status = {
        "source_id": source["id"],
        "name": source["name"],
        "url": source["url"],
        "ok": False,
        "http_status": None,
        "records": 0,
        "warning": None,
    }

    try:
        response = requests.get(
            source["url"],
            headers=HEADERS,
            timeout=20,
        )

        status["http_status"] = response.status_code
        response.raise_for_status()

    except requests.RequestException as exc:
        status["warning"] = str(exc)
        return [], status

    feed = feedparser.parse(response.content)

    if feed.bozo:
        status["warning"] = str(feed.bozo_exception)

    records = []

    for entry in feed.entries:

        title = entry.get("title", "").strip()
        url = entry.get("link")

        # Don't create unusable records.
        if not title or not url:
            continue

        records.append(
            {
                "title": title,
                "source": source["name"],
                "source_id": source["id"],
                "source_type": "rss",
                "content_type": source.get("content_type", "news"),
                "evidence_stage": source.get("evidence_stage"),
                "published": _parse_date(entry),
                "url": url,
                "summary": _clean_summary(entry, source),
                "topics": source.get("topics", []),
                "company": None,
                "score": None,
            }
        )

    status["records"] = len(records)
    status["ok"] = len(records) > 0

    return records, status
