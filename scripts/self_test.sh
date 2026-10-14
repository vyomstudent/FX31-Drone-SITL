#!/usr/bin/env bash
set -Eeuo pipefail
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d -t fx31-sitl-selftest.XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT
cd "$KIT_DIR"
echo '=== 1/4 Package/static validation ==='
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_kit.py
echo
echo '=== 2/4 Offline release-zone gate properties ==='
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_release_safety_gate.py --trials 250 --seed 42 --min-separation-m 5.0 --output "$TMP_DIR/release_gate_trials.csv"
echo
echo '=== 3/4 Deterministic world randomization ==='
PYTHONDONTWRITEBYTECODE=1 python3 scripts/randomize_world.py --seed 42 --count 3 --output-dir "$TMP_DIR/worlds"
echo
echo '=== 4/4 Shell syntax ==='
while IFS= read -r -d '' f; do bash -n "$f"; echo "PASS: $f"; done < <(find install scripts -maxdepth 1 -type f -name '*.sh' -print0)
echo
echo 'ALL OFFLINE KIT TESTS PASSED. No SITL flight or Gazebo runtime was launched.'
