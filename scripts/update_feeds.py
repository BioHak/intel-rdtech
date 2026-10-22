#!/usr/bin/env python

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.collectors.rss import collect_rss
from src.collectors.biorxiv import (
    fetch_recent_biorxiv,
    normalize_biorxiv,
)
from src.processing.classify import classify_record


SOURCES_FILE = PROJECT_ROOT / "config" / "sources.yml"
TOPICS_FILE = PROJECT_ROOT / "config" / "topics.yml"
OUTPUT_FILE = PROJECT_ROOT / "data" / "feeds" / "feed.json"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def load_sources() -> list[dict]:
    """Load configured intelligence sources."""

    with SOURCES_FILE.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    return config.get("sources", [])


def load_topics() -> list[dict]:
    """Load configured intelligence topics."""

    with TOPICS_FILE.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    return config.get("topics", [])


# ---------------------------------------------------------------------------
# RSS collection
# ---------------------------------------------------------------------------

def collect_rss_sources(
    sources: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Collect all enabled RSS sources."""

    records = []
    source_status = []

    for source in sources:

        if not source.get("enabled", True):
            print(f"Skipping: {source['name']} (disabled)")
            continue

        print(f"Collecting: {source['name']}")

        if source.get("type") != "rss":
            print(
                f"  Unsupported source type: "
                f"{source.get('type')}"
            )
            continue

        source_records, status = collect_rss(source)

        records.extend(source_records)
        source_status.append(status)

        state = "OK" if status["ok"] else "FAILED"

        print(
            f"  {state}: {status['records']} records "
            f"(HTTP {status.get('http_status')})"
        )

        if status.get("warning"):
            print(f"  Warning: {status['warning']}")

    return records, source_status


# ---------------------------------------------------------------------------
# bioRxiv collection
# ---------------------------------------------------------------------------

def collect_biorxiv(
    topics: list[dict],
    days: int = 7,
) -> tuple[list[dict], dict]:
    """
    Retrieve recent bioRxiv preprints and retain records matching
    configured Intel-RDTech topics.
    """

    print("Collecting: bioRxiv")

    try:
        raw_records = fetch_recent_biorxiv(days=days)

        matched_records = []

        for item in raw_records:

            record = normalize_biorxiv(item)

            record["topics"] = classify_record(
                record,
                topics,
            )

            # v0.1 behavior:
            # only retain preprints matching at least one
            # configured intelligence topic.
            if not record["topics"]:
                continue

            matched_records.append(record)

        status = {
            "source_id": "biorxiv",
            "name": "bioRxiv",
            "ok": True,
            "records": len(matched_records),
            "examined": len(raw_records),
            "warning": None,
        }

        print(
            f"  OK: {len(raw_records)} examined, "
            f"{len(matched_records)} matched"
        )

        return matched_records, status

    except Exception as exc:

        status = {
            "source_id": "biorxiv",
            "name": "bioRxiv",
            "ok": False,
            "records": 0,
            "examined": 0,
            "warning": str(exc),
        }

        print(f"  FAILED: {exc}")

        return [], status


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main():

    sources = load_sources()
    topics = load_topics()

    all_records = []
    source_status = []

    # RSS / Atom sources
    rss_records, rss_status = collect_rss_sources(
        sources
    )

    all_records.extend(rss_records)
    source_status.extend(rss_status)

    # Leading-edge scientific literature
    biorxiv_records, biorxiv_status = collect_biorxiv(
        topics,
        days=7,
    )

    all_records.extend(biorxiv_records)
    source_status.append(biorxiv_status)

    # Newest dated records first.
    all_records.sort(
        key=lambda record: record.get("published") or "",
        reverse=True,
    )

    output = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "record_count": len(all_records),
        "source_count": len(source_status),
        "source_status": source_status,
        "records": all_records,
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as handle:

        json.dump(
            output,
            handle,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print(f"Wrote {len(all_records)} records")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
