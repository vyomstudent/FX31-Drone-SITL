#!/usr/bin/env bash
# Gazebo is deliberately OPT-IN. There is no GPU in ordinary GitHub Codespaces.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ "${FX31_GAZEBO_OPT_IN:-}" == 'YES' ]] || {
  echo 'Gazebo may exhaust free CPU/storage quota. Run FX31_GAZEBO_OPT_IN=YES bash scripts/install_gazebo_optional.sh only after SITL succeeds.' >&2
  exit 2
}
cd "$ROOT"
bash install/03_install_gazebo_harmonic.sh
bash install/04_build_ardupilot_gazebo_plugin.sh
echo 'Try: HEADLESS=1 bash scripts/run_gazebo_world.sh in one terminal, then bash scripts/run_gazebo_sitl.sh in another.'
