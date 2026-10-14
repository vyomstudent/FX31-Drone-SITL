#!/usr/bin/env bash
set -Eeuo pipefail
if ! grep -qi ubuntu /etc/os-release; then echo 'ERROR: Ubuntu is required for this installer.' >&2; exit 2; fi
. /etc/os-release
if [[ "${VERSION_ID:-}" != "22.04" && "${VERSION_ID:-}" != "24.04" ]]; then echo "WARNING: Ubuntu 22.04 or 24.04 preferred; detected ${VERSION_ID:-unknown}."; fi
ARDUPILOT_DIR="${ARDUPILOT_DIR:-$HOME/ardupilot}"
# Use a named stable release by default for repeatability. Override this to match
# the exact Copter release/tag intended for the target Pixhawk firmware.
ARDUPILOT_BRANCH="${ARDUPILOT_BRANCH:-Copter-4.7.1}"
sudo apt-get update
sudo apt-get install -y git git-lfs python3 python3-pip python3-venv python3-dev build-essential
if [[ -d "$ARDUPILOT_DIR/.git" ]]; then
  echo "Using existing ArduPilot repo at $ARDUPILOT_DIR"
  if [[ -n "$(git -C "$ARDUPILOT_DIR" status --porcelain)" ]]; then
    echo "ERROR: $ARDUPILOT_DIR has uncommitted/untracked changes. Commit/stash them or choose another ARDUPILOT_DIR; refusing to change the working tree." >&2
    exit 3
  fi
  git -C "$ARDUPILOT_DIR" fetch --tags origin
  git -C "$ARDUPILOT_DIR" checkout "$ARDUPILOT_BRANCH"
  git -C "$ARDUPILOT_DIR" submodule sync --recursive
  git -C "$ARDUPILOT_DIR" submodule update --init --recursive
elif [[ -e "$ARDUPILOT_DIR" ]]; then
  echo "ERROR: $ARDUPILOT_DIR exists but is not a Git repo; move it or set ARDUPILOT_DIR." >&2; exit 3
else
  git clone --depth 1 --branch "$ARDUPILOT_BRANCH" --recurse-submodules --shallow-submodules https://github.com/ArduPilot/ardupilot.git "$ARDUPILOT_DIR"
fi
cd "$ARDUPILOT_DIR"
Tools/environment_install/install-prereqs-ubuntu.sh -y
if [[ -f "$HOME/.profile" ]]; then source "$HOME/.profile"; fi
./waf configure --board sitl
./waf copter -j "${BUILD_JOBS:-2}"
printf '\nPASS: ArduPilot SITL Copter build completed in %s\n' "$ARDUPILOT_DIR"
printf 'Firmware reference: %s\n' "$(git describe --tags --always --dirty)"
