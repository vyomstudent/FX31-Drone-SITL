#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
SIM="${ARDUPILOT_DIR:-$HOME/ardupilot}/Tools/autotest/sim_vehicle.py"
[[ -f "$SIM" ]] || { echo 'SITL not installed; run bash scripts/codespaces_bootstrap.sh' >&2; exit 2; }
[[ -f .venv/bin/activate ]] || { echo '.venv missing; rerun bootstrap' >&2; exit 2; }
. .venv/bin/activate
export PATH="$HOME/.local/bin:$PATH"
# Two independent localhost streams prevent the dashboard from stealing packets
# from the smoke and control test tools. No real controller is addressed.
# MAVProxy runs as a terminal process; no X server, map or console flags.
args=(-v ArduCopter -f quad --out=127.0.0.1:14560 --out=127.0.0.1:14561)
if [[ "${RESET_EEPROM:-0}" == "1" ]]; then
    echo 'Requested SITL EEPROM wipe (-w)'; args+=(-w)
fi
echo 'Launching simulated quadcopter (terminal-only MAVProxy). Local test stream 14560; dashboard stream 14561.'
exec python "$SIM" "${args[@]}" "$@"
