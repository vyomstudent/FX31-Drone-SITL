#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
. .venv/bin/activate
python scripts/check_sitl.py
python scripts/param_audit.py
python scripts/test_release_safety_gate.py --trials 250 --seed 42 --min-separation-m 5.0
