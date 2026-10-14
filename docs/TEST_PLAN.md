# FX31 staged SITL test plan

This is a recordable engineering test card, not a certified safety case. Keep Pixhawk, ESC, LiPo, propellers and the payload-release mechanism disconnected during these tests.

## Stage 0 — baseline

Run `./scripts/self_test.sh` before installing the simulator. This validates package syntax, the offline release gate and randomized SDF generation; it is not a SITL/Gazebo runtime pass.

- [ ] Record date/time, OS, ArduPilot version/commit and Gazebo version when used.
- [ ] Confirm automation uses only `udpin:127.0.0.1:14560` and no hardware serial endpoint is connected.
- [ ] Start `scripts/run_sitl_only.sh`; keep MAVProxy visible.

## Stage 1 — telemetry

```bash
source .venv/bin/activate
python scripts/check_sitl.py
python scripts/param_audit.py
```

Pass means heartbeat, GPS 3D fix, global position and `SYS_STATUS` are present. Save JSON/CSV from `outputs/`. Do not run automated flight while the result is `CHECK` or `FAIL`.

## Stage 2 — review actual failsafe parameters

Use the live parameter descriptions for the running ArduPilot version; do not blindly paste enums from a different release. Record `FS_THR_ENABLE`, `FS_THR_VALUE`, `FS_OPTIONS`, `FS_GCS_ENABLE`, `FS_GCS_TIMEOUT` if present, `BATT_FS_LOW_ACT`, `BATT_FS_CRT_ACT`, `FENCE_ENABLE`, `FENCE_TYPE`, `FENCE_ACTION`, fence geometry/altitude, `SERVOx_FUNCTION` and output limits. The included audit is read-only.

## Stage 3 — offline person-separation release gate

```bash
python scripts/test_release_safety_gate.py --trials 250 --seed 42 --min-separation-m 5.0
```

Choose the separation parameter from a reviewed hazard analysis; `5.0 m` is only an illustrative value. PASS means the example gate obeys its synthetic distance invariant and boundary tests. It does not validate perception, localization, flight dynamics, wind drift, payload trajectory, or the actual release policy. Save the CSV and record the value/assumptions.

## Stage 4 — simulated servo command

```bash
python scripts/servo_test.py --channel 9 --pwm 1100
python scripts/servo_test.py --channel 9 --pwm 1100 --execute --confirm SITL_ONLY
```

Use the second command only after verifying that channel 9 is a valid auxiliary output in the **current SITL parameter set**. Channel 9 is an example. Record the ACK and visible output state where available. Never command a motor channel. Return the output to its desired safe simulated state.

## Stage 5 — short controlled flight

```bash
python scripts/guided_flight_test.py --altitude-m 3
python scripts/guided_flight_test.py --altitude-m 3 --execute --confirm SITL_ONLY
```

Expected: GUIDED mode, accepted arm, takeoff climb, RTL mode. Independently observe landing/disarm. If pre-arm checks fail, diagnose the error instead of disabling checks to force a pass.

## Stage 6 — one injected fault at a time

### RC loss

```bash
python scripts/sitl_param.py --parameter SIM_RC_FAIL --value 1
python scripts/sitl_param.py --parameter SIM_RC_FAIL --value 1 --apply --confirm SITL_ONLY
```

Record the configured RC failsafe action and latency. Restore the pre-test value from the parameter audit after the test (normally 0):

```bash
python scripts/sitl_param.py --parameter SIM_RC_FAIL --value 0 --apply --confirm SITL_ONLY
```

Optionally test `SIM_RC_FAIL=2` as a separate trial. Do not assume the configured response is RTL: inspect the live `FS_THR_ENABLE` meaning for this firmware.

### GPS loss

```bash
python scripts/sitl_param.py --parameter SIM_GPS_DISABLE --value 1 --apply --confirm SITL_ONLY
python scripts/sitl_param.py --parameter SIM_GPS_DISABLE --value 0 --apply --confirm SITL_ONLY
```

Observe GPS/EKF status and mode response; restore the pre-test `SIM_GPS_DISABLE` value promptly (normally 0).

### Wind / accelerometer noise

```bash
python scripts/sitl_param.py --parameter SIM_WIND_DIR --value 180 --apply --confirm SITL_ONLY
python scripts/sitl_param.py --parameter SIM_WIND_SPD --value 3 --apply --confirm SITL_ONLY
python scripts/sitl_param.py --parameter SIM_WIND_SPD --value 0 --apply --confirm SITL_ONLY
python scripts/sitl_param.py --parameter SIM_ACC_RND --value 1 --apply --confirm SITL_ONLY
python scripts/sitl_param.py --parameter SIM_ACC_RND --value 0 --apply --confirm SITL_ONLY
```

Do not combine fault conditions during the first trials. Before testing, record all allowlisted fault parameters; restore each to its recorded pre-test value, including `SIM_WIND_DIR` and `SIM_ACC_RND`, rather than assuming every baseline was zero.

### Simulated battery-voltage failsafe

Inspect `BATT_LOW_VOLT`, `BATT_CRT_VOLT`, `BATT_FS_LOW_ACT`, `BATT_FS_CRT_ACT`, and `SIM_BATT_VOLTAGE` in the live audit first. Use a value appropriate to the simulated battery and below the threshold you intentionally want to test; step down gradually and change only one condition at a time. This changes the simulated voltage input and is a failsafe-path test, not a realistic discharge/cell-sag test.

```bash
# Example only: choose a target after reviewing the values for this SITL build.
python scripts/sitl_param.py --parameter SIM_BATT_VOLTAGE --value 10.8
python scripts/sitl_param.py --parameter SIM_BATT_VOLTAGE --value 10.8 --apply --confirm SITL_ONLY
# After the trial, restore the exact numeric baseline recorded in the audit.
# Do not paste a made-up default; use the recorded number in --value.
```

Record the actual failsafe action and restore the original voltage after the trial. Do not copy the sample voltage blindly to a different simulated battery or firmware.

### GCS link and geofence

RC-loss injection is not a GCS/companion-link failure. Before testing GCS loss, verify the release-specific GCS failsafe and isolate the exact MAVLink link to interrupt; do not remove your only control/observation path during first trials. Battery tests need a known simulated battery model plus reviewed low/critical thresholds/actions. Geofence tests need a known fence geometry/action. Treat these as separate test cards after base tests pass.

## Stage 7 — exit criteria for Gazebo

- [ ] Smoke test PASS and evidence saved.
- [ ] Read-only parameter audit saved.
- [ ] Servo command acceptance documented in SITL.
- [ ] Short GUIDED/RTL trial is observed through landing.
- [ ] RC-loss response and reset documented.
- [ ] GPS-loss response and restoration documented.
- [ ] No physical-hardware claims inferred from simulation.

| Record | Value |
|---|---|
| Test ID/date | |
| Firmware/version/hash | |
| SITL type: built-in / Gazebo | |
| Parameter file | |
| Starting mode/GPS/battery | |
| Command/fault | |
| Expected response | |
| Actual response + time | |
| Evidence filenames | |
| Pass/fail/notes | |
