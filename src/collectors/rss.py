from datetime import datetime, timezone
from time import mktime
from typing import Any

import feedparser
import requests


HEADERS = {
    "User-Agent": (
        "RDTech-Intelligence/0.1 "
        "(R&D technology intelligence aggregator)"
    )
}


def _parse_date(entry: Any) -> str | None:
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
                "published": _parse_date(entry),
                "url": url,
                "summary": entry.get("summary", "").strip(),
                "topics": source.get("topics", []),
                "company": None,
                "score": None,
            }
        )

    status["records"] = len(records)
    status["ok"] = len(records) > 0

    return records, status
