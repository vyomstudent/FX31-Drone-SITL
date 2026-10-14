#!/usr/bin/env bash
set -Eeuo pipefail
ARDUPILOT_DIR="${ARDUPILOT_DIR:-$HOME/ardupilot}"
PLUGIN_DIR="${ARDUPILOT_GAZEBO_DIR:-$HOME/ardupilot_gazebo}"
SIM="$ARDUPILOT_DIR/Tools/autotest/sim_vehicle.py"
[[ -f "$SIM" ]] || { echo "ERROR: $SIM not found." >&2; exit 2; }
[[ -d "$PLUGIN_DIR/build" ]] || { echo "ERROR: plugin build missing at $PLUGIN_DIR/build." >&2; exit 3; }
export GZ_SIM_SYSTEM_PLUGIN_PATH="$PLUGIN_DIR/build:${GZ_SIM_SYSTEM_PLUGIN_PATH:-}"
export GZ_SIM_RESOURCE_PATH="$PLUGIN_DIR/models:$PLUGIN_DIR/worlds:${GZ_SIM_RESOURCE_PATH:-}"
export PATH="$HOME/.local/bin:$PATH"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$ROOT/.venv/bin/activate" ]]; then source "$ROOT/.venv/bin/activate"; fi
args=(-v ArduCopter -f gazebo-iris --model JSON --out=127.0.0.1:14560 --out=127.0.0.1:14561)
if [[ "${FX31_GUI:-0}" == '1' && -n "${DISPLAY:-}" ]]; then args+=(--console --map); fi
echo 'Starting Gazebo-linked Iris (not a calibrated FX31 drone). Ensure Gazebo world server is already running.'
exec python "$SIM" "${args[@]}" "$@"
