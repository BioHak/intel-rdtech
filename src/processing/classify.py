def classify_record(record: dict, topics: list[dict]) -> list[str]:
    """Assign intelligence topics using title + summary/abstract."""

    text = " ".join(
        [
            record.get("title", ""),
            record.get("summary", ""),
        ]
    ).lower()

    matches = []

    for topic in topics:

        if not topic.get("enabled", True):
            continue

        include_terms = [
            term.lower()
            for term in topic.get("include_any", [])
        ]

        context_terms = [
            term.lower()
            for term in topic.get("context_any", [])
        ]

        if not any(term in text for term in include_terms):
            continue

        if context_terms:
            if not any(term in text for term in context_terms):
                continue

        matches.append(topic["id"])

    return matches
