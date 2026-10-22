#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_ROOT="${INTEL_RDTECH_WEB_ROOT:-$HOME/intel.rdtechadvisory.com}"
PYTHON="${INTEL_RDTECH_PYTHON:-$HOME/virtualenv/intel-rdtech/bin/python}"

cd "$PROJECT_ROOT"

# Keep the host runner aligned with main before collecting.
git pull --ff-only origin main

# Build the new feed first. If collection fails, set -e prevents a partial
# deployment and leaves the previously published console intact.
"$PYTHON" scripts/update_feeds.py

mkdir -p "$WEB_ROOT"
cp web/index.html "$WEB_ROOT/index.html.tmp"
cp data/feeds/feed.json "$WEB_ROOT/feed.json.tmp"

sed -i "s#const DATA='../data/feeds/feed.json'#const DATA='./feed.json'#" \
    "$WEB_ROOT/index.html.tmp"

# Publish atomically enough for a two-file static release: each completed file
# replaces the prior version only after its copy/transformation succeeds.
mv "$WEB_ROOT/feed.json.tmp" "$WEB_ROOT/feed.json"
mv "$WEB_ROOT/index.html.tmp" "$WEB_ROOT/index.html"

echo "$(date -Is) Intel-RDTech refresh complete"
