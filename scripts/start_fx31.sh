#!/usr/bin/env bash
# Runs both SITL and read-only HTTP monitor. Ctrl+C ends both.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p logs outputs
if [[ ! -f .venv/bin/activate ]]; then
    echo 'Dependencies not ready; run: bash scripts/codespaces_bootstrap.sh' >&2
    exit 2
fi
. .venv/bin/activate
python dashboard/server.py --host 0.0.0.0 --port 8000 >logs/dashboard.log 2>&1 &
dashboard_pid=$!
cleanup(){
    kill "$dashboard_pid" 2>/dev/null || true
    wait "$dashboard_pid" 2>/dev/null || true
}
trap cleanup EXIT
sleep 1
if ! kill -0 "$dashboard_pid" 2>/dev/null; then
    cat logs/dashboard.log >&2
    echo 'Could not start dashboard on port 8000.' >&2
    exit 3
fi
echo 'FX31 browser monitor: PORTS tab > 8000 (private)' 
echo 'SITL output: local UDP ports 14560 (tests) and 14561 (dashboard)'
echo 'In another terminal: bash scripts/run_smoke_test.sh'
echo 'Press Ctrl+C to stop. No real hardware should be connected.'
bash scripts/run_codespaces_sitl.sh 2>&1 | tee logs/sitl.log
