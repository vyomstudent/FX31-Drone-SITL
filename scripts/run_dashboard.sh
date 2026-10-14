#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[[ -f .venv/bin/activate ]] || { echo 'Run Codespaces bootstrap first.' >&2; exit 1; }
. .venv/bin/activate
echo 'Open the private Codespaces forwarded port 8000 in the PORTS tab.'
exec python dashboard/server.py --host 0.0.0.0 --port 8000
