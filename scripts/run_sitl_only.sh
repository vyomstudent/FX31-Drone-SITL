#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SIM="${ARDUPILOT_DIR:-$HOME/ardupilot}/Tools/autotest/sim_vehicle.py"
[[ -f "$SIM" ]] || { echo "ERROR: $SIM not found; run installer first." >&2; exit 2; }
mkdir -p "$ROOT/outputs"
[[ -f "$ROOT/.venv/bin/activate" ]] && source "$ROOT/.venv/bin/activate" || true
export PATH="$HOME/.local/bin:$PATH"
args=(-v ArduCopter -f quad --out=127.0.0.1:14560 --out=127.0.0.1:14561)
if [[ "${FX31_GUI:-0}" == '1' && -n "${DISPLAY:-}" ]]; then args+=(--console --map); fi
if [[ "${RESET_EEPROM:-0}" == '1' ]]; then echo 'WARNING: wiping SITL saved parameters (-w).'; args+=(-w); fi
echo 'Starting Copter SITL. Telemetry on localhost UDP 14560 (tests) and 14561 (dashboard).'
exec python "$SIM" "${args[@]}" "$@"
