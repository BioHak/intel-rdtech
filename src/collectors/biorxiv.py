from datetime import date, timedelta
from time import sleep

import requests


BASE_URL = "https://api.biorxiv.org/details/biorxiv"

HEADERS = {
    "User-Agent": (
        "RDTech-Intelligence/0.1 "
        "(contact: genaro@rdtechadvisory.com)"
    )
}


def fetch_recent_biorxiv(
    days: int = 7,
    request_delay: float = 0.15,
) -> list[dict]:
    """
    Retrieve all bioRxiv records within a recent date window.

    bioRxiv endpoint:
        /details/biorxiv/YYYY-MM-DD/YYYY-MM-DD/cursor/json

    Pagination metadata returned by the API includes:
        cursor
        count
        total
        count_new_papers
    """

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    start = start_date.isoformat()
    end = end_date.isoformat()

    records = []
    cursor = 0
    total = None

    while True:

        url = (
            f"{BASE_URL}/"
            f"{start}/{end}/{cursor}/json"
        )

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        messages = data.get("messages", [])
        collection = data.get("collection", [])

        if not messages:
            raise RuntimeError(
                "bioRxiv API returned no status metadata"
            )

        message = messages[0]

        status = message.get("status")

        if status != "ok":
            raise RuntimeError(
                f"bioRxiv API error: {status}"
            )

        if total is None:
            total = int(message.get("total", 0))

            print(
                f"    interval: {start} to {end}"
            )
            print(
                f"    total records/versions: {total}"
            )
            print(
                "    new papers: "
                f"{message.get('count_new_papers', 'unknown')}"
            )

        if not collection:
            break

        records.extend(collection)

        count = len(collection)

        print(
            f"    cursor={cursor:<5} "
            f"received={count:<3} "
            f"collected={len(records)}/{total}"
        )

        cursor += count

        if cursor >= total:
            break

        # Be polite to the public API.
        sleep(request_delay)

    return records


def normalize_biorxiv(item: dict) -> dict:
    """Normalize bioRxiv metadata into Intel-RDTech schema."""

    doi = item.get("doi")
    published_doi = item.get("published") or None

    return {
        # Core record
        "title": item.get("title", "").strip(),
        "source": "bioRxiv",
        "source_id": "biorxiv",

        # Acquisition method
        "source_type": "api",

        # Content semantics
        "content_type": "publication",
        "evidence_stage": "preprint",

        "published": (
            f"{item['date']}T00:00:00+00:00"
            if item.get("date")
            else None
        ),

        "url": (
            f"https://www.biorxiv.org/content/{doi}"
            if doi
            else None
        ),

        "summary": item.get("abstract", "").strip(),

        # Intelligence metadata
        "topics": [],
        "company": None,
        "score": None,

        # Publication identity
        "doi": doi,
        "preprint_doi": doi,
        "published_doi": published_doi,

        # bioRxiv metadata
        "version": item.get("version"),
        "category": item.get("category"),
        "authors": item.get("authors"),

        "corresponding_author":
            item.get("author_corresponding"),

        "corresponding_institution":
            item.get(
                "author_corresponding_institution"
            ),
    }
