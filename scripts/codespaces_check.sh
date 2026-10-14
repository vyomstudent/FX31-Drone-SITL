#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 scripts/validate_kit.py >/dev/null
[[ -x "${ARDUPILOT_DIR:-$HOME/ardupilot}/build/sitl/bin/arducopter" ]] || {
  echo 'NOT READY: ArduPilot SITL executable missing; inspect logs/codespaces_setup.log' >&2; exit 1;
}
[[ -f .venv/bin/activate ]] || { echo 'NOT READY: .venv missing' >&2; exit 1; }
. .venv/bin/activate
python -c 'from pymavlink import mavutil; print("PASS: pymavlink available")'
echo 'PASS: FX31 Codespaces dependencies are installed (not a live flight test).'
