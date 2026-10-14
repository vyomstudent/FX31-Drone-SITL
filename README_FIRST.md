# FX31 — GitHub Codespaces ArduPilot SITL environment

**Start here.** This is a dedicated **free-tier, CPU-first Codespaces project** for the FX31 firefighting/rescue drone. It runs real ArduCopter SITL firmware and testing tools, plus a lightweight browser telemetry/map console. It builds on the prior FX31 SITL v1.0.0 kit, preserving its fault-injection, dry-run servo, GUIDED/RTL, randomized Gazebo SDF, and release-zone test tools.

**This is not a complete Gazebo rendering service:** ordinary GitHub Codespaces has no dedicated GPU. Gazebo Harmonic/ArduPilot's plugin is an optional, unverified heavy stage; the browser dashboard is a simple illustrative map, not Gazebo video or detector imagery. The Iris simulation is **not calibrated to FX31 hardware**. No hardware firmware has been developed yet.

## Simplest route: let ChatGPT install the project into GitHub

1. In GitHub, create a **separate personal repository** named `FX31-Drone-SITL`: https://github.com/new. Check **Add README**, then create the repository. You may choose private; repository must belong to your personal account for your personal Codespaces free quota.
2. Send ChatGPT its URL. GitHub connector can commit these source files to the repository once it has access. **Do not put these files in the VSPIMU IMU-v5 repository.**
3. After files are committed, open `Code` → `Codespaces` → `Create codespace on main`; explicitly select **2-core**. The `.devcontainer/devcontainer.json` automatically executes `scripts/codespaces_bootstrap.sh`. Keep the terminal open for setup and read `logs/codespaces_setup.log` if it fails. GitHub may defer `postCreateCommand` output into a setup terminal.
4. Once setup finishes, run `bash scripts/start_fx31.sh`. From the **PORTS** tab, open private port **8000**. A second terminal can run `bash scripts/run_smoke_test.sh`.
5. Stop the simulation with `Ctrl+C`. **Stop your Codespace from GitHub's Codespaces page when not in use** to avoid consuming free compute time.

## Alternative manual upload (without GitHub connector)

If you downloaded the packaged ZIP instead, create the same personal GitHub repo (check **Add README**) and start a 2-core Codespace from it. Use VS Code Explorer to **drag the ZIP into the repository root** of your running Codespace. Then execute (replace filename if necessary):

```bash
unzip -qo FX31_Codespaces_Starter_v1.0.0.zip
cp -a FX31_Codespaces_Starter_v1.0.0/. .
rm -rf FX31_Codespaces_Starter_v1.0.0 FX31_Codespaces_Starter_v1.0.0.zip
bash scripts/codespaces_bootstrap.sh
```

This manual setup works in the default Codespace. To persist your source changes, **commit and push them**: `git add . && git commit -m "Add FX31 Codespaces SITL workspace" && git push`. A later Codespace rebuild will detect the `.devcontainer` settings and may rerun the idempotent bootstrap. Keep `.venv/`, `logs/`, output files and ArduPilot build artifacts outside Git, as configured in `.gitignore`.

## Launch and verify

The built-in setup installs a pinned **ArduCopter `Copter-4.7.1`** source tag to `$HOME/ardupilot`, compiles for the Linux SITL board, and creates `.venv` with Pymavlink and MAVProxy. You can override `ARDUPILOT_BRANCH` later to match the Pixhawk flight firmware. No ROS or Pixhawk physical controller is required.

In **terminal 1** (from repository root):

```bash
bash scripts/codespaces_check.sh
bash scripts/start_fx31.sh
```

Keep terminal 1 running and open the private `8000` port from the **PORTS** tab. After SITL is running, in **terminal 2**:

```bash
bash scripts/run_smoke_test.sh
```

A passing smoke test means the real SITL autopilot responds with heartbeats, GPS, position and battery telemetry; its JSON/CSV results are written under `outputs/`. The dashboard listens to independent `udpin:127.0.0.1:14561`, while the smoke/fault/servo tools use `udpin:127.0.0.1:14560`. Never point those test tools at real hardware.

