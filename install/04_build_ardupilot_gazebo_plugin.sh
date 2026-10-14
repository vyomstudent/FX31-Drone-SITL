#!/usr/bin/env bash
set -Eeuo pipefail
command -v gz >/dev/null || { echo 'ERROR: gz CLI unavailable; install Harmonic first.' >&2; exit 2; }
PLUGIN_DIR="${ARDUPILOT_GAZEBO_DIR:-$HOME/ardupilot_gazebo}"
sudo apt-get update
sudo apt-get install -y git cmake g++ pkg-config libgz-sim8-dev rapidjson-dev libopencv-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-bad gstreamer1.0-libav gstreamer1.0-gl
if [[ -d "$PLUGIN_DIR/.git" ]]; then
  if [[ -n "$(git -C "$PLUGIN_DIR" status --porcelain)" ]]; then
    echo "ERROR: $PLUGIN_DIR has local changes; commit/stash them or choose another ARDUPILOT_GAZEBO_DIR." >&2; exit 3
  fi
  git -C "$PLUGIN_DIR" pull --ff-only
elif [[ -e "$PLUGIN_DIR" ]]; then echo "ERROR: $PLUGIN_DIR exists but is not a Git clone." >&2; exit 3
else git clone https://github.com/ArduPilot/ardupilot_gazebo.git "$PLUGIN_DIR"; fi
export GZ_VERSION=harmonic
cmake -S "$PLUGIN_DIR" -B "$PLUGIN_DIR/build" -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build "$PLUGIN_DIR/build" --parallel "${BUILD_JOBS:-2}"
printf '\nPASS: official plugin built at %s\n' "$PLUGIN_DIR"
printf 'export GZ_SIM_SYSTEM_PLUGIN_PATH=%q/build:${GZ_SIM_SYSTEM_PLUGIN_PATH:-}\n' "$PLUGIN_DIR"
printf 'export GZ_SIM_RESOURCE_PATH=%q/models:%q/worlds:${GZ_SIM_RESOURCE_PATH:-}\n' "$PLUGIN_DIR" "$PLUGIN_DIR"
