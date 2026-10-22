#!/usr/bin/env python

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.collectors.rss import collect_rss


CONFIG_FILE = PROJECT_ROOT / "config" / "sources.yml"
OUTPUT_FILE = PROJECT_ROOT / "data" / "feeds" / "feed.json"


def load_sources() -> list[dict]:

    with CONFIG_FILE.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    return config.get("sources", [])


def main():

    sources = load_sources()

    all_records = []
    source_status = []

    for source in sources:
        
        if not source.get("enabled", True):
            print(f"Skipping: {source['name']} (disabled)")
            continue
        
        print(f"Collecting: {source['name']}")

        if source["type"] == "rss":
            records, status = collect_rss(source)
        else:
            print(f"  Unsupported source type: {source['type']}")
            continue

        source_status.append(status)
        all_records.extend(records)

        state = "OK" if status["ok"] else "FAILED"

        print(
            f"  {state}: {status['records']} records "
            f"(HTTP {status['http_status']})"
        )

        if status["warning"]:
            print(f"  Warning: {status['warning']}")

    all_records.sort(
        key=lambda record: record["published"] or "",
        reverse=True,
    )
    
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "record_count": len(all_records),
        "source_count": len(source_status),
        "source_status": source_status,
        "records": all_records,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as handle:
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
