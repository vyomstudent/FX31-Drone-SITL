#!/usr/bin/env bash
# Automatic one-time setup when Codespaces creates/rebuilds this devcontainer.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$ROOT/logs" "$ROOT/outputs"
exec > >(tee -a "$ROOT/logs/codespaces_setup.log") 2>&1
printf '\nFX31 Codespaces bootstrap: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
cd "$ROOT"
python3 scripts/validate_kit.py
# Build footprint is intentionally limited by skipping optional ArduPilot graphics,
# coverage and ARM cross-compile dependencies. The run remains in cloud CPU-only SITL.
export SKIP_AP_GRAPHIC_ENV=1 SKIP_AP_COV_ENV=1 SKIP_AP_EXT_ENV=1 SKIP_AP_ARM_GCC=1
export ARDUPILOT_BRANCH="${ARDUPILOT_BRANCH:-Copter-4.7.1}"
if [[ ! -x "${ARDUPILOT_DIR:-$HOME/ardupilot}/build/sitl/bin/arducopter" ]]; then
    bash install/01_install_ardupilot_sitl.sh
else
    echo 'Existing SITL binary found: skipping ArduPilot compilation.'
fi
if [[ ! -f .venv/bin/activate ]]; then
    bash install/02_install_python_tools.sh
else
    . .venv/bin/activate
    python -c 'from pymavlink import mavutil; print("pymavlink ready")'
fi
bash scripts/codespaces_check.sh
python3 -m unittest discover -s tests -v
printf '\nSETUP COMPLETE. Start sim: ./scripts/run_codespaces_sitl.sh\n'
