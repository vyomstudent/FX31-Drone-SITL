#!/usr/bin/env bash
set -Eeuo pipefail
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$KIT_DIR"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -c 'from pymavlink import mavutil; print("PASS: pymavlink import OK; MAVLink 2:", mavutil.mavlink20())'
