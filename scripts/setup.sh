#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
command -v uv >/dev/null || { echo "uv is required: https://docs.astral.sh/uv/" >&2; exit 1; }
uv sync --project "${ROOT_DIR}"

echo "Environment ready."
echo "Run from the repository: uv run lynote-ai examples/sample_ai_like.txt --json"