## Other tests (SITL only; explicit execution required)

Dry-run commands, safe to inspect with no flight:

```bash
source .venv/bin/activate
python scripts/guided_flight_test.py --altitude-m 3
python scripts/servo_test.py --channel 9 --pwm 1100
python scripts/sitl_param.py --parameter SIM_RC_FAIL --value 1
```

Once `run_smoke_test.sh` is PASS and all output/parameter mapping is verified, the isolated **SITL-only** tests can be run with `--execute --confirm SITL_ONLY` (or `--apply --confirm SITL_ONLY` for simulated faults). No real airframe may be connected. Commands must be verified against Copter version and selected servo function. See `docs/TEST_PLAN.md` for procedure and cleanup.

## Optional Gazebo (not required for this milestone)

```bash
FX31_GAZEBO_OPT_IN=YES bash scripts/install_gazebo_optional.sh
```

This installs Gazebo Harmonic and builds `ardupilot_gazebo`, which can consume substantial disk and CPU on a 2-core machine. When installed, `HEADLESS=1 bash scripts/run_gazebo_world.sh` and `bash scripts/run_gazebo_sitl.sh` should be run in separate terminals (do **not** simultaneously run the lightweight physics SITL). Software rendering and sensor/camera support are **not validated** for free Codespaces. Full fire effects, real human animation and thermal physics are not implemented. The generated world SDF uses proxy objects and the official Iris example, not the complete FX31 drone model. See `docs/GAZEBO_STAGE.md`.

## Usage budget and privacy

GitHub Free personal accounts have 120 core-hours/month (60h at 2 cores) plus 15 GB-month storage quota. These are **allowances, not a guarantee of no charges** if you have enabled payment/overage. Use 2-core, disable paid overages or set a zero-spend budget, stop idle Codespaces, do not enable prebuilds, and do not run the optional Gazebo installer without reviewing storage. Codespaces port **8000 must remain private**. Never publish or forward MAVLink UDP to the internet. Repo source is small but the ArduPilot clone and binaries occupy persistent Codespaces storage, which can accumulate after you stop compute.

**References**: [GitHub Codespaces free quota](https://docs.github.com/en/billing/concepts/product-billing/github-codespaces), [ArduPilot SITL setup](https://ardupilot.org/dev/docs/setting-up-sitl-on-linux.html), [official Gazebo integration](https://ardupilot.org/dev/docs/sitl-with-gazebo.html), [Gazebo Harmonic installation](https://gazebosim.org/docs/harmonic/install_ubuntu/).

## Troubleshooting

- `SITL binary missing` → check `logs/codespaces_setup.log` and run `bash scripts/codespaces_bootstrap.sh`.
- `No heartbeat` → verify terminal 1 actually launched MAVProxy with `--out=127.0.0.1:14560`; wait for SITL startup; do not start two SITL processes.
- `GPS 3D fix missing` → allow simulated GPS to initialize; keep arming/failsafes intact, do not bypass pre-arm checks.
- `8000 doesn't open` → read `logs/dashboard.log`, inspect **PORTS**, confirm private 8000 forwarded and `bash scripts/start_fx31.sh` remains active.
- `pip missing package` → `source .venv/bin/activate && pip install -r requirements.txt`, then rerun smoke test.
- `Out of storage` → don't install Gazebo; delete unused Codespaces or ArduPilot build files **after saving source changes**.
- `bash ... permission denied` → all scripts can be launched via `bash scripts/file.sh` without executable bits.

## What is verified

`python3 scripts/validate_kit.py`, `bash scripts/self_test.sh`, and `python3 -m unittest discover -s tests -v` exercise static safety constraints, seeded scenario generation and offline dashboard tests. **ArduPilot build, actual MAVLink flight, Codespaces post-create install, Gazebo physics and streamed camera output have not been executed by the authoring environment.** Runtime PASS must be observed in your Codespace before firmware development.
