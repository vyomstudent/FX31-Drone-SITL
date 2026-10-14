# FX31 Drone SITL Test Kit v1.0.0

A staged test kit for ArduPilot Copter SITL, companion-computer MAVLink scripts, an offline person-separation release-gate exercise, simulated release-servo command acceptance, fault injection, then Gazebo Harmonic building-scene integration. Baseline: **Ubuntu 22.04 under WSL2**. The SITL installer defaults to the stable `Copter-4.7.1` tag for repeatability; match the exact Copter version intended for your Pixhawk firmware before treating parameters or behavior as comparable.

> **Safety boundary:** Control scripts default to `udpin:127.0.0.1:14560`, and flight/servo/fault actions require explicit flags. Do not change the endpoint to a physical serial port or a real aircraft. The short guided test is capped at 5 m and is only for SITL. A simulated servo ACK does not prove physical wiring or mechanism safety.

## Included files

- `install/01_install_ardupilot_sitl.sh`: clone/build ArduPilot Copter SITL.
- `install/02_install_python_tools.sh`: create a local Python venv and install pymavlink.
- `install/03_install_gazebo_harmonic.sh`: install Gazebo Harmonic.
- `install/04_build_ardupilot_gazebo_plugin.sh`: build the official ArduPilot Gazebo plugin.
- `scripts/run_sitl_only.sh`: the lightest first run (MAVProxy map/console, UDP telemetry on localhost port 14560).
- `scripts/check_sitl.py`: heartbeat/GPS/position/battery telemetry smoke test, logs CSV + JSON.
- `scripts/param_audit.py`: read-only parameter inventory.
- `scripts/sitl_param.py`: bounded `SIM_` fault injection, dry-run by default.
- `scripts/servo_test.py`: `MAV_CMD_DO_SET_SERVO`, dry-run by default; blocks output channels 1–8.
- `scripts/guided_flight_test.py`: opt-in GUIDED takeoff, altitude check, RTL.
- `scripts/test_release_safety_gate.py`: offline seeded synthetic trials for a simple minimum-distance-to-person release gate; does not connect to MAVLink or actuate hardware.
- `scripts/self_test.sh`: one-command offline validation of package, release gate, randomized worlds and shell syntax.
- `scripts/randomize_world.py` generates seeded scenario variants; `scripts/run_gazebo_world.sh` and `scripts/run_gazebo_sitl.sh`: custom rescue scene + official Iris Gazebo integration.
- `worlds/fx31_rescue_training_world.sdf`: multi-storey facade, balconies, person stand-ins, glowing fire proxies and Iris-with-gimbal.
- `docs/TEST_PLAN.md`, `docs/GAZEBO_STAGE.md`, and `docs/VALIDATION_REPORT.md`: stepwise test plan, Gazebo/camera caveats, and a transparent offline-validation report.

## Phase 1 — install SITL on Windows/WSL2

### A. Open PowerShell as Administrator

If WSL2 + Ubuntu 22.04 is not already installed:

```powershell
wsl --install -d Ubuntu-22.04
```

Restart if Windows asks. Open Ubuntu 22.04 and create the Linux username. Keep all source/build directories in the Linux filesystem (`~/...`), not `/mnt/c`, to avoid slower builds.

### B. Extract this kit into Linux home

If the ZIP is in Windows Downloads, access it from Ubuntu under `/mnt/c/Users/<WINDOWS_USER>/Downloads/`. Extract to `~/FX31_SITL_Test_Kit_v1.0.0`, then:

```bash
cd ~/FX31_SITL_Test_Kit_v1.0.0
chmod +x install/*.sh scripts/*.sh
./scripts/self_test.sh
./install/01_install_ardupilot_sitl.sh
./install/02_install_python_tools.sh
source .venv/bin/activate
```

The first installer clones ArduPilot to `~/ardupilot`, installs upstream build prerequisites, and builds the SITL Copter target. It may take a while and requires network access. It defaults to `Copter-4.7.1`; for a separate checkout, use `ARDUPILOT_BRANCH='Copter-4.7.1' ARDUPILOT_DIR="$HOME/ardupilot_fx31_test" ./install/01_install_ardupilot_sitl.sh`. Replace the tag with the exact Copter release used on the target Pixhawk when known. If an existing checkout is dirty, the installer refuses to switch it. If your ArduPilot clone is elsewhere, set `ARDUPILOT_DIR=/your/path`.

Validation checkpoint:

```bash
~/ardupilot/Tools/autotest/sim_vehicle.py --help | head -n 20
python -c 'import pymavlink; print("pymavlink import OK")'
```

## Phase 2 — launch the lightest simulator

Terminal 1:

```bash
cd ~/FX31_SITL_Test_Kit_v1.0.0
./scripts/run_sitl_only.sh
```

Keep this terminal open. Wait for SITL and MAVProxy to finish startup. The script adds `--out=127.0.0.1:14560`, which the local test scripts listen to.

Terminal 2:

```bash
cd ~/FX31_SITL_Test_Kit_v1.0.0
source .venv/bin/activate
python scripts/check_sitl.py
python scripts/param_audit.py
```

Do **not** proceed to automated flight until the smoke test reports `PASS`. `CHECK` means GPS or required telemetry did not fully validate; `FAIL` means connectivity/telemetry failed. Logs are saved under `outputs/`.

## Phase 3 — offline release-zone logic (no flight controller)

Before servo/flight commands, exercise the example distance gate against repeatable synthetic scenes:

