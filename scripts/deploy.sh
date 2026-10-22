#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE_DIR="${TMPDIR:-/tmp}/intel-rdtech-release"
SSH_HOST="${INTEL_RDTECH_SSH_HOST:-rdtech-intel}"
REMOTE_ROOT="${INTEL_RDTECH_REMOTE_ROOT:-~/intel.rdtechadvisory.com}"

cd "$PROJECT_ROOT"

rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

cp web/index.html "$RELEASE_DIR/index.html"
cp data/feeds/feed.json "$RELEASE_DIR/feed.json"

sed -i "s#const DATA='../data/feeds/feed.json'#const DATA='./feed.json'#" \
    "$RELEASE_DIR/index.html"

echo "Deploying Intel-RDTech to ${SSH_HOST}:${REMOTE_ROOT}"
rsync -av --delete "$RELEASE_DIR/" "${SSH_HOST}:${REMOTE_ROOT}/"

echo "Deployment complete."
