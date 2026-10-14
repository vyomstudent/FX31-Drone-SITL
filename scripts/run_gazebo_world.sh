#!/usr/bin/env bash
set -Eeuo pipefail
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_DIR="${ARDUPILOT_GAZEBO_DIR:-$HOME/ardupilot_gazebo}"
command -v gz >/dev/null || { echo 'ERROR: Gazebo CLI unavailable.' >&2; exit 2; }
[[ -d "$PLUGIN_DIR/models/iris_with_gimbal" ]] || { echo "ERROR: $PLUGIN_DIR/models/iris_with_gimbal not found; build the official plugin first." >&2; exit 3; }
export GZ_SIM_SYSTEM_PLUGIN_PATH="$PLUGIN_DIR/build:${GZ_SIM_SYSTEM_PLUGIN_PATH:-}"
export GZ_SIM_RESOURCE_PATH="$PLUGIN_DIR/models:$PLUGIN_DIR/worlds:${GZ_SIM_RESOURCE_PATH:-}"
WORLD_FILE="${WORLD_FILE:-$KIT_DIR/worlds/fx31_rescue_training_world.sdf}"
[[ "$WORLD_FILE" = /* ]] || WORLD_FILE="$KIT_DIR/$WORLD_FILE"
[[ -f "$WORLD_FILE" ]] || { echo "ERROR: world file not found: $WORLD_FILE" >&2; exit 4; }
if [[ "${HEADLESS:-0}" == "1" ]]; then
  echo "Starting Gazebo server-only mode. Camera rendering may require a working offscreen/render setup."
  exec gz sim -s -v4 -r "$WORLD_FILE" "$@"
else
  exec gz sim -v4 -r "$WORLD_FILE" "$@"
fi