```bash
python scripts/test_release_safety_gate.py --trials 250 --seed 42 --min-separation-m 5.0
```

The `5.0 m` value is only an illustrative test input, **not a recommended operational safety radius**. Set it from the payload, altitude, descent/dispersion, localization error and hazard analysis. The script creates a CSV in `outputs/`, tests inside/on/outside-threshold boundaries, and never contacts SITL. It tests only a simple distance gate using synthetic ground-truth positions—not your fire/person detector, visual localization, descent trajectory, or full drop policy.

## Phase 4 — isolated SITL tests

### Simulated release-servo output

Dry-run first:

```bash
python scripts/servo_test.py --channel 9 --pwm 1100
```

Only after confirming that the chosen number is the intended *auxiliary* output in the active SITL parameters, send the command:

```bash
python scripts/servo_test.py --channel 9 --pwm 1100 --execute --confirm SITL_ONLY
```

Channel 9 is an example, **not** a claim about the FX31 wiring or Pixhawk port mapping. Use `param_audit.py` and inspect the chosen channel’s `SERVOx_FUNCTION`. Confirm the function is compatible with `DO_SET_SERVO` for this firmware (typically function 0, 1, or 51–66); the command may be rejected for other assignments. Never select a motor output. Record ACK and any output shown by the GCS; restore the intended safe simulated position afterwards.

### Fault injection

Preview:

```bash
python scripts/sitl_param.py --parameter SIM_RC_FAIL --value 1
```

Apply in SITL:

```bash
python scripts/sitl_param.py --parameter SIM_RC_FAIL --value 1 --apply --confirm SITL_ONLY
```

Restore after logging observations:

```bash
python scripts/sitl_param.py --parameter SIM_RC_FAIL --value 0 --apply --confirm SITL_ONLY
```

The script allowlists `SIM_RC_FAIL`, `SIM_GPS_DISABLE`, `SIM_BATT_VOLTAGE`, `SIM_WIND_SPD`, `SIM_WIND_DIR`, and `SIM_ACC_RND`; it refuses unknown parameters and non-local endpoints. Always restore the original value recorded before each fault trial.

### Short GUIDED takeoff + RTL

Dry-run:

```bash
python scripts/guided_flight_test.py --altitude-m 3
```

Execute only when ready, with MAVProxy visible:

```bash
python scripts/guided_flight_test.py --altitude-m 3 --execute --confirm SITL_ONLY
```

It verifies a GPS 3D fix, enters GUIDED, requests arm, checks the armed bit, requests takeoff, confirms climb, then switches to RTL. It does not bypass pre-arm checks. If arming is denied, review SITL messages rather than disabling checks.

## Phase 5 — Gazebo Harmonic building scene

Only after Phase 2 passes:

```bash
./install/03_install_gazebo_harmonic.sh
./install/04_build_ardupilot_gazebo_plugin.sh
```

Terminal 1:

```bash
./scripts/run_gazebo_world.sh
```

Terminal 2:

```bash
./scripts/run_gazebo_sitl.sh
```

For a server-only start, use `HEADLESS=1 ./scripts/run_gazebo_world.sh`; camera rendering may need an offscreen/render configuration. You can select a randomized world with `WORLD_FILE=outputs/scenarios/fx31_scenario_seed_00042.sdf ./scripts/run_gazebo_world.sh`. Generate repeatable target-placement variants with `python scripts/randomize_world.py --seed 42 --count 25`; this creates 25 checked SDF files under `outputs/scenarios/` but does not launch flights or evaluate release policy. Launch one by setting `WORLD_FILE=outputs/scenarios/fx31_scenario_seed_00042.sdf`. This uses the plugin's official Iris example, not an FX31 airframe model. The world contains **static target proxies**, not dynamic walking people, realistic fire/smoke physics, thermal truth, or a validated FX31 aerodynamic model. See `docs/GAZEBO_STAGE.md` before camera work.

## Important limitations

- SITL runs ArduPilot flight code but does not electrically emulate Pixhawk 6X wiring, the 4-in-1 ESC, real battery sag, ELRS, Pi UART, modem interference/brownouts, servo mechanics or payload safety.
- The official Iris airframe is for integration proving only; it does not validate FX31 mass/inertia/thrust values.
- Orange emissive objects are RGB-visible fire stand-ins. They are **not thermal sources**. Gazebo Sim lists thermal-camera capability, but temperature assignment, sensor setup, renderer output and detector-compatible stream still need a separate tested implementation.
- The supplied scripts intentionally do not listen on the LAN. A later Raspberry Pi test should use a private lab network and an explicitly reviewed MAVLink forward path after local testing.
- Passing SITL means “no obvious logic/integration failure under these assumptions,” not “safe to fly.” Use a propeller-off bench setup, validated power/BEC design, independent kill/disarm and a reviewed test card before hardware tests.

## Official references

- ArduPilot SITL: https://ardupilot.org/dev/docs/using-sitl-for-ardupilot-testing.html
- Linux SITL setup: https://ardupilot.org/dev/docs/setting-up-sitl-on-linux.html
- ArduPilot + Gazebo: https://ardupilot.org/dev/docs/sitl-with-gazebo.html
- Official plugin: https://github.com/ArduPilot/ardupilot_gazebo
- Gazebo Harmonic installation: https://gazebosim.org/docs/harmonic/install_ubuntu/
- Gazebo Sim sensors: https://gazebosim.org/docs/harmonic/sensors/
